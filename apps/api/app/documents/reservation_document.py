from datetime import date, datetime
from decimal import Decimal

from beanie import Indexed, PydanticObjectId
from pydantic import EmailStr

from app.common.collections import Collections
from app.common.enums import Channel, PaymentStatus, ReservationStatus
from app.documents.base import AuditDocument


class ReservationDocument(AuditDocument):
    code: Indexed(str, unique=True)  # type: ignore[valid-type]
    experience_id: PydanticObjectId
    schedule_id: PydanticObjectId | None = None
    channel: Channel
    status: ReservationStatus = ReservationStatus.CONTACT
    holder_name: str | None = None
    holder_email: EmailStr | None = None
    holder_phone: str | None = None
    requested_date: date | None = None
    participant_count: int
    quoted_total_amount: Decimal | None = None
    currency: str = "COP"
    payment_status: PaymentStatus = PaymentStatus.PENDING
    payment_proof_ids: list[PydanticObjectId] = []
    participant_ids: list[PydanticObjectId] = []
    provider_ids: list[PydanticObjectId] = []
    policy_ids: list[PydanticObjectId] = []
    confirmed_at: datetime | None = None
    cancelled_at: datetime | None = None
    completed_at: datetime | None = None
    created_by: PydanticObjectId | None = None
    updated_by: PydanticObjectId | None = None

    class Settings:
        name = Collections.RESERVATIONS
