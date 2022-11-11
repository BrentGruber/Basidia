import aio_pika
import asyncio


class RMQ:

    def __init__(self):
        self.CONNECTION_STRING="amqp://user:bitnami@127.0.0.1:5672/"

    async def connect(self, loop):
        # Connect with the givien parameters is also valiable.
        # aio_pika.connect_robust(host="host", login="login", password="password")
        # You can only choose one option to create a connection, url or kw-based params.
        self.connection = await aio_pika.connect_robust(
            self.CONNECTION_STRING, loop=loop
        )

    async def consume(self, queue):
        async with queue.iterator() as queue_iter:
            # Cancel consuming after __aexit__
            async for message in queue_iter:
                async with message.process():
                    print(message.body)
                    if queue.name in message.body.decode():
                        break


async def main(loop):
    rmq = RMQ()
    await rmq.connect(loop)
    queue_name = "test_queue"
    # Declaring queue
    queue: aio_pika.abc.AbstractQueue = await rmq.connection.channel().declare_queue(
        queue_name,
        auto_delete=True
    )

    rmq.consume(queue)

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(loop))
    loop.close()


    


    