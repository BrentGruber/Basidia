import pytest
import asyncio
from basidia.brokers.memory import MemoryBroker

class TestMemoryBroker:

    @pytest.mark.asyncio
    async def test_connection_lifecycle(self):
        broker = MemoryBroker()

        # Initially not connected
        assert not broker.is_connected

        # Connect
        await broker.connect()
        assert broker.is_connected

        # Disconnect
        await broker.disconnect()
        assert not broker.is_connected

    @pytest.mark.asyncio
    async def test_context_manager(self):
        async with MemoryBroker() as broker:
            assert broker.is_connected

        # Should be disconnected after context
        assert not broker.is_connected

    @pytest.mark.asyncio
    async def test_publish_and_queue_size(self):
        async with MemoryBroker() as broker:
            await broker.declare_queue("test_queue")

            # INitially empty
            assert broker.get_queue_size("test_queue") == 0

            # Publish message
            await broker.publish("test_queue", b"hello world")
            assert broker.get_queue_size("test_queue") == 1

    @pytest.mark.asyncio
    async def test_consume_single_message(self):
        async with MemoryBroker() as broker:
            received_messages = []

            async def handler(message: bytes):
                received_messages.append(message)

            # Start consuming
            await broker.consume("test_queue", handler)

            # Publish message
            await broker.publish("test_queue", b"test message")

            # Give consumer time to process
            await asyncio.sleep(0.1)

            assert len(received_messages) == 1
            assert received_messages[0] == b"test message"

    @pytest.mark.asyncio
    async def test_multiple_messages(self):
        async with MemoryBroker() as broker:
            received_messages = []

            async def handler(message: bytes):
                received_messages.append(message)

            await broker.consume("test_queue", handler)

            messages = [b"msg1", b"msg2", b"msg3"]
            for msg in messages:
                await broker.publish("test_queue", msg)

            # Wait for processing
            await asyncio.sleep(0.1)

            assert len(received_messages) == 3
            assert received_messages == messages

    @pytest.mark.asyncio
    async def test_multiple_consumers(self):
        async with MemoryBroker() as broker:
            consumer1_messages = []
            consumer2_messages = []

            async def handler1(message: bytes):
                consumer1_messages.append(message)

            async def handler2(message: bytes):
                consumer2_messages.append(message)

            # Both consumers will listen to the same queue
            await broker.consume("shared_queue", handler1)
            await broker.consume("shared_queue", handler2)

            message = b"broadcast message"
            await broker.publish("shared_queue", message)

            await asyncio.sleep(0.1)

            # Both consumers should receive the message
            assert consumer1_messages == [message]
            assert consumer2_messages == [message]

    @pytest.mark.asyncio
    async def test_error_handling_in_consumer(self):
        async with MemoryBroker() as broker:
            processed_messages = []

            async def failing_handler(message: bytes):
                if message == b"fail":
                    raise ValueError("Simulated error")
                processed_messages.append(message)

            await broker.consume("error_queue", failing_handler)

            # Publish good and bad messages
            await broker.publish("error_queue", b"good")
            await broker.publish("error_queue", b"fail")
            await broker.publish("error_queue", b"also_good")

            await asyncio.sleep(0.1)

            # Should process good messages despite error
            assert len(processed_messages) == 2
            assert b"good" in processed_messages
            assert b"also_good" in processed_messages

    @pytest.mark.asyncio
    async def test_publish_without_connection_fails(self):
        broker = MemoryBroker()

        with pytest.raises(RuntimeError, match="Broker not connected"):
            await broker.publish("test_queue", b"message")

    @pytest.mark.asyncio
    async def test_consume_without_connection_fails(self):
        broker = MemoryBroker()

        async def handler(message: bytes):
            pass

        with pytest.raises(RuntimeError, match="Broker not connected"):
            await broker.consume("test_queue", handler)

    @pytest.mark.asyncio
    async def test_clear_queue_utility(self):
        async with MemoryBroker() as broker:
            await broker.publish("test_queue", b"messsage1")
            await broker.publish("test_queue", b"message2")

            assert broker.get_queue_size("test_queue") == 2

            broker.clear_queue("test_queue")
            assert broker.get_queue_size("test_queue") == 0
