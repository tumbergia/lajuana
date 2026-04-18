from pymongo import AsyncMongoClient

from app.core.config import settings
from app.documents.ping_document import PingDocument


class Database:
    client: AsyncMongoClient | None = None


db = Database()


async def init_db() -> None:
    db.client = AsyncMongoClient(settings.mongodb_uri)
    database = db.client[settings.mongodb_db_name]

    from beanie import init_beanie

    await init_beanie(
        database=database,
        document_models=[PingDocument],
    )


async def close_db() -> None:
    if db.client is not None:
        await db.client.close()
        db.client = None
