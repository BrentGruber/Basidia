import asyncio
from collections import defaultdict, deque
from typing import Callable, Any, Dict, Set
from .base import MessageBroker


class MemoryBroker(MessageBroker):
    """In-memory message broker for testing and development"""

    def __init__(self, connection_string: str = "memory://localhost"):
        super().__init__(connection_string)
        self._queues: Dict[str, deque] = defaultdict(deque)
        self._consumers: Dict[str, Set[Callable]] = defaultdict(set)
        self._consumer_tasks: Set[asyncio.Task] = set()

    async def connect(self) -> None:
        """Memory broker is always connected"""
        self._connected = True

    async def disconnect(self) -> None:
        """Stop all consumer tasks and clear state"""
        # Cancel all consumer tasks
        for task in self._consumer_tasks:
            task.cancel()

        # Wait for tasks to finsih
        if self._consumer_tasks:
            await asyncio.gather(*self._consumer_tasks, return_exceptions=True)

        self._consumer_tasks.clear()
        self._connected = False

    async def publish(self, routing_key: str, message: bytes, **kwargs) -> None:
        """Add message to the queue"""
        if not self._connected:
            raise RuntimeError("Broker not connected")

        # In memory broker, routing key is the queue name
        self._queues[routing_key].append(message)

        # Notify any waiting consumers
        await self._process_queue(routing_key)

    async def consume(self, queue: str, handler: Callable[[bytes], Any]) -> None:
        """Start consuming messages from a queue"""
        if not self._connected:
            raise RuntimeError("Broker not connected")

        self._consumers[queue].add(handler)

        # Start a task to process existing messages
        task = asyncio.create_task(self._consumer_loop(queue, handler))
        self._consumer_tasks.add(task)

    async def declare_queue(self, queue_name: str, **kwargs) -> None:
        """Ensure queue exists (no-op for memory broker)"""
        if queue_name not in self._queues:
            self._queues[queue_name] = deque()

    async def _process_queue(self, queue_name: str) -> None:
        """Process messages in a queue for all consumers"""
        queue = self._queues[queue_name]
        consumers = self._consumers[queue_name]

        while queue and consumers:
            message = queue.popleft()
            # Send to all consumers (broadcast)
            for handler in consumers.copy(): # Copy to avoid modifying original during loop
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(message)
                    else:
                        handler(message)
                except Exception as e:
                    print(f"Error processing message: {e}")

    async def _consumer_loop(self, queue_name: str, handler: Callable[[bytes], Any]) -> None:
        """Background task that processes messages for a specific consumer"""
        try:
            while self._connected and handler in self._consumers[queue_name]:
                await asyncio.sleep(0.01) # small delay
                await self._process_queue(queue_name)
        except asyncio.CancelledError:
            # Clean up when task is cancelled
            if handler in self._consumers[queue_name]:
                self._consumers[queue_name].remove(handler)
            raise

    ## Utility methods
    def get_queue_size(self, queue_name: str) -> int:
        """Get number of messages in queue (for testing)"""
        return len(self._queues[queue_name])

    def clear_queue(self, queue_name: str) -> None:
        """Clear all messages from a queue for testing)"""
        self._queues[queue_name].clear()
