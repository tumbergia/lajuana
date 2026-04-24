from datetime import UTC, datetime

from pymongo import AsyncMongoClient

from app.common.collections import Collections
from app.core.config import settings

MUTABLE_COLLECTIONS = (
    Collections.USERS,
    Collections.EXPERIENCES,
    Collections.SCHEDULES,
    Collections.RESERVATIONS,
    Collections.PARTICIPANTS,
    Collections.PAYMENT_PROOFS,
    Collections.EQUINES,
    Collections.SADDLES,
    Collections.ASSIGNMENTS,
    Collections.SERVICE_LOGS,
    Collections.PROVIDERS,
    Collections.POLICIES,
)


async def run_backfill() -> None:
    client = AsyncMongoClient(settings.mongodb_uri)
    database = client[settings.mongodb_db_name]
    now = datetime.now(UTC)
    for collection_name in MUTABLE_COLLECTIONS:
        collection = database[collection_name]
        await collection.update_many(
            {"version": {"$exists": False}},
            {"$set": {"version": 1}},
        )
        await collection.update_many(
            {"deleted_at": {"$exists": False}},
            {"$set": {"deleted_at": None}},
        )
        await collection.update_many(
            {"created_at": {"$exists": False}},
            {"$set": {"created_at": now}},
        )
        await collection.update_many(
            {"updated_at": {"$exists": False}},
            {"$set": {"updated_at": now}},
        )
    await client.close()
