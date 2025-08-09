# interfaces/log_repository.py
from abc import ABC, abstractmethod
from typing import List, Optional
from logs.models import Log, Level


class AbstractLogRepository(ABC):
    @abstractmethod
    async def insert(self, log: Log) -> None: ...

    @abstractmethod
    async def get(self, uid: str) -> Optional[Log]: ...

    @abstractmethod
    async def all(self) -> List[Log]: ...

    @abstractmethod
    async def find_by_tag(self, tag: str) -> List[Log]: ...

    @abstractmethod
    async def find_by_level(self, level: Level) -> List[Log]: ...

    @abstractmethod
    async def find_by_group_path(self, group_path: List[str]) -> List[Log]: ...

    @abstractmethod
    async def find_children_by_group_path(self, group_path: List[str]) -> List[Log]: ...
