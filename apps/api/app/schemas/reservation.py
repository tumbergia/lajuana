from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, EmailStr, Field

from app.common.enums import Channel, ParticipantFormStatus, PaymentStatus, ReservationStatus
from app.schemas.common import AuditMetadataSchema
from app.schemas.participant import ParticipantResponseSchema
from app.schemas.payment_proof import PaymentProofResponseSchema


class ReservationCreateSchema(BaseModel):
    experience_id: str
    schedule_id: str | None = None
    requested_date: date | None = None
    participant_count: int = Field(gt=0)
    channel: Channel
    holder_name: str | None = None
    holder_email: EmailStr | None = None
    holder_phone: str | None = None


class ReservationUpdateSchema(BaseModel):
    participant_count: int | None = Field(default=None, gt=0)
    holder_name: str | None = None
    holder_email: EmailStr | None = None
    holder_phone: str | None = None
    quoted_total_amount: Decimal | None = None


class ReservationConfirmSchema(BaseModel):
    notes: str | None = None


class ReservationApprovePaymentSchema(BaseModel):
    note: str | None = None


class ReservationCancelSchema(BaseModel):
    reason: str | None = None


class ReservationSelfCancelSchema(BaseModel):
    reservation_code: str
    holder_phone: str


class ReservationStatusTransitionSchema(BaseModel):
    target_status: ReservationStatus


class ReservationAvailabilityResponseSchema(BaseModel):
    date: date
    available: bool
    blocking_reservation_id: str | None = None
    reason: str | None = None


class ReservationResponseSchema(AuditMetadataSchema):
    id: str
    code: str
    experience_id: str
    schedule_id: str | None
    channel: Channel
    status: ReservationStatus
    participant_count: int
    payment_status: PaymentStatus
    holder_name: str | None
    holder_email: EmailStr | None
    holder_phone: str | None
    requested_date: date | None
    quoted_total_amount: Decimal | None
    currency: str
    expected_participants_count: int | None
    participants_completed_count: int
    participant_form_status: ParticipantFormStatus
    form_url: str | None
    participant_form_sent_at: datetime | None = None
    participant_form_send_count: int = 0
    form_sent: bool = False
    confirmation_message_sent_at: datetime | None = None
    confirmation_message_sent: bool = False
    confirmed_at: datetime | None
    cancelled_at: datetime | None
    completed_at: datetime | None
    participants: list[ParticipantResponseSchema] = []
    payment_proofs: list[PaymentProofResponseSchema] = []
    assignment_status: str | None = None
    assignments_total: int = 0
    assignments_pending: int = 0
    assignment_blocking_reasons: list[str] = []


class ReservationListItemSchema(AuditMetadataSchema):
    id: str
    code: str
    status: ReservationStatus
    participant_count: int
    payment_status: PaymentStatus
    holder_name: str | None = None
    holder_email: str | None = None
    holder_phone: str | None = None
    experience_id: str
    experience_name: str | None = None
    schedule_id: str | None = None
    requested_date: date | None = None
    scheduled_date: str | None = None
    start_time: str | None = None
    expected_participants_count: int | None = None
    participants_completed_count: int = 0
    participant_form_status: ParticipantFormStatus = ParticipantFormStatus.NOT_SENT
    channel: Channel | None = None
    assignment_status: str | None = None
    assignments_total: int = 0
    assignments_pending: int = 0
    assignment_blocking_reasons: list[str] = []
