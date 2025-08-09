from interfaces.log_repository import AbstractLogRepository
from logs.models import Log, Level
from typing import List, Optional
from beanie import Document
from beanie.operators import Expr


class MongoLogDocument(Document, Log):
    """
    Document model for MongoDB

    This class inherits from the Log model from the app.logs.models module, but also adds Beanie-based document functionality.
    In case you need to add support for another database, you need to develop a counterpart of this class, using another ODM
    (e.g. PynamoDB for DynamoDB).
    """

    class Settings:
        name = "logs"

    def to_log(self) -> Log:
        return Log(**self.model_dump())

    @classmethod
    def from_log(cls, log: Log):
        return cls(**log.model_dump())


class MongoLogRepository(AbstractLogRepository):
    """
    MongoDB implementation of the AbstractLogRepository interface.

    This class provides methods for inserting, retrieving, and querying logs stored in MongoDB.
    Similar to the MongoLogDocument, if you need to add support for another database, you need to develop a counterpart of this class too.
    """

    async def insert(self, log: Log):
        return await MongoLogDocument.from_log(log).create()

    async def get(self, uid: str) -> Optional[Log]:
        doc = await MongoLogDocument.find_one({"uid": uid})
        return doc.to_log() if doc else None

    async def all(self) -> List[Log]:
        docs = await MongoLogDocument.find_all().to_list()
        return [doc.to_log() for doc in docs]

    async def find_by_tag(self, tag: str) -> List[Log]:
        docs = await MongoLogDocument.find({"tag": tag}).to_list()
        return [doc.to_log() for doc in docs]

    async def find_by_level(self, level: Level) -> List[Log]:
        if isinstance(level, str):
            level = Level(level)
        if not isinstance(level, Level):
            raise TypeError(f"'{level}' is not a valid Level")
        docs = await MongoLogDocument.find({"level": level}).to_list()
        return [doc.to_log() for doc in docs]

    async def find_by_group_path(self, group_path: List[str]) -> List[Log]:
        docs = await MongoLogDocument.find({"group_path": group_path}).to_list()
        return [doc.to_log() for doc in docs]

    async def find_children_by_group_path(self, group_path: List[str]) -> List[Log]:
        # Match all logs whose group_path starts with the given path
        docs = await MongoLogDocument.find(
            Expr({"$eq": [{"$slice": ["$group_path", len(group_path)]}, group_path]})
        ).to_list()
        return [doc.to_log() for doc in docs]
