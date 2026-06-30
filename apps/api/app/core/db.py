import logging
import re
import urllib.parse

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
    ConversationSessionDocument,
    ConversationTurnDocument,
    EquineDocument,
    EquineEventDocument,
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
        hosts = sorted(
            (str(a.target).rstrip("."), a.port) for a in srv_answers
        )
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


async def init_db() -> None:
    if settings.app_skip_db_init:
        return

    mongo_uri = _resolve_srv_uri(settings.mongodb_uri)
    db.client = AsyncMongoClient(mongo_uri)
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
        EquineEventDocument,
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


async def close_db() -> None:
    if db.client is not None:
        await db.client.close()
        db.client = None
