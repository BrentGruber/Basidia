import pytest
from unittest.mock import create_autospec
from basidia.rpc import (Rpc, RpcProxy, rpc)

hello = object()


class ExampleError(Exception):
    pass

class ExampleService(object):
    name = 'exampleservice'

    example_rpc = RpcProxy('exampleservice')
    unknown_rpc = RpcProxy('unknown_service')

    @rpc
    async def task_a(self, *args, **kwargs):
        return "result_a"

    @rpc
    def task_b(self, *args, **kwargs):
        return "result_b"

    @rpc
    async def call_async(self):
        res1 = await self.example_rpc.task_a.call_async()
        res2 = await self.example_rpc.task_b.call_async()
        res3 = await self.example_rpc.echo.call_async()
        return [res2.result(), res1.result(), res3.result()]

    @rpc
    async def call_unknown(self):
        return await self.unknown_rpc.any_method()

    @rpc
    def echo(self, *args, **kwargs):
        return args, kwargs

    @rpc
    def say_hello(self):
        return "hello"
    
    @event_handler('srcservice', 'eventtype')
    def async_task(self):
        pass # pragma: no cover

    @rpc
    async def raises(self):
        raise ExampleError("error")

@pytest.fixture
def get_rpc_exchange():
    with patch('basidia.rpc.get_rpc_exchange', autospec=True) as patched:
        yield patched

@pytest.fixture
def queue_consumer():
    replacement = create_autospec(QueueConsumer)
    with patch.object(QueueConsumer, 'bind') as mock_ext:
        mock_ext.return_value = replacement
        yield replacement


async def test_rpc_consumer(get_rpc_exchange, queue_consumer, mock_container):

    container = mock_container
    container.shared_extensions = {}
    container.config = {}
    container.service_name = 'exampleservice'
    container.service_cls = Mock(rpcmethod=lambda: None)

    exchange = Exchange("some_exchange")
    get_rpc_exchange.return_value = exchange

    consumer = RpcConsumer().bind(container)

    entrypoint = Rpc().bind(container, "rpcmethod")
    entrypoint.rpc_consumer = consumer

    entrypoint.setup()
    consumer.setup()
    queue_consumer.setup()

    queue = consumer.queue
    assert queue.name == "rpc-exampleservice"
    assert queue.routing_key == "exampleservice.*"
    assert queue.exchange == exchange
    assert queue.durable

    queue_consumer.register_provider.assert_called_once_with(consumer)

    consumer.register_provider(entrypoint)
    assert consumer._providers == set([entrypoint])

    routing_key = "exampleservice.rpcmethod"
    assert consumer.get_provider_for_method(routing_key) == entrypoint

    routing_key = "exampleservice.invalidmethod"
    with pytest.raises(MethodNotFound):
        consumer.get_provider_for_method(routing_key)

    consumer.unregister_provider(entrypoint)
    assert consumer._providers == set()
