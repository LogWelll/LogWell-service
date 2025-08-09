import logging
from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

from repositories.mongo_repository import MongoLogDocument
from settings import settings



async def init_db(
    db_address: str = settings.DB_ADDRESS, db_name: str = settings.DB_NAME
):
    try:
        client = AsyncIOMotorClient(db_address)
        # db = client[db_name]
        db = client.get_database(db_name)
        await init_beanie(database=db, document_models=[MongoLogDocument])
        logging.info(
            "✅ Database initialized successfully.", "\n", f"db_name: {db_name}"
        )
    except Exception as e:
        logging.exception("❌ Failed to initialize database.")
        raise e
