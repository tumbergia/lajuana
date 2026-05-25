from datetime import UTC, datetime

from beanie import PydanticObjectId

from app.common.collections import Collections
from app.documents.base import AuditDocument


class LiabilityReleaseDocument(AuditDocument):
    participant_id: PydanticObjectId
    reservation_id: PydanticObjectId
    participant_name: str
    pdf_base64: str
    accepted_at: datetime

    class Settings:
        name = Collections.LIABILITY_RELEASES
