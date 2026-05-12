from pymongo import AsyncMongoClient
from pymongo.errors import PyMongoError

from app.common.collections import Collections
from app.core.config import settings
from app.documents import (
    AppConfigDocument,
    AssignmentDocument,
    ConversationTurnDocument,
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
    ToolCallLogDocument,
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

    try:
        await database[Collections.USERS].update_many(
            {"role": "staff"},
            {"$set": {"role": "guide"}},
        )
    except PyMongoError:
        # Keep the API bootable even if the migration cannot run right now.
        # The request path still depends on Mongo, but startup should not fail on a best-effort fixup.
        pass

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
            ConversationTurnDocument,
            ToolCallLogDocument,
        ],
    )


async def close_db() -> None:
    if db.client is not None:
        await db.client.close()
        db.client = None
