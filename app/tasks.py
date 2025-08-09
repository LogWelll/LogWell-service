from repositories.mongo_repository import MongoLogRepository
from logs.models import Log
from database import init_db
from celery import shared_task
import asyncio
import logging
import traceback
from settings import settings

repo = MongoLogRepository()


@shared_task
def create_log_task(log_data: dict):
    try:
        asyncio.run(_save_log(log_data))
    except Exception as e:
        logging.error(f"Error in create_log_task: {e}")
        logging.error(traceback.format_exc())


async def _save_log(log_data: dict):
    await init_db(db_address=settings.DB_ADDRESS, db_name=settings.DB_NAME)
    log = Log(**log_data)

    logging.info(await repo.insert(log))
    logging.info(f"Log added: {log.model_dump()}")
