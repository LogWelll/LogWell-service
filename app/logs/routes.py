from fastapi import APIRouter, Depends, status, BackgroundTasks
from queues.celery_worker import celery_app
from logs.schemas import LogCreateSchema, LogRetrieveSchema
from logs.models import Level
from interfaces.log_repository import AbstractLogRepository
from celery import Celery
from logs.services import (
    create_log,
    read_log,
    read_logs_list,
    read_logs_by_level,
    read_logs_by_tag,
    read_logs_by_group_path,
    read_logs_by_group_path_children,
    create_log_non_blocking,
)

from base_error import NotFoundError
from logs.errors import ServiceUnavailableError
from tasks import _save_log
from logs.responses import (
    LogCreateResponse,
    LogReadResponse,
    LogReadListResponse,
    NonBlockingLogCreateResponse,
)

logging_router = APIRouter()


def get_repository() -> AbstractLogRepository:
    """
    If you are adding support for another database, you are supposed to return the corresponding repository instead of MongoLogRepository;
    make sure that your repository implements the AbstractLogRepository interface properly.
    """
    from repositories.mongo_repository import MongoLogRepository

    return MongoLogRepository()


def get_celery_app():
    return celery_app


@logging_router.post(
    "/",
    response_model=LogCreateResponse[LogRetrieveSchema],
    status_code=status.HTTP_201_CREATED,
)
async def post_log(
    record: LogCreateSchema, repo: AbstractLogRepository = Depends(get_repository)
):
    """
    Use this endpoint to create a new log.
    """
    log = await create_log(record.model_dump(), repo)

    # return create_log_response(LogRetrieveSchema(**log.model_dump()))
    return LogCreateResponse(data=LogRetrieveSchema(**log.model_dump()))


@logging_router.get(
    "/{uid}",
    response_model=LogReadResponse[LogRetrieveSchema],
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "description": "Log not found",
            "content": {"application/json": {"example": NotFoundError().example}},
        }
    },
)
async def get_log_by_id(
    uid: str,
    repo: AbstractLogRepository = Depends(get_repository),
):
    """
    Use this endpoint to retrieve a log by its uid.
    """
    log = await read_log(uid, repo)

    # return read_log_response(LogRetrieveSchema(**log.model_dump()))
    return LogReadResponse(data=LogRetrieveSchema(**log.model_dump()))


@logging_router.get(
    "/",
    response_model=LogReadListResponse[list[LogRetrieveSchema]],
    status_code=status.HTTP_200_OK,
)
async def get_logs_list(
    repo: AbstractLogRepository = Depends(get_repository),
    offset: int = 0,
    limit: int = 10,
):
    """
    Use this endpoint to retrieve all logs within the database.
    """
    logs, total = await read_logs_list(repo, offset, limit)

    # return read_logs_response([LogRetrieveSchema(**log.model_dump()) for log in logs])
    return LogReadListResponse(
        data=[LogRetrieveSchema(**log.model_dump()) for log in logs], total=total
    )


@logging_router.get(
    "/tag/{tag}",
    response_model=LogReadListResponse[list[LogRetrieveSchema]],
    status_code=status.HTTP_200_OK,
)
async def get_logs_by_tag(
    tag: str,
    repo: AbstractLogRepository = Depends(get_repository),
    offset: int = 0,
    limit: int = 10,
):
    """
    Given a tag, retrieve all logs with that tag using this endpoint.
    """
    logs, total = await read_logs_by_tag(tag, repo, offset, limit)

    # return read_logs_response([LogRetrieveSchema(**log.model_dump()) for log in logs])
    return LogReadListResponse(
        data=[LogRetrieveSchema(**log.model_dump()) for log in logs], total=total
    )


