import logging

from pymongo import AsyncMongoClient
from pymongo.errors import PyMongoError

from app.common.collections import Collections
from app.conversations.documents import (
    MessageBufferDocument,
    OutboundMessageDocument,
    WhatsAppInboundEventDocument,
)
from app.core.config import settings
from app.documents import (
    AppConfigDocument,
    AssignmentDocument,
    ConversationSessionDocument,
    ConversationTurnDocument,
    EquineDocument,
    ExperienceDocument,
    HumanReviewRequestDocument,
    ParticipantDocument,
    ParticipantFormLinkDocument,
    PaymentProofDocument,
    PingDocument,
    PolicyDocument,
    ProviderDocument,
    ReservationAuditLogDocument,
    ReservationDocument,
    SaddleDocument,
    ScheduleDocument,
    ServiceLogDocument,
    ToolCallLogDocument,
    UserDocument,
)

logger = logging.getLogger(__name__)


class Database:
    client: AsyncMongoClient | None = None


db = Database()


async def init_db() -> None:
    if settings.app_skip_db_init:
        return

    db.client = AsyncMongoClient(settings.mongodb_uri)
    database = db.client[settings.mongodb_db_name]

    try:
        result = await database[Collections.USERS].update_many(
            {"role": "staff"},
            {"$set": {"role": "guide"}},
        )
        if result.modified_count:
            logger.info("Migrated %d users from staff→guide", result.modified_count)
    except PyMongoError:
        logger.exception("[db] Failed to migrate staff→guide roles")

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
            ParticipantFormLinkDocument,
            PaymentProofDocument,
            AppConfigDocument,
            EquineDocument,
            SaddleDocument,
            AssignmentDocument,
            ServiceLogDocument,
            ProviderDocument,
            PolicyDocument,
            ConversationSessionDocument,
            ConversationTurnDocument,
            ReservationAuditLogDocument,
            ToolCallLogDocument,
            WhatsAppInboundEventDocument,
            MessageBufferDocument,
            OutboundMessageDocument,
            HumanReviewRequestDocument,
        ],
    )

    try:
        await database["whatsapp_inbound_events"].create_index(
            "wa_message_id", unique=True, name="uq_wa_message_id"
        )
    except PyMongoError:
        logger.warning(
            "[db] Index uq_wa_message_id may already exist — continuing"
        )


async def close_db() -> None:
    if db.client is not None:
        await db.client.close()
        db.client = None
