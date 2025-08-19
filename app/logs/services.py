from interfaces.log_repository import AbstractLogRepository
from logs.models import Log
from celery import Celery
from fastapi.encoders import jsonable_encoder
from tasks import create_log_task
from kombu.exceptions import OperationalError
from base_error import NotFoundError
from logs.errors import ServiceUnavailableError


async def create_log(record: dict, repo: AbstractLogRepository) -> Log:
    log = Log(**record)

    await repo.insert(log)

    return log


async def read_log(uid: str, repo: AbstractLogRepository) -> Log:
    log = await repo.get(uid)

    if not log:
        raise NotFoundError().error

    return log


async def read_logs_list(
    repo: AbstractLogRepository, offset: int = 0, limit: int = 10
) -> list[Log]:
    return await repo.all(offset, limit)


async def read_logs_by_tag(
    tag: str, repo: AbstractLogRepository, offset: int = 0, limit: int = 10
) -> list[Log]:
    return await repo.find_by_tag(tag, offset, limit)


async def read_logs_by_level(
    level: str, repo: AbstractLogRepository, offset: int = 0, limit: int = 10
) -> list[Log]:
    return await repo.find_by_level(level, offset, limit)


async def read_logs_by_group_path(
    group_path: str, repo: AbstractLogRepository, offset: int = 0, limit: int = 10
) -> list[Log]:
    group_path_list = group_path.split("-")
    return await repo.find_by_group_path(group_path_list, offset, limit)


async def read_logs_by_group_path_children(
    group_path: str, repo: AbstractLogRepository, offset: int = 0, limit: int = 10
) -> list[Log]:
    group_path_list = group_path.split("-")
    return await repo.find_children_by_group_path(group_path_list, offset, limit)


async def create_log_non_blocking(record: dict, celery_app: Celery):
    import logging

    try:
        logging.warning("starting")
        with celery_app.connection_or_acquire() as conn:
            conn.ensure_connection(max_retries=1, timeout=2)
        create_log_task.delay(jsonable_encoder(record))
        return record

    except OperationalError:
        raise ServiceUnavailableError().error
