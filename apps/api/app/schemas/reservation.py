from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, EmailStr, Field

from app.common.enums import Channel, PaymentStatus, ReservationStatus


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


class ReservationCancelSchema(BaseModel):
    reason: str | None = None


class ReservationStatusTransitionSchema(BaseModel):
    target_status: ReservationStatus


class ReservationResponseSchema(BaseModel):
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
    confirmed_at: datetime | None
    cancelled_at: datetime | None
    completed_at: datetime | None
    created_at: datetime


class ReservationListItemSchema(BaseModel):
    id: str
    code: str
    status: ReservationStatus
    participant_count: int
    payment_status: PaymentStatus
    created_at: datetime
