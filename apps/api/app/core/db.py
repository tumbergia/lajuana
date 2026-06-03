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

    # Staff→guide migration handled by 001_staff_to_guide in app.migrations

    from beanie import init_beanie

    document_models = [
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
    ]

    await init_beanie(database=database, document_models=document_models)

    try:
        await database["whatsapp_inbound_events"].create_index(
            "wa_message_id", unique=True, name="uq_wa_message_id"
        )
    except PyMongoError:
        logger.warning(
            "[db] Index uq_wa_message_id may already exist — continuing"
        )

    # Ensure indexes declared in Beanie document Settings.indexes exist.
    # init_beanie does NOT guarantee indexes are created if they already
    # exist in a different state or were created before the Setting was added.
    for model in document_models:
        try:
            indexes = getattr(model.Settings, "indexes", None)
            if indexes:
                await model.get_motor_collection().create_indexes(indexes)
        except Exception:
            logger.exception("[db] Failed to ensure indexes for %s", model.__name__)


async def close_db() -> None:
    if db.client is not None:
        await db.client.close()
        db.client = None
