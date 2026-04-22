from datetime import datetime

from beanie import PydanticObjectId

from app.common.collections import Collections
from app.documents.base import AuditDocument


class PolicyDocument(AuditDocument):
    reservation_id: PydanticObjectId
    provider_id: PydanticObjectId | None = None
    policy_number: str
    issued_at: datetime | None = None
    expires_at: datetime | None = None
    notes: str | None = None

    class Settings:
        name = Collections.POLICIES
