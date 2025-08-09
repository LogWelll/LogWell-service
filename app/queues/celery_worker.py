from settings import settings
from celery import Celery


celery_app = Celery(
    broker=settings.MQ_URL,
)

celery_app.autodiscover_tasks(["tasks"])
