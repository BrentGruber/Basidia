import abc


class AbstractRpc(abc.ABC):

    @abc.abstractmethod
    async def connect()