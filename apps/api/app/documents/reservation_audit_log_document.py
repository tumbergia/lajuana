from beanie import PydanticObjectId

from app.common.collections import Collections
from app.common.enums import UserRole
from app.documents.base import AuditDocument


class ReservationAuditLogDocument(AuditDocument):
    reservation_id: PydanticObjectId
    payment_proof_id: PydanticObjectId | None = None
    actor_user_id: PydanticObjectId | None = None
    actor_role: UserRole
    action: str
    previous_status: str
    new_status: str
    reason: str | None = None
    source: str = "mobile_app"
    metadata: dict = {}

    class Settings:
        name = Collections.RESERVATION_AUDIT_LOGS
