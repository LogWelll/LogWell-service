from beanie import init_beanie
from repositories.mongo_repository import MongoLogDocument, MongoLogRepository
import pytest_asyncio
import pytest
from logs.schemas import LogCreateSchema
from logs.models import Log, Level
from httpx import ASGITransport, AsyncClient
from main import app


@pytest_asyncio.fixture(scope="function", autouse=True)
async def init_test_db():
    """ "
    Let's use mongomock_motor to mock a MongoDB instance for testing.
    """
    from mongomock_motor import AsyncMongoMockClient

    mock_client = AsyncMongoMockClient()
    db = mock_client["test_db"]
    await init_beanie(database=db, document_models=[MongoLogDocument])


@pytest.fixture
def test_log_schema() -> LogCreateSchema:
    """
    A fixture to create a sample log schema for testing.
    """
    return LogCreateSchema(
        tenant="test_tenant",
        log={"event": "test_event"},
        metadata={"trace": "test_trace"},
        level="INFO",
        tag="test_tag",
    )


@pytest.fixture
def repo() -> MongoLogRepository:
    return MongoLogRepository()


@pytest_asyncio.fixture
async def test_log(test_log_schema: LogCreateSchema, repo: MongoLogRepository) -> Log:
    """
    A fixture to create a sample log for testing.
    """

    log = Log(**test_log_schema.model_dump())
    await repo.insert(log)

    return log


@pytest_asyncio.fixture
async def test_create_log_list(
    test_log_schema: LogCreateSchema, repo: MongoLogRepository, rep: int = 10
) -> list[Log]:
    """
    A fixture to create a list of sample logs for testing.
    """
    logs = []
    for i in range(rep):
        log = Log(**test_log_schema.model_dump())
        await repo.insert(log)
        logs.append(log)

    return logs


@pytest_asyncio.fixture
async def grouped_logs(repo: MongoLogRepository) -> list[Log]:
    """
    Fixture to insert sample logs with group paths for group path testing.
    """
    base_path = ["root", "section"]

    logs = [
        Log(
            tenant="test_tenant",
            log={"event": "root log"},
            metadata={},
            tag="group_test",
            level=Level.INFO,
            group_path=base_path,
        ),
        Log(
            tenant="test_tenant",
            log={"event": "child log"},
            metadata={},
            tag="group_test",
            level=Level.INFO,
            group_path=base_path + ["child"],
        ),
        Log(
            tenant="test_tenant",
            log={"event": "deep child log"},
            metadata={},
            tag="group_test",
            level=Level.INFO,
            group_path=base_path + ["child", "deep"],
        ),
    ]

    for log in logs:
        await repo.insert(log)

    return logs


@pytest_asyncio.fixture
async def client():
    """
    To test the API endpoints (controllers), we use this clinet.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="https://testserver") as ac:
        yield ac
