from pymongo import AsyncMongoClient

from app.common.collections import Collections
from app.core.config import settings
from app.documents import (
    AppConfigDocument,
    AssignmentDocument,
    EquineDocument,
    ExperienceDocument,
    ParticipantDocument,
    PaymentProofDocument,
    PingDocument,
    PolicyDocument,
    ProviderDocument,
    ReservationDocument,
    SaddleDocument,
    ScheduleDocument,
    ServiceLogDocument,
    UserDocument,
)


class Database:
    client: AsyncMongoClient | None = None


db = Database()


async def init_db() -> None:
    if settings.app_skip_db_init:
        return

    db.client = AsyncMongoClient(settings.mongodb_uri)
    database = db.client[settings.mongodb_db_name]
    await database[Collections.USERS].update_many(
        {"role": "staff"},
        {"$set": {"role": "guide"}},
    )

    from beanie import init_beanie

    await init_beanie(
        database=database,
        document_models=[
            PingDocument,
            UserDocument,
            ExperienceDocument,
            ScheduleDocument,
            ReservationDocument,
            ParticipantDocument,
            PaymentProofDocument,
            AppConfigDocument,
            EquineDocument,
            SaddleDocument,
            AssignmentDocument,
            ServiceLogDocument,
            ProviderDocument,
            PolicyDocument,
        ],
    )


async def close_db() -> None:
    if db.client is not None:
        await db.client.close()
        db.client = None
