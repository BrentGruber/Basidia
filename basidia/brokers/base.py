from abc import ABC, abstractmethod
from typing import Callable, Any, Optional
import asyncio

class MessageBroker(ABC):
    """Abstract base class for message brokers supported by Basidia"""

    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self._connected = False

    @abstractmethod
    async def connect(self) -> None:
        """Establish connection to the broker"""
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Close connection to the broker"""
        pass

    @abstractmethod
    async def publish(self, routing_key: str, message: bytes, **kwargs) -> None:
        """Publish a message to the broker"""
        pass

    @abstractmethod
    async def consume(self, queue: str, handler: Callable[[bytes], Any]) -> None:
        """Start consuming messages from a queue"""
        pass

    @abstractmethod
    async def declare_queue(self, queue_name: str, **kwargs) -> None:
        """Declare/create a queue"""
        pass

    @property
    def is_connected(self) -> bool:
        return self._connected

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.disconnect()
