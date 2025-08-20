# LogWell

<p align="center">
  <img src="app/static/logo.jpeg" alt="LogWell Logo" width="300">
</p>

## Introduction
LogWell is a self-hostable logging microservice, tailored to store the logs produced by a set of microservices, working together.

## Features
1. Log creation functionality, supporting both blocking and non-blocking log registeration
2. Nested log creation, through group pathing
3. Log query functionality, through various parameters:
    -   Unique identifier
    -   Level
    -   Tag
    -   Group pathing
4. Easy authentication, through API keys
5. [Custom client library]() with logging-compatible handler

## Log object
A log object is basically an instance of `[pydantic.BaseModel]`(), consisting the following structure:

```Python
tenant: str | None = None                                       # an identifier to the creator (service) of the log
log: dict | str = Field(default_factory=dict)                   # the actual log to save
execution_path: dict | None = None                              # the execution path, leading to where the log is introduced
metadata: dict = Field(default_factory=dict)                    # additional metadata to stroe
tag: str | None = None                                          # a custom tag to query a log or a family of logs
level: Level = Level.NOTSET                                     # the level to produce the log; available options are: ["INFO", "TRACE","DEBUG", "WARNING", "ERROR", "CRITICAL", "FATAL", "NOTSET",]
group_path: List[str] | None = None                             # a group path, to register nnested logs
uid: str = Field(default_factory=lambda: str(uuid4()))          # an unique identifier field, produced by the system, automatically
created_at: datetime = Field(default_factory=datetime.now)      # an automatically produced created_at field
```

## Infrastructure
LogWell, at least, requires a database (natievely supportingh MongoDB) to store and retrieve logs and a FastAPI application to create and read logs; this basic configuration provides fire-and-forget log creation (upon calling the log creation endpoints, the HTTP communication channel is closed as soon as possible and the actual DB-related insertion operation is done in a separate thread to avoid blocking the application) functionality through FastAPI builtin BackgroundTasks. For high-throghput applications that FastAPI BackgroundTasks may perform poorly, by adding a celery worker and a message queue (natievely supporting RabbitMQ), a more robust option would be available to create logs in a non-blocking manner.


## Environemnt variables
Below, is an example of the `.env` file you are supposed to provide for this application to work:

```env
DB_ADDRESS=mongodb://mongo:27017                    # the address to the database.
DB_NAME=logs_db                                     # the name of the database.
NON_BLOCKING_AVAILABLE=true                         # either if you want to use non-blocking log posting feature or not; it set true, you must also give values for MQ_URL and QUEUE_NAME.
MQ_URL=amqp://admin:admin123@rabbitmq/              # the address towards the message queue that stores logs temporiraly.
QUEUE_NAME=log_queue                                # the name of the message queue that hosts logs, temporiraly.
ALLOWED_KEYS=["key1"]                               # list of the keys who are allowed to interact with hte system; these keys are strings used as API keys.
```

Fields are self-descriptory and no further explanation is required.
Attention: Keep in mind that if you want the advanced non-blocking functionality, you must set `NON_BLOCKING_AVAILABLE` field here to `true` and provide the `MQ_URL` and `QUEUE_NAME` too; provoking the `base_url/logs/non-blocking/` endpoint without these fields not passed or additional services (worker and the message queue) not being available, results in a 503 error.

## Deployment
I strongly encourage deploying LogWell using `docker compose`, as it is a multi-service application. You can use the `docker-compose.yaml` file in the root directory of this project, with the following command:

```bash
docker compose up --build -d
```

Attention: Do not forget modifying the development stage suitable placeholders, for the production stage.

## Usage

### Log creation

Logs can be created in different styles:

#### 1. Direct HTTP calls

You can directly call the log creation endpoints to register your log; below is a simple example:

```python
import httpx

response = httpx.post(
    url="http://localhost:8000/logs/",
    json={
        "tenant": "tenant1",
        "log": "hello world",
        "metadata": {"client_ip": "127.0.0.1"},
        "level": "INFO",
        "tag": "tag1",
    },
    headers={"x-api-key": "key1"},
)

response.raise_for_status()

print(response.json())

OUTPUT>>>
{'message': 'Log added successfully', 'data': {'tenant': 'tenant1', 'log': 'hello world', 'execution_path': None, 'metadata': {'client_ip': '127.0.0.1'}, 'tag': 'tag1', 'level': 'INFO', 'group_path': None, 'uid': '754e109f-ff9b-4f10-a933-87a8888021b7', 'created_at': '2025-08-20T07:46:37.505030'}}
```

#### 2. Using the LogWell client, directly

If you prefer using a custom client, instead of plain HTTP calls every now and then, use the [LogWell clinet]() as below:

```python

from log_writing_client.src.client import SyncLogClient
from log_writing_client.src.schema import LogCreateSchema

client = SyncLogClient(
    base_url="http://localhost:8000/", api_key="key1", tenant="tenant1"
)
response = client.create_log(
    log=LogCreateSchema(
        log="hello world",
        metadata={"client_ip": "127.0.0.1"},
        level="INFO",
        tag="tag1",
    )
)

# Alternatively, you can pass plain dicts
# response = client.create_log(
#     log={
#         "log": "hello world",
#         "metadata": {"client_ip": "127.0.0.1"},
#         "level": "INFO",
#         "tag": "tag1",
#     }
# )

response.raise_for_status()

print(response.json())

OUTPUT>>>
{'message': 'Log added successfully', 'data': {'tenant': 'tenant1', 'log': 'hello world', 'execution_path': None, 'metadata': {'client_ip': '127.0.0.1'}, 'tag': 'tag1', 'level': 'INFO', 'group_path': None, 'uid': '660aa1a3-a938-4d58-bafe-ed12b14e53f9', 'created_at': '2025-08-20T08:01:42.831983'}}s
```

#### 3. Adding the LogWell handler to logging
LogWell offers logging compatible handler to facilitate the logging operation; use it as below:

```python
import logging
from log_writing_client.src.handler import LogServiceHandler

logger = logging.getLogger("my-app")
logger.setLevel(logging.DEBUG)

handler = LogServiceHandler(
    base_url="http://localhost:8000",
    api_key="key1",
    tenant="tenant1",
)
logger.addHandler(handler)


logger.info(
    "Hello world!",
    extra={
        "metadata": {"client_ip": "127.0.0.1"},
        "level": "INFO",
        "tag": "tag1",
    },
)
```