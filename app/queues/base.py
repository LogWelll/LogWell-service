from abc import ABC, abstractmethod


class AbstractLogQueue(ABC):
    @abstractmethod
    async def enqueue(self, log_data: dict):
        pass
