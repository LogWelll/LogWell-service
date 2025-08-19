from fastapi.encoders import jsonable_encoder
import pytest
from logs.schemas import LogCreateSchema
from logs.models import Level
from repositories.mongo_repository import MongoLogRepository
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
from logs.models import Log
from datetime import datetime
import uuid
from kombu.exceptions import OperationalError


async def test_create_log(
    test_log_schema: LogCreateSchema, repo: MongoLogRepository
) -> Log:
    """
    Test to verify that the create_log function successfully creates a log in the database.
    """
    log_schema = test_log_schema
    log: Log = await create_log(log_schema.model_dump(), repo)

    assert log.tenant == log_schema.tenant
    assert log.log == log_schema.log
    assert log.metadata == log_schema.metadata
    assert log.level == log_schema.level
    assert log.tag == log_schema.tag
    assert isinstance(log.uid, str)
    assert isinstance(log.created_at, datetime)
    assert isinstance(uuid.UUID(log.uid), uuid.UUID)


@pytest.mark.asyncio
async def test_read_log(test_log: Log, repo: MongoLogRepository):
    """
    Test to verify that the read_log function successfully retrieves a log from the database given its uid.
    """
    log: Log = test_log

    queried_log = await read_log(log.uid, repo)
    assert queried_log.uid == log.uid


@pytest.mark.asyncio
async def test_read_logs_list(
    test_create_log_list: list[Log], repo: MongoLogRepository
):
    test_logs: list[Log] = test_create_log_list
    queried_logs, total = await read_logs_list(repo)
    assert len(test_logs) == len(queried_logs)
    assert len(test_logs) == total


@pytest.mark.asyncio
async def test_read_logs_by_level(test_log: Log, repo: MongoLogRepository):
    log = test_log
    queried_by_tag_logs, total = await read_logs_by_level("INFO", repo)
    assert len(queried_by_tag_logs) == 1
    assert log.tag == queried_by_tag_logs[0].tag
    assert total == 1


@pytest.mark.asyncio
async def test_read_logs_by_empty_level(repo: MongoLogRepository):
    queried_by_tag_logs, total = await read_logs_by_level(Level.CRITICAL, repo)
    assert len(queried_by_tag_logs) == 0
    assert total == 0


@pytest.mark.asyncio
async def test_read_logs_by_tag(test_log: Log, repo: MongoLogRepository):
    log = test_log
    queried_by_tag_logs, total = await read_logs_by_tag(log.tag, repo)
    assert total == 1
    assert len(queried_by_tag_logs) == 1
    assert log.tag == queried_by_tag_logs[0].tag


@pytest.mark.asyncio
async def test_read_logs_by_empty_tag(repo: MongoLogRepository):
    queried_by_tag_logs, total = await read_logs_by_tag("non_existing_tag", repo)
    assert len(queried_by_tag_logs) == 0
    assert total == 0


@pytest.mark.asyncio
async def test_read_logs_by_group_path(grouped_logs, repo: MongoLogRepository):
    logs, total = await read_logs_by_group_path("root-section", repo)
    assert total == 1
    assert len(logs) == 1  # Only the exact match
    assert logs[0].group_path == ["root", "section"]


@pytest.mark.asyncio
async def test_read_logs_by_empty_group_path(repo: MongoLogRepository):
    logs, total = await read_logs_by_group_path("non-existing-group-path", repo)
    assert total == 0
    assert len(logs) == 0


@pytest.mark.asyncio
async def test_read_logs_by_group_path_children(grouped_logs, repo: MongoLogRepository):
    logs, total = await read_logs_by_group_path_children("root-section", repo)
    paths = [log.group_path for log in logs]
    assert any(["child" in path for path in paths])
    assert len(logs) >= 2
    assert total


# The following test is not working because mongomock does not support such complex queries.
# @pytest.mark.asyncio
# async def test_read_logs_by_empty_group_path_children(repo: MongoLogRepository):
#     logs = await read_logs_by_group_path_children("non-existing-group-path", repo)
#     assert len(logs) == 0


@pytest.mark.asyncio
async def test_create_log_non_blocking_success(
    test_log_schema: LogCreateSchema, mocker
):
    sample_record = test_log_schema.model_dump()

    celery_app_mock = mocker.Mock()

    # Use MagicMock for context manager support
    connection_mock = mocker.MagicMock()
    connection_mock.ensure_connection.return_value = None

    context_manager_mock = mocker.MagicMock()
    context_manager_mock.__enter__.return_value = connection_mock
    celery_app_mock.connection_or_acquire.return_value = context_manager_mock

    # Patch the Celery task
    delay_mock = mocker.patch("tasks.create_log_task.delay")

    result = await create_log_non_blocking(sample_record, celery_app_mock)

    delay_mock.assert_called_once_with(jsonable_encoder(sample_record))
    assert result == sample_record


@pytest.mark.asyncio
async def test_create_log_non_blocking_connection_failure(
    test_log_schema: LogCreateSchema, mocker
):
    from fastapi import HTTPException
    from logs.errors import ServiceUnavailableError

    sample_record = test_log_schema.model_dump()

    # Mock celery app
    celery_app_mock = mocker.Mock()

    # Raise OperationalError when acquiring the connection
    context_manager_mock = mocker.MagicMock()
    context_manager_mock.__enter__.side_effect = OperationalError()
    celery_app_mock.connection_or_acquire.return_value = context_manager_mock

    # Patch the Celery task just in case (though it should not be called)
    delay_mock = mocker.patch("tasks.create_log_task.delay")

    with pytest.raises(HTTPException) as exc_info:
        await create_log_non_blocking(sample_record, celery_app_mock)

    # Ensure Celery task was never called
    delay_mock.assert_not_called()

    # Optional: check that the raised error matches the expected exception
    assert exc_info.value.status_code == ServiceUnavailableError().error.status_code
