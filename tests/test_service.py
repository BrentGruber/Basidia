import pytest
import json
import asyncio
from io import StringIO
import sys
from unittest.mock import AsyncMock, patch
from basidia.service import Service
from basidia.decorators import rpc
from basidia.brokers.memory import MemoryBroker


class GreetingService(Service):
    name = "greeting_service"
    
    @rpc
    async def greet(self, name):
        return f"Hello, {name}!"


class TestServiceInitialization:
    
    def test_service_initialization_with_custom_name(self):
        """Test service uses custom name when provided"""
        with patch('sys.stdout', new=StringIO()):
            service = GreetingService()
        assert service.name == "greeting_service"

    def test_service_initialization_with_default_name(self):
        """Test service uses class name as default"""
        class MyTestService(Service):
            pass
        
        with patch('sys.stdout', new=StringIO()):
            service = MyTestService()
        assert service.name == "MyTestService"

    def test_service_initialization_with_broker(self):
        """Test service initialization with broker"""
        broker = MemoryBroker()
        with patch('sys.stdout', new=StringIO()):
            service = Service(broker=broker)
        assert service.broker is broker

    def test_startup_banner_printed(self):
        """Test that startup banner is printed on initialization"""
        captured_output = StringIO()
        with patch('sys.stdout', captured_output):
            Service()
        
        output = captured_output.getvalue()
        assert "BASIDIA SERVICE" in output
        assert "Service" in output
        assert "Service ready" in output

    def test_rpc_methods_discovery(self):
        """Test that @rpc decorated methods are discovered"""
        class TestService(Service):
            @rpc
            def method_one(self):
                return "one"
            
            @rpc
            async def method_two(self):
                return "two"
            
            def regular_method(self):
                return "regular"
        
        with patch('sys.stdout', new=StringIO()):
            service = TestService()
        
        assert len(service._rpc_methods) == 2
        assert "method_one" in service._rpc_methods
        assert "method_two" in service._rpc_methods
        assert "regular_method" not in service._rpc_methods

    def test_pending_requests_initialized(self):
        """Test that pending requests dict is initialized"""
        with patch('sys.stdout', new=StringIO()):
            service = Service()
        assert hasattr(service, '_pending_requests')
        assert isinstance(service._pending_requests, dict)
        assert len(service._pending_requests) == 0


class TestServiceStart:
    
    @pytest.mark.asyncio
    async def test_start_without_broker_raises_error(self):
        """Test that start() raises error without broker"""
        with patch('sys.stdout', new=StringIO()):
            service = Service()
        
        with pytest.raises(ValueError, match="Service needs a broker to start"):
            await service.start()

    @pytest.mark.asyncio
    async def test_start_with_broker_connects_and_consumes(self):
        """Test that start() connects to broker and sets up consumer"""
        broker = AsyncMock()
        with patch('sys.stdout', new=StringIO()):
            service = Service(broker=broker)
        
        await service.start()
        
        # Verify broker methods were called
        broker.connect.assert_called_once()
        broker.declare_queue.assert_called_once_with("rpc.Service")
        broker.consume.assert_called_once()
        
        # Check consume was called with correct queue and handler
        consume_call = broker.consume.call_args
        assert consume_call[0][0] == "rpc.Service"
        assert consume_call[0][1] == service._handle_rpc_request

    @pytest.mark.asyncio
    async def test_start_with_custom_service_name(self):
        """Test that start() uses custom service name for queue"""
        broker = AsyncMock()
        
        class CustomService(Service):
            name = "MyCustomService"
        
        with patch('sys.stdout', new=StringIO()):
            service = CustomService(broker=broker)
        
        await service.start()
        
        broker.declare_queue.assert_called_once_with("rpc.MyCustomService")


class TestRPCRequestHandling:
    
    @pytest.mark.asyncio
    async def test_handle_rpc_request_success(self):
        """Test successful RPC request handling"""
        class TestService(Service):
            @rpc
            async def add_numbers(self, a, b):
                return a + b
        
        broker = AsyncMock()
        with patch('sys.stdout', new=StringIO()):
            service = TestService(broker=broker)
        
        # Create test request
        request = {
            "method": "add_numbers",
            "args": [3, 4],
            "kwargs": {},
            "request_id": "test-123",
            "reply_to": "test.reply.queue"
        }
        
        await service._handle_rpc_request(json.dumps(request).encode())
        
        # Verify response was published
        broker.publish.assert_called_once()
        call_args = broker.publish.call_args
        
        assert call_args[0][0] == "test.reply.queue"
        
        response_data = json.loads(call_args[0][1].decode())
        assert response_data["request_id"] == "test-123"
        assert response_data["result"] == 7
        assert response_data["error"] is None

    @pytest.mark.asyncio
    async def test_handle_rpc_request_with_kwargs(self):
        """Test RPC request with keyword arguments"""
        class TestService(Service):
            @rpc
            async def greet(self, name, title="Mr"):
                return f"{title} {name}"
        
        broker = AsyncMock()
        with patch('sys.stdout', new=StringIO()):
            service = TestService(broker=broker)
        
        request = {
            "method": "greet",
            "args": ["Smith"],
            "kwargs": {"title": "Dr"},
            "request_id": "test-456",
            "reply_to": "test.reply"
        }
        
        await service._handle_rpc_request(json.dumps(request).encode())
        
        broker.publish.assert_called_once()
        response_data = json.loads(broker.publish.call_args[0][1].decode())
        assert response_data["result"] == "Dr Smith"

    @pytest.mark.asyncio
    async def test_handle_rpc_request_method_not_found(self):
        """Test RPC request for non-existent method"""
        broker = AsyncMock()
        with patch('sys.stdout', new=StringIO()):
            service = Service(broker=broker)
        
        request = {
            "method": "nonexistent_method",
            "args": [],
            "kwargs": {},
            "request_id": "test-789",
            "reply_to": "test.reply"
        }
        
        await service._handle_rpc_request(json.dumps(request).encode())
        
        broker.publish.assert_called_once()
        response_data = json.loads(broker.publish.call_args[0][1].decode())
        assert response_data["result"] is None
        assert "Method nonexistent_method not found" in response_data["error"]

    @pytest.mark.asyncio
    async def test_handle_rpc_request_method_exception(self):
        """Test RPC request when method raises exception"""
        class TestService(Service):
            @rpc
            async def failing_method(self):
                raise ValueError("Something went wrong")
        
        broker = AsyncMock()
        with patch('sys.stdout', new=StringIO()):
            service = TestService(broker=broker)
        
        request = {
            "method": "failing_method",
            "args": [],
            "kwargs": {},
            "request_id": "test-error",
            "reply_to": "test.reply"
        }
        
        await service._handle_rpc_request(json.dumps(request).encode())
        
        broker.publish.assert_called_once()
        response_data = json.loads(broker.publish.call_args[0][1].decode())
        assert response_data["result"] is None
        assert "Something went wrong" in response_data["error"]


