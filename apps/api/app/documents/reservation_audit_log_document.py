from beanie import PydanticObjectId
from pydantic import field_validator

from app.common.collections import Collections
from app.common.enums import UserRole
from app.documents.audit_metadata_models import AuditMetadata, parse_audit_metadata
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

    @field_validator("metadata", mode="before")
    @classmethod
    def _normalize_metadata(cls, value: object) -> object:
        return parse_audit_metadata(value)

    class Settings:
        name = Collections.RESERVATION_AUDIT_LOGS
