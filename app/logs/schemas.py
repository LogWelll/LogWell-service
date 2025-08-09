from datetime import datetime
from logs.models import BaseLog


class LogCreateSchema(BaseLog):
    pass


class LogRetrieveSchema(BaseLog):
    uid: str
    created_at: datetime
    group_path: list[str] | None = None
