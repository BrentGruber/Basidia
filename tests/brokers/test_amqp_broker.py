import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from basidia.brokers.amqp import AMQPBroker
import aio_pika


class TestAMQPBroker:
    
    @pytest.fixture
    def mock_connection(self):
        """Mock AMQP connection"""
        connection = AsyncMock()
        channel = AsyncMock()
        connection.channel.return_value = channel
        
        # Mock queue
        queue = AsyncMock()
        
        # Mock the iterator context manager properly
        mock_iterator = AsyncMock()
        mock_iterator.__aenter__ = AsyncMock(return_value=mock_iterator)
        mock_iterator.__aexit__ = AsyncMock(return_value=None)
        mock_iterator.__aiter__ = AsyncMock(return_value=iter([]))
        queue.iterator.return_value = mock_iterator
        
        channel.get_queue.return_value = queue
        channel.declare_queue = AsyncMock()
        channel.default_exchange.publish = AsyncMock()
        
        return connection, channel, queue

    @pytest.mark.asyncio
    async def test_connection_lifecycle(self, mock_connection):
        connection, channel, queue = mock_connection
        
        with patch('aio_pika.connect_robust', return_value=connection):
            broker = AMQPBroker()
            
            # Initially not connected
            assert not broker.is_connected
            
            # Connect
            await broker.connect()
            assert broker.is_connected
            
            # Disconnect
            await broker.disconnect()
            assert not broker.is_connected
            
            # Verify cleanup calls
            channel.close.assert_called_once()
            connection.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_connection_failure(self):
        with patch('aio_pika.connect_robust', side_effect=ConnectionError("Connection failed")):
            broker = AMQPBroker()
            
            with pytest.raises(RuntimeError, match="Failed to connect to AMQP Broker"):
                await broker.connect()
            
            assert not broker.is_connected

    @pytest.mark.asyncio
    async def test_context_manager(self, mock_connection):
        connection, channel, queue = mock_connection
        
        with patch('aio_pika.connect_robust', return_value=connection):
            async with AMQPBroker() as broker:
                assert broker.is_connected
            
            # Should be disconnected after context
            assert not broker.is_connected
            channel.close.assert_called_once()
            connection.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_publish_success(self, mock_connection):
        connection, channel, queue = mock_connection
        
        with patch('aio_pika.connect_robust', return_value=connection):
            async with AMQPBroker() as broker:
                await broker.publish("test_queue", b"test message")
                
                # Verify publish was called with correct parameters
                channel.default_exchange.publish.assert_called_once()
                call_args = channel.default_exchange.publish.call_args
                
                # Check the message
                message = call_args[0][0]  # First positional argument
                assert message.body == b"test message"
                
                # Check routing key
                assert call_args[1]['routing_key'] == "test_queue"

    @pytest.mark.asyncio
    async def test_publish_with_custom_delivery_mode(self, mock_connection):
        connection, channel, queue = mock_connection
        
        with patch('aio_pika.connect_robust', return_value=connection):
            async with AMQPBroker() as broker:
                await broker.publish(
                    "test_queue", 
                    b"test message", 
                    delivery_mode=aio_pika.DeliveryMode.NOT_PERSISTENT
                )
                
                # Verify message was created with custom delivery mode
                channel.default_exchange.publish.assert_called_once()
                call_args = channel.default_exchange.publish.call_args
                message = call_args[0][0]
                assert message.delivery_mode == aio_pika.DeliveryMode.NOT_PERSISTENT

    @pytest.mark.asyncio
    async def test_publish_without_connection_fails(self):
        broker = AMQPBroker()
        
        with pytest.raises(RuntimeError, match="Broker not connected"):
            await broker.publish("test_queue", b"message")

    @pytest.mark.asyncio
    async def test_declare_queue(self, mock_connection):
        connection, channel, queue = mock_connection
        
        with patch('aio_pika.connect_robust', return_value=connection):
            async with AMQPBroker() as broker:
                await broker.declare_queue("test_queue")
                
                channel.declare_queue.assert_called_once_with(
                    "test_queue",
                    durable=True,
                    exclusive=False,
                    auto_delete=False
                )

    @pytest.mark.asyncio
    async def test_declare_queue_with_options(self, mock_connection):
        connection, channel, queue = mock_connection
        
        with patch('aio_pika.connect_robust', return_value=connection):
            async with AMQPBroker() as broker:
                await broker.declare_queue(
                    "temp_queue",
                    durable=False,
                    exclusive=True,
                    auto_delete=True
                )
                
                channel.declare_queue.assert_called_once_with(
                    "temp_queue",
                    durable=False,
                    exclusive=True,
                    auto_delete=True
                )

    @pytest.mark.asyncio
    async def test_declare_queue_without_connection_fails(self):
        broker = AMQPBroker()
        
        with pytest.raises(RuntimeError, match="Broker not connected"):
            await broker.declare_queue("test_queue")

    @pytest.mark.asyncio
    async def test_consume_setup(self, mock_connection):
        connection, channel, queue = mock_connection
        
        async def handler(message: bytes):
            pass
        
        with patch('aio_pika.connect_robust', return_value=connection):
            async with AMQPBroker() as broker:
                await broker.consume("test_queue", handler)
                
                # Verify queue was declared and retrieved
                channel.declare_queue.assert_called_once()
                channel.get_queue.assert_called_once_with("test_queue")

    @pytest.mark.asyncio
    async def test_consume_without_connection_fails(self):
        broker = AMQPBroker()
        
        async def handler(message: bytes):
            pass
        
        with pytest.raises(RuntimeError, match="Broker not connected"):
            await broker.consume("test_queue", handler)

    @pytest.mark.asyncio
    async def test_consumer_task_creation(self, mock_connection):
        """Test that consumer tasks are created and cleaned up properly"""
        connection, channel, queue = mock_connection
        
        async def handler(message: bytes):
            pass
        
        with patch('aio_pika.connect_robust', return_value=connection):
            broker = AMQPBroker()
            await broker.connect()
            
            # Initially no consumer tasks
            assert len(broker._consumer_tasks) == 0
            
            # Start consuming
            await broker.consume("test_queue", handler)
            
            # Should have one consumer task
            assert len(broker._consumer_tasks) == 1
            
            # Disconnect should clean up tasks
            await broker.disconnect()
            assert len(broker._consumer_tasks) == 0

    @pytest.mark.asyncio
    async def test_publish_calls_channel_correctly(self, mock_connection):
        """Test that publishing calls the channel with correct parameters"""
        connection, channel, queue = mock_connection
        
        with patch('aio_pika.connect_robust', return_value=connection):
            async with AMQPBroker() as broker:
                # Test basic publish
                await broker.publish("my_queue", b"test payload")
                
                # Verify channel.default_exchange.publish was called
                channel.default_exchange.publish.assert_called_once()
                call_args = channel.default_exchange.publish.call_args
                
                # Check message content
                message = call_args[0][0]
                assert message.body == b"test payload"
                assert call_args[1]['routing_key'] == "my_queue"

    @pytest.mark.asyncio
    async def test_multiple_publishes(self, mock_connection):
        """Test multiple publish calls work correctly"""
        connection, channel, queue = mock_connection
        
        with patch('aio_pika.connect_robust', return_value=connection):
            async with AMQPBroker() as broker:
                # Publish multiple messages
                await broker.publish("queue1", b"message1")
                await broker.publish("queue2", b"message2")
                
                # Should have called publish twice
                assert channel.default_exchange.publish.call_count == 2

    @pytest.mark.asyncio
    async def test_disconnect_cancels_consumer_tasks(self, mock_connection):
        connection, channel, queue = mock_connection
        
        # Setup infinite iterator to keep consumer running
        async def infinite_iter():
            while True:
                await asyncio.sleep(0.01)
                yield AsyncMock()
        
        queue.iterator.return_value.__aiter__ = infinite_iter
        
        async def handler(message: bytes):
            pass
        
        with patch('aio_pika.connect_robust', return_value=connection):
            broker = AMQPBroker()
            await broker.connect()
            
            # Start consumer
            await broker.consume("test_queue", handler)
            
            # Verify task was created
            assert len(broker._consumer_tasks) == 1
            
            # Disconnect should cancel tasks
            await broker.disconnect()
            
            # Verify tasks were cleaned up
            assert len(broker._consumer_tasks) == 0

    @pytest.mark.asyncio
    async def test_custom_connection_string(self, mock_connection):
        connection, channel, queue = mock_connection
        custom_url = "amqp://user:pass@remote:5672/vhost"
        
        with patch('aio_pika.connect_robust') as mock_connect:
            mock_connect.return_value = connection
            
            broker = AMQPBroker(custom_url)
            await broker.connect()
            
            mock_connect.assert_called_once_with(custom_url)

    @pytest.mark.asyncio
    async def test_default_connection_string(self, mock_connection):
        connection, channel, queue = mock_connection
        
        with patch('aio_pika.connect_robust') as mock_connect:
            mock_connect.return_value = connection
            
            broker = AMQPBroker()  # Use default connection string
            await broker.connect()
            
            mock_connect.assert_called_once_with("amqp://admin:admin@localhost:5672/")
