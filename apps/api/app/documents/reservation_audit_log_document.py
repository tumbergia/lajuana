from beanie import PydanticObjectId

from app.common.collections import Collections
from app.common.enums import UserRole
from app.documents.audit_metadata_models import AuditMetadata
from app.documents.base import AuditDocument


class ReservationAuditLogDocument(AuditDocument):
    reservation_id: PydanticObjectId
    payment_proof_id: PydanticObjectId | None = None
    actor_user_id: PydanticObjectId | None = None
    actor_role: UserRole | None = None
    action: str
    previous_status: str
    new_status: str
    reason: str | None = None
    source: str = "mobile_app"
    metadata: AuditMetadata | None = None

    class Settings:
        name = Collections.RESERVATION_AUDIT_LOGS
