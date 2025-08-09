from .base import AbstractLogQueue
from .rabbitmq_queue import RabbitMQLogQueue

_log_queue_backend: AbstractLogQueue | None = None


def register_log_queue(backend: AbstractLogQueue):
    global _log_queue_backend
    _log_queue_backend = backend


def get_log_queue() -> AbstractLogQueue:
    if _log_queue_backend is None:
        # Default to RabbitMQ
        register_log_queue(RabbitMQLogQueue())
    return _log_queue_backend