class TestRPCResponseHandling:
    
    def test_handle_rpc_response_success(self):
        """Test successful RPC response handling"""
        with patch('sys.stdout', new=StringIO()):
            service = Service()
        
        # Set up a pending request
        future = asyncio.Future()
        service._pending_requests["test-123"] = future
        
        response = {
            "request_id": "test-123",
            "result": "success",
            "error": None
        }
        
        service._handle_rpc_response(json.dumps(response).encode())
        
        # Future should be resolved with response
        assert future.done()
        assert future.result() == response

    def test_handle_rpc_response_no_pending_request(self):
        """Test response for unknown request ID"""
        with patch('sys.stdout', new=StringIO()):
            service = Service()
        
        response = {
            "request_id": "unknown-123",
            "result": "success",
            "error": None
        }
        
        # Should not raise exception
        service._handle_rpc_response(json.dumps(response).encode())

    @patch('builtins.print')
    def test_handle_rpc_response_malformed_json(self, mock_print):
        """Test handling of malformed JSON response"""
        with patch('sys.stdout', new=StringIO()):
            service = Service()
        
        # Should not raise exception
        service._handle_rpc_response(b"invalid json")
        
        # Should print error (the mock_print will catch the error message)
        mock_print.assert_called()
        error_message = mock_print.call_args[0][0]
        assert "Error handling RPC response" in error_message


class TestCallRPC:
    
    @pytest.mark.asyncio
    async def test_call_rpc_without_broker_raises_error(self):
        """Test that call_rpc raises error without broker"""
        with patch('sys.stdout', new=StringIO()):
            service = Service()
        
        with pytest.raises(ValueError, match="Service needs a broker for rpc calls"):
            await service.call_rpc("target_service", "method_name")

    @pytest.mark.asyncio
    async def test_call_rpc_success(self):
        """Test successful RPC call"""
        broker = AsyncMock()
        with patch('sys.stdout', new=StringIO()):
            service = Service(broker=broker)
        
        # Mock the response handling
        response_future = asyncio.Future()
        response_future.set_result({
            "request_id": "test-id",
            "result": "rpc_result",
            "error": None
        })
        
        with patch('asyncio.Future', return_value=response_future):
            with patch('uuid.uuid4', return_value="test-id"):
                result = await service.call_rpc("target_service", "test_method", "arg1", kwarg="value")
        
        assert result == "rpc_result"
        
        # Verify broker calls
        broker.consume.assert_called_once()
        broker.publish.assert_called_once()
        
        # Check published request
        publish_call = broker.publish.call_args
        target_queue = publish_call[0][0]
        request_data = json.loads(publish_call[0][1].decode())
        
        assert target_queue == "rpc.target_service"
        assert request_data["method"] == "test_method"
        assert request_data["args"] == ["arg1"]
        assert request_data["kwargs"] == {"kwarg": "value"}
        assert request_data["request_id"] == "test-id"

    @pytest.mark.asyncio
    async def test_call_rpc_with_error_response(self):
        """Test RPC call that returns error"""
        broker = AsyncMock()
        with patch('sys.stdout', new=StringIO()):
            service = Service(broker=broker)
        
        response_future = asyncio.Future()
        response_future.set_result({
            "request_id": "test-id",
            "result": None,
            "error": "Remote method failed"
        })
        
        with patch('asyncio.Future', return_value=response_future):
            with patch('uuid.uuid4', return_value="test-id"):
                with pytest.raises(Exception, match="RPC Error: Remote method failed"):
                    await service.call_rpc("target_service", "failing_method")

    @pytest.mark.asyncio
    async def test_call_rpc_cleanup_on_success(self):
        """Test that pending requests are cleaned up on success"""
        broker = AsyncMock()
        with patch('sys.stdout', new=StringIO()):
            service = Service(broker=broker)
        
        response_future = asyncio.Future()
        response_future.set_result({
            "request_id": "test-id",
            "result": "success",
            "error": None
        })
        
        with patch('asyncio.Future', return_value=response_future):
            with patch('uuid.uuid4', return_value="test-id"):
                await service.call_rpc("target_service", "test_method")
        
        # Verify cleanup
        assert "test-id" not in service._pending_requests
