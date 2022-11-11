import abc


class AbstractRpcConsumer(abc.ABC):

    @abc.abstractmethod
    async def setup(self):
        raise NotImplementedError

    @abc.abstractmethod
    async def stop(self):
        raise NotImplementedError

    @abc.abstractmethod
    async def handle_message(self, body, message):
        raise NotImplementedError

    @abc.abstractmethod
    async def handle_result(self, message, result, exc_info):
        raise NotImplementedError

    @abc.abstractmethod
    async def requeue_message(self, message):
        raise NotImplementedError