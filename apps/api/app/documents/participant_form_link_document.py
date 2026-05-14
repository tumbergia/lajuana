from datetime import datetime

from beanie import PydanticObjectId

from app.common.collections import Collections
from app.common.enums import ParticipantFormLinkStatus
from app.documents.base import AuditDocument


class ParticipantFormLinkDocument(AuditDocument):
    reservation_id: PydanticObjectId
    token_hash: str
    expires_at: datetime
    max_participants: int
    used_count: int = 0
    status: ParticipantFormLinkStatus = ParticipantFormLinkStatus.ACTIVE
    created_by: PydanticObjectId | None = None
    channel: str = "whatsapp"
    sent_to_phone: str | None = None
    revoked_at: datetime | None = None
    completed_at: datetime | None = None

    class Settings:
        name = Collections.PARTICIPANT_FORM_LINKS
