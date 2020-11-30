import asyncio
import aio_pika
import json
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Union


class UndeliverableMessage(Exception):
    """ 
    Raised when publisher confirms are enabled and a message could not
    be routed or persisted 
    """

@asynccontextmanager
async def get_connection(amqp_uri: str):

    conn = await aio_pika.connect_robust(amqp_uri)
    try:
        yield conn
    finally:
        await conn.close()


class Publisher(object):
    """
    Utility helper for publishing messages to RabbitMQ.
    """
    def __init__(self, amqp_uri):
        self.amqp_uri = amqp_uri

    async def publish(self, topic: str, payload: Union[Dict[Any,Any],List[Any]]):
        """
        publish a message
        """
        async with get_connection(self.amqp_uri) as conn:
            routing_key = topic

            channel = await conn.channel()

            await channel.default_exchange.publish(
                aio_pika.Message(body=json.dumps(payload).encode()),
                routing_key=routing_key
            )