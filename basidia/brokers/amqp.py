import asyncio
from typing import Callable, Any, Dict, Set
import aio_pika
from aio_pika.abc import AbstractConnection, AbstractChannel
from .base import MessageBroker

class AMQPBroker(MessageBroker):
    """Message Broker class that is able to connect to an AMQP compatible Broker"""

    def __init__(self, connection_string: str = "amqp://admin:admin@localhost:5672/"):
        super().__init__(connection_string)
        self._connection: AbstractConnection = None
        self._channel: AbstractChannel = None
        self._consumer_tasks: set[asyncio.Task] = set()

    async def connect(self) -> None:
        """Establish a connection to an AMQP broker"""
        try:
            self._connection = await aio_pika.connect_robust(self.connection_string)
            self._channel = await self._connection.channel()
            self._connected = True
        except Exception as e:
            raise RuntimeError(f"Failed to connect to AMQP Broker: {e}")

    async def disconnect(self) -> None:
        """Close connection to the broker"""
        for task in self._consumer_tasks:
            task.cancel()

        if self._consumer_tasks:
            await asyncio.gather(*self._consumer_tasks, return_exceptions=True)

        self._consumer_tasks.clear()

        if self._channel:
            await self._channel.close()
        if self._connection:
            await self._connection.close()

        self._connected = False

    async def publish(self, routing_key: str, message: bytes, **kwargs) -> None:
        """Publish a message to the broker"""
        if not self._connected:
            raise RuntimeError("Broker not connected")

        amqp_message = aio_pika.Message(
                message,
                delivery_mode=kwargs.get("delivery_mode", aio_pika.DeliveryMode.PERSISTENT) # Default to a persistent delivery mode if none is provided
        )

        await self._channel.default_exchange.publish(
                amqp_message,
                routing_key=routing_key
        )

    async def consume(self, queue: str, handler: Callable[[bytes], Any]) -> None:
        """Start consuming messages from a queue"""
        if not self._connected:
            raise RuntimeError("Broker not connected")

        # Declare the queueu
        await self.declare_queue(queue)

        # get the queue
        amqp_queue = await self._channel.get_queue(queue)

        # Start consuming
        task = asyncio.create_task(self._consumer_loop(amqp_queue, handler))
        self._consumer_tasks.add(task)

    async def declare_queue(self, queue_name: str, **kwargs) -> None:
        """Declare/create a queue"""
        if not self._connected:
            raise RuntimeError("Broker not connected")

        await self._channel.declare_queue(
                queue_name,
                durable=kwargs.get("durable", True),
                exclusive=kwargs.get("exclusive", False),
                auto_delete=kwargs.get("auto_delete", False)
        )

    async def _consumer_loop(self, queue, handler: Callable[[bytes], Any]) -> None:
        """Background task that processes messages for a specific consumer"""
        try:
            async with queue.iterator() as queue_iter:
                async for message in queue_iter:
                    try:
                        if asyncio.iscoroutinefunction(handler):
                            await handler(message.body)
                        else:
                            handler(message.body)

                        # Ack message
                        await message.ack()
                    except Exception as e:
                        print(f"Error processing message: {e}")
                        await message.nack(requeue=False)
        except asyncio.CancelledError:
            raise


