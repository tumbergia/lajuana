from datetime import datetime

from beanie import PydanticObjectId
from pydantic import Field

from app.common.collections import Collections
from app.common.enums import PaymentStatus
from app.documents.base import AuditDocument, utc_now


class PaymentProofDocument(AuditDocument):
    reservation_id: PydanticObjectId
    storage_key: str
    filename: str
    content_type: str
    size_bytes: int
    sha256: str
    uploaded_by: PydanticObjectId | None = None
    uploaded_at: datetime = Field(default_factory=utc_now)
    status: PaymentStatus = PaymentStatus.RECEIVED

    class Settings:
        name = Collections.PAYMENT_PROOFS
