from logs.routes import get_celery_app
import httpx
from fastapi import status
from fastapi.encoders import jsonable_encoder
from logs.schemas import LogCreateSchema
from logs.models import Log, Level
from base_error import NotFoundError
from main import app


async def test_create_log(
    client: httpx.Client, test_log_schema: LogCreateSchema, header: dict
):
    """
    Test to verify that the POST endpoint for creating a log successfully creates a log in the database.
    """

    response = await client.post(
        "/logs/", json=test_log_schema.model_dump(), headers=header("valid")
    )
    assert response.status_code == status.HTTP_201_CREATED


async def test_read_valid_log_uid(client: httpx.Client, test_log: Log, header: dict):
    """
    Test to verify that the GET endpoint for retrieving a log by its uid successfully retrieves the log when given a valid uid.
    """
    log = test_log

    response = await client.get(f"/logs/{log.uid}", headers=header("valid"))
    assert response.status_code == status.HTTP_200_OK
    assert response.json().get("data").get("uid") == log.uid


async def test_read_invalid_log_uid(client: httpx.Client, header: dict):
    """
    Test to verify that the GET endpoint for retrieving a log by its uid returns a 404
    status code and the correct error message when given an invalid uid.
    """
    response = await client.get("/logs/invalid_log_uid", headers=header("valid"))
    assert response.status_code == NotFoundError().error.status_code
    assert response.json().get("detail") == NotFoundError().error.detail


async def test_read_log_list(
    client: httpx.Client, test_create_log_list: list[Log], header: dict
):
    """
    Test to verify that the GET endpoint for retrieving the list of logs
    successfully returns all logs in the database.
    """

    response = await client.get("/logs/", headers=header("valid"))
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json().get("data")) == len(test_create_log_list)


async def test_read_log_list_with_tag(
    client: httpx.Client, test_create_log_list: list[Log], header: dict
):
    """
    Test to verify that the GET endpoint for retrieving a list of logs by tag
    successfully returns a list of logs with the given tag when given a valid tag.
    """
    response = await client.get("/logs/tag/test_tag", headers=header("valid"))
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json().get("data")) == len(test_create_log_list)


async def test_read_log_list_with_empty_tag(client: httpx.Client, header: dict):
    """
    Test to verify that the GET endpoint for retrieving logs by a tag
    returns an empty list when the specified tag does not exist.
    """

    response = await client.get("/logs/tag/empty_tag", headers=header("valid"))
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json().get("data")) == 0


async def test_read_log_list_with_level(
    client: httpx.Client, test_create_log_list: list[Log], header: dict
):
    """
    Test to verify that the GET endpoint for retrieving logs by level
    successfully returns a list of logs with the given level when given a valid level.
    """

    response = await client.get(f"/logs/level/{Level.INFO}", headers=header("valid"))
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json().get("data")) == len(test_create_log_list)


async def test_read_log_list_with_empty_level(client: httpx.Client, header: dict):
    """
    Test to verify that the GET endpoint for retrieving logs by level
    returns an empty list when the specified level does not exist.
    """
    response = await client.get(f"/logs/level/{Level.DEBUG}", headers=header("valid"))
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json().get("data")) == 0


async def test_read_log_list_with_invalid_level(client: httpx.Client, header: dict):
    """
    Test to verify that the GET endpoint for retrieving logs by level
    returns an appropriate error when given an invalid level.
    """
    response = await client.get("/logs/level/invalid_level", headers=header("valid"))
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


async def test_read_log_list_with_group_path(
    client: httpx.Client, grouped_logs: list[Log], header: dict
):
    """
    Test to verify that the GET endpoint for retrieving logs by group path
    successfully returns a list of logs with the given group path when given a valid group path.
    """
    response = await client.get("/logs/group/root-section/", headers=header("valid"))
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json().get("data")) == 1


async def test_read_log_list_with_empty_group_path(client: httpx.Client, header: dict):
    """
    Test to verify that the GET endpoint for retrieving logs by group path
    returns an empty list when the specified group path does not exist.
    """
    response = await client.get(
        "/logs/group/empty-group-path/", headers=header("valid")
    )
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json().get("data")) == 0


async def test_read_log_list_with_group_path_children(
    client: httpx.Client, grouped_logs: list[Log], header: dict
):
    """
    Test to verify that the GET endpoint for retrieving logs by group path children
    successfully returns a list of logs that are defined under the given group path
    when given a valid group path.
    """
    response = await client.get(
        "/logs/group/root-section/children/", headers=header("valid")
    )
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json().get("data")) == len(grouped_logs)


## The following test is not working because mongomock does not support such complex queries.

# async def test_read_log_list_with_empty_group_path_children(
#     client: httpx.Client, test_log: Log
# ):

#     """
#     Test to verify that the GET endpoint for retrieving logs by group path children
#     returns an empty list when the specified group path does not exist.
#     """

#     response = await client.get("/logs/group/empty-group-path/children/")
#     assert response.status_code == status.HTTP_200_OK
#     assert len(response.json().get("data")) == 0


async def test_post_log_non_blocking_accepted(
    client: httpx.AsyncClient, test_log_schema: LogCreateSchema, mocker, header: dict
):
    """
    Test to verify that the POST endpoint for creating logs non-blocking
    successfully queues a job and returns a 202 Accepted status code
    when given a valid log to create.
    """
    sample_record = test_log_schema.model_dump()

    celery_app_mock = mocker.Mock()
    connection_mock = mocker.MagicMock()
    connection_mock.ensure_connection.return_value = None

    context_manager_mock = mocker.MagicMock()
    context_manager_mock.__enter__.return_value = connection_mock
    celery_app_mock.connection_or_acquire.return_value = context_manager_mock

    delay_mock = mocker.patch("tasks.create_log_task.delay")

    app.dependency_overrides[get_celery_app] = lambda: celery_app_mock

    response = await client.post(
        "/logs/non-blocking/", json=sample_record, headers=header("valid")
    )

    assert response.status_code == status.HTTP_202_ACCEPTED
    delay_mock.assert_called_once_with(jsonable_encoder(sample_record))

    app.dependency_overrides.clear()


async def test_post_log_non_blocking_service_unavailable(
    client: httpx.AsyncClient, test_log_schema: LogCreateSchema, header: dict
):
    """
    Test to verify that the POST endpoint for creating a log in non-blocking mode
    returns a 503 Service Unavailable status code when the message queue service
    is not available.
    """

    response = await client.post(
        "/logs/non-blocking/",
        json=test_log_schema.model_dump(),
        headers=header("valid"),
    )

    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
