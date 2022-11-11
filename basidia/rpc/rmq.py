import aio_pika
import asyncio
import logging

class RpcConsumer:

    queue_name = "test_queue"

    async def process_message(self, message: aio_pika.abc.AbstractIncomingMessage) -> None:
        async with message.process():
            print(message.body)
            await asyncio.sleep(1)

    
    async def handle_message(self):

        connection = await aio_pika.connect_robust(
            "amqp://user:bitnami@127.0.0.1/"
        )

        async with connection:
            # Create channel
            channel = await connection.channel()

            # Take no more than 10 messages in advance
            await channel.set_qos(prefetch_count=10)

            # Declaring queue
            queue = await channel.declare_queue(self.queue_name, auto_delete=True)

            await queue.consume(self.process_message)

            try:
                # Wait until terminate
                await asyncio.Future()
            finally:
                await connection.close()


class RpcProducer:

    queue_name = "test_queue"

    async def publish_message(self):
        connection = await aio_pika.connect_robust(
            "amqp://user:bitnami@127.0.0.1/"
        )

        async with connection:
            channel = await connection.channel()

            await channel.default_exchange.publish(
                aio_pika.Message(body=f"Hello World".encode()),
                routing_key=self.queue_name,
            )

async def main():
    logging.basicConfig(level=logging.INFO)
    
    consumer = RpcConsumer()
    producer = RpcProducer()

    #await producer.publish_message()
    await asyncio.sleep(5)
    await consumer.handle_message()
    
    
    

if __name__ == "__main__":
    loop = asyncio.run(main())