@logging_router.get(
    "/level/{level}",
    response_model=LogReadListResponse[list[LogRetrieveSchema]],
    status_code=status.HTTP_200_OK,
)
async def get_logs_by_level(
    level: Level,
    repo: AbstractLogRepository = Depends(get_repository),
    offset: int = 0,
    limit: int = 10,
):
    """
    Use this endpoint to retrieve all logs with a specific level.
    """
    logs, total = await read_logs_by_level(level, repo, offset, limit)

    # return read_logs_response([LogRetrieveSchema(**log.model_dump()) for log in logs])
    return LogReadListResponse(
        data=[LogRetrieveSchema(**log.model_dump()) for log in logs], total=total
    )


@logging_router.get(
    "/group/{group_path}/",
    response_model=LogReadListResponse[list[LogRetrieveSchema]],
    status_code=status.HTTP_200_OK,
)
async def get_logs_by_group_path(
    group_path: str,
    repo: AbstractLogRepository = Depends(get_repository),
    offset: int = 0,
    limit: int = 10,
):
    """
    Use this endpoint to retrieve all logs with a specific group path.
    The group path is a string of the form "root-node1-node2" and this endpoint will retrieve all logs with this exact group path.
    """
    logs, total = await read_logs_by_group_path(group_path, repo, offset, limit)

    # return read_logs_response([LogRetrieveSchema(**log.model_dump()) for log in logs])
    return LogReadListResponse(
        data=[LogRetrieveSchema(**log.model_dump()) for log in logs], total=total
    )


@logging_router.get(
    "/group/{group_path}/children/",
    response_model=LogReadListResponse[list[LogRetrieveSchema]],
    status_code=status.HTTP_200_OK,
)
async def get_logs_by_group_path_children(
    group_path: str,
    repo: AbstractLogRepository = Depends(get_repository),
    offset: int = 0,
    limit: int = 10,
):
    """
    Use this endpoint to retrieve all logs that are defined under a specific group path.
    Unlike the /logs/group/{group_path} endpoint that returns only the logs with the specific group path,
    this endpoint will retrieve all logs that are defined under the group path.
    """
    logs, total = await read_logs_by_group_path_children(
        group_path, repo, offset, limit
    )

    # return read_logs_response([LogRetrieveSchema(**log.model_dump()) for log in logs])
    return LogReadListResponse(
        data=[LogRetrieveSchema(**log.model_dump()) for log in logs], total=total
    )


@logging_router.post(
    "/non-blocking/",
    response_model=NonBlockingLogCreateResponse[dict],
    status_code=status.HTTP_202_ACCEPTED,
    responses={
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "description": "This endpoint requires an active message queue; such service not found.",
            "content": {
                "application/json": {"example": ServiceUnavailableError().example}
            },
        }
    },
)
async def post_log_non_blocking(
    record: LogCreateSchema, celery_app: Celery = Depends(get_celery_app)
):
    """
    For the cases of high-throughput log creation and to avoid blocking the main thread,
    use this endpoint to create a new log without blocking the main thread. Keep in mind that for this endpoint to be available,
    the message queue and celery worker must be active.
    """

    log = await create_log_non_blocking(record.model_dump(), celery_app)

    # return non_blocking_create_log_response(log)
    return NonBlockingLogCreateResponse(data=log)


@logging_router.post(
    "/non-blocking/builtin/",
    response_model=NonBlockingLogCreateResponse[dict],
    status_code=status.HTTP_202_ACCEPTED,
)
async def post_log_non_blocking_builtin(
    record: LogCreateSchema,
    background_tasks: BackgroundTasks,
    repo: AbstractLogRepository = Depends(get_repository),
):
    """
    For the cases of high-throughput log creation and to avoid blocking the main thread,
    use this endpoint to create a new log without blocking the main thread. This endpoint uses Background tasks
    from FastAPI, therefore this requires no external services (e.g. celery worker and message queue), unlike the non-blocking endpoint.
    """

    background_tasks.add_task(_save_log, record.model_dump())

    # return non_blocking_create_log_response(record.model_dump())
    return NonBlockingLogCreateResponse(data=record.model_dump())
