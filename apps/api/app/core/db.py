import logging
import re

import dns.resolver
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
    ConfigurationAuditDocument,
    ConversationSessionDocument,
    ConversationTurnDocument,
    EquineDocument,
    EquineEventDocument,
    ExperienceDocument,
    FileUploadDocument,
    HumanReviewRequestDocument,
    InAppNotificationDocument,
    NotificationOutboxDocument,
    NotificationTemplateDocument,
    ParticipantDocument,
    ParticipantFormLinkDocument,
    PaymentProofDocument,
    PingDocument,
    PolicyDocument,
    ProviderDocument,
    ReservationAuditLogDocument,
    ReservationDocument,
    ReservationProviderDocument,
    SaddleDocument,
    ServiceLogDocument,
    SyncChangeDocument,
    SyncOperationReceiptDocument,
    ToolCallLogDocument,
    UserDocument,
)

logger = logging.getLogger(__name__)

LEGACY_NOTIFICATION_TEMPLATE_INDEX_KEYS = [("template_key", 1)]
NOTIFICATION_TEMPLATE_COMPOUND_INDEX_KEYS = [
    ("template_key", 1),
    ("channel", 1),
]


def _resolve_srv_uri(uri: str) -> str:
    """Convert mongodb+srv:// URI to direct mongodb:// URI using public DNS."""
    if not uri.startswith("mongodb+srv://"):
        return uri

    # Parse the SRV URI
    m = re.match(r"mongodb\+srv://(.+?@)?([^/]+?)(?:/(.*))?$", uri)
    if not m:
        logger.warning("[db] Could not parse SRV URI, using as-is")
        return uri

    creds = m.group(1) or ""
    hostname = m.group(2)
    db_and_params = m.group(3) or ""

    # Strip port from hostname if present (shouldn't be for SRV)
    hostname = hostname.split(":")[0]

    # Resolve SRV with public DNS
    resolver = dns.resolver.Resolver(configure=False)
    resolver.nameservers = ["8.8.8.8", "8.8.4.4"]

    try:
        srv_answers = resolver.resolve(f"_mongodb._tcp.{hostname}", "SRV")
        hosts = sorted((str(a.target).rstrip("."), a.port) for a in srv_answers)
        host_list = ",".join(f"{h}:{p}" for h, p in hosts)
    except Exception as e:
        logger.warning("[db] SRV resolution failed (%s), using hostname as-is", e)
        return uri.replace("mongodb+srv://", "mongodb://", 1)

    # Resolve TXT for auth options
    try:
        txt_answers = resolver.resolve(hostname, "TXT")
        txt_parts = []
        for txt in txt_answers:
            for part in txt.strings:
                txt_parts.append(part.decode() if isinstance(part, bytes) else part)
        txt_options = "&".join(txt_parts)
    except Exception:
        txt_options = ""

    # Build direct URI
    direct_uri = f"mongodb://{creds}{host_list}/{db_and_params}"
    if txt_options:
        separator = "&" if "?" in db_and_params else "?"
        direct_uri += f"{separator}{txt_options}"
    if "ssl=" not in direct_uri:
        direct_uri += "&ssl=true" if "?" in direct_uri else "?ssl=true"

    logger.info("[db] Converted SRV URI to direct URI")
    return direct_uri


class Database:
    client: AsyncMongoClient | None = None


db = Database()


async def preflight_notification_template_natural_key(collection) -> tuple[list[str], int]:
    dropped_indexes: list[str] = []

    indexes = await collection.list_indexes()

    async for index in indexes:
        key = list(index.get("key", {}).items())
        if key == LEGACY_NOTIFICATION_TEMPLATE_INDEX_KEYS and index.get("unique"):
            dropped_indexes.append(index["name"])

    for index_name in dropped_indexes:
        await collection.drop_index(index_name)

    removed_documents = 0
    duplicate_groups = await collection.aggregate(
        [
            {
                "$match": {
                    "template_key": {"$exists": True},
                    "channel": {"$exists": True},
                }
            },
            {
                "$sort": {
                    "template_key": 1,
                    "channel": 1,
                    "updated_at": -1,
                    "created_at": -1,
                    "_id": 1,
                }
            },
            {
                "$group": {
                    "_id": {
                        "template_key": "$template_key",
                        "channel": "$channel",
                    },
                    "ids": {"$push": "$_id"},
                    "count": {"$sum": 1},
                }
            },
            {"$match": {"count": {"$gt": 1}}},
        ]
    )

    async for duplicate_group in duplicate_groups:
        ids = duplicate_group.get("ids", [])
        duplicate_ids = ids[1:]
        if not duplicate_ids:
            continue

        result = await collection.delete_many({"_id": {"$in": duplicate_ids}})
        removed_documents += result.deleted_count

        logger.warning(
            "[db] Removed %d duplicate notification templates for %s/%s; kept %s",
            result.deleted_count,
            duplicate_group["_id"].get("template_key"),
            duplicate_group["_id"].get("channel"),
            ids[0],
        )

    return dropped_indexes, removed_documents


async def init_db() -> None:
    if settings.app_skip_db_init:
        return

    mongo_uri = _resolve_srv_uri(settings.mongodb_uri)
    db.client = AsyncMongoClient(mongo_uri)
    database = db.client[settings.mongodb_db_name]

    # Backfill provider slugs before Beanie creates the unique index.
    try:
        from app.migrations.versions.migrate_provider_fields import backfill_provider_slugs

        slug_count = await backfill_provider_slugs(database[Collections.PROVIDERS])
        if slug_count:
            logger.info("[db] Backfilled slug on %d legacy providers", slug_count)
    except PyMongoError:
        logger.warning("[db] Provider slug backfill failed — continuing", exc_info=True)

    # Staff→guide migration handled by 001_staff_to_guide in app.migrations

    dropped_indexes, removed_duplicates = await preflight_notification_template_natural_key(
        database[Collections.NOTIFICATION_TEMPLATES]
    )
    if dropped_indexes or removed_duplicates:
        logger.info(
            (
                "[db] Notification template preflight dropped %d legacy indexes "
                "and removed %d duplicates"
            ),
            len(dropped_indexes),
            removed_duplicates,
        )

    from beanie import init_beanie

    document_models = [
        PingDocument,
        UserDocument,
        ExperienceDocument,
        ReservationDocument,
        ParticipantDocument,
        ParticipantFormLinkDocument,
        PaymentProofDocument,
        AppConfigDocument,
        EquineDocument,
        SaddleDocument,
        AssignmentDocument,
        ServiceLogDocument,
        EquineEventDocument,
        ProviderDocument,
        ReservationProviderDocument,
        PolicyDocument,
        SyncChangeDocument,
        SyncOperationReceiptDocument,
        ConversationSessionDocument,
        ConversationTurnDocument,
        ConfigurationAuditDocument,
        ReservationAuditLogDocument,
        ToolCallLogDocument,
        WhatsAppInboundEventDocument,
        MessageBufferDocument,
        OutboundMessageDocument,
        HumanReviewRequestDocument,
        NotificationTemplateDocument,
        NotificationOutboxDocument,
        InAppNotificationDocument,
        FileUploadDocument,
    ]

    await init_beanie(database=database, document_models=document_models)

    try:
        await database["whatsapp_inbound_events"].create_index(
            "wa_message_id", unique=True, name="uq_wa_message_id"
        )
    except PyMongoError:
        logger.warning("[db] Index uq_wa_message_id may already exist — continuing")


async def close_db() -> None:
    if db.client is not None:
        await db.client.close()
        db.client = None
