from datetime import date, datetime
from decimal import Decimal

from beanie import Indexed, PydanticObjectId
from pydantic import EmailStr, field_validator
from pymongo import IndexModel

from app.common.collections import Collections
from app.common.enums import Channel, ParticipantFormStatus, PaymentStatus, ReservationStatus
from app.documents.base import AuditDocument

ACTIVE_RESERVATION_STATUSES = [
    ReservationStatus.QUOTED.value,
    ReservationStatus.PENDING_PAYMENT.value,
    ReservationStatus.PAYMENT_RECEIVED.value,
    ReservationStatus.CONFIRMED.value,
]


class ReservationDocument(AuditDocument):
    code: Indexed(str, unique=True)  # type: ignore[valid-type]
    experience_id: PydanticObjectId
    channel: Channel
    status: ReservationStatus = ReservationStatus.CONTACT
    holder_name: str | None = None
    holder_email: EmailStr | None = None
    holder_phone: str | None = None
    requested_date: date | None = None
    blocks_day: bool = False
    availability_lock_key: str | None = None
    participant_count: int
    quoted_total_amount: Decimal | None = None
    currency: str = "COP"
    payment_status: PaymentStatus = PaymentStatus.PENDING
    payment_proof_ids: list[PydanticObjectId] = []
    participant_ids: list[PydanticObjectId] = []
    policy_ids: list[PydanticObjectId] = []
    confirmed_at: datetime | None = None
    cancelled_at: datetime | None = None
    completed_at: datetime | None = None
    expected_participants_count: int | None = None
    participants_completed_count: int = 0
    participant_form_status: ParticipantFormStatus = ParticipantFormStatus.NOT_SENT
    form_url: str | None = None
    participant_form_sent_at: datetime | None = None
    participant_form_sent_by: PydanticObjectId | None = None
    participant_form_send_count: int = 0
    participant_form_last_message_id: str | None = None
    confirmation_message_sent_at: datetime | None = None
    confirmation_message_sent_by: PydanticObjectId | None = None
    quote_snapshot: dict | None = None
    quote_trace_id: str | None = None
    pre_reserved_at: datetime | None = None
    expire_at: datetime | None = None
    created_by: PydanticObjectId | None = None
    updated_by: PydanticObjectId | None = None

    @field_validator("participant_form_status", mode="before")
    @classmethod
    def _migrate_legacy_status(cls, v: object) -> object:
        """Map old enum values (removed in schema migration) to current values."""
        mapping = {
            "active": "sent",
            "full": "complete",
            "expired": "revoked",
        }
        return mapping.get(v, v)  # type: ignore[return-value]

    @field_validator("quoted_total_amount", mode="before")
    @classmethod
    def _parse_decimal128(cls, v: object) -> object:
        """Convert MongoDB Decimal128 to Python Decimal to avoid pydantic parse error."""
        if v is None:
            return None
        if hasattr(v, "to_decimal"):
            return v.to_decimal()
        return v

    class Settings:
        name = Collections.RESERVATIONS
        indexes = [
            IndexModel(
                [("availability_lock_key", 1)],
                unique=True,
                partialFilterExpression={
                    "blocks_day": True,
                    "availability_lock_key": {"$type": "string"},
                },
            )
        ]
