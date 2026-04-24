from pymongo import AsyncMongoClient

from app.common.collections import Collections
from app.core.config import settings


async def run_backfill() -> None:
    client = AsyncMongoClient(settings.mongodb_uri)
    database = client[settings.mongodb_db_name]
    collection = database[Collections.SCHEDULES]
    await collection.update_many(
        {"is_active": {"$exists": False}},
        {"$set": {"is_active": True}},
    )
    await client.close()
