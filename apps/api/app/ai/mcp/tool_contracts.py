from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


class ToolBlockingReason(BaseModel):
    code: str
    message: str


class CheckExperienceAvailabilityInput(BaseModel):
    experience_id: str | None = Field(
        default=None,
        description="ID de la experiencia. Puede ser null si se usa experience_query.",
    )
    experience_query: str | None = Field(
        default=None,
        description="Texto libre para buscar experiencia cuando no se conoce el ID.",
    )
    requested_date: date
    participant_count: int = Field(ge=1, le=30)


class CheckExperienceAvailabilityOutput(BaseModel):
    available: bool
    trace_id: str
    tool_name: Literal["check_experience_availability"] = "check_experience_availability"
    experience_id: str | None = None
    experience_name: str | None = None
    schedule_id: str | None = None
    requested_date: date
    participant_count: int
    capacity_total: int | None = None
    capacity_available: int | None = None
    min_notice_days: int | None = None
    blocking_reasons: list[ToolBlockingReason] = Field(default_factory=list)


class QuotePricingTier(BaseModel):
    min_participants: int
    max_participants: int
    price_per_person: int


class QuoteExperienceInput(BaseModel):
    experience_id: str | None = Field(
        default=None,
        description="ID de la experiencia. Puede ser null si se usa experience_query.",
    )
    experience_query: str | None = Field(
        default=None,
        description="Texto libre para buscar experiencia cuando no se conoce el ID.",
    )
    participants_count: int = Field(ge=1, le=30)
    schedule_id: str | None = Field(
        default=None,
        description="ID opcional del schedule para validar coherencia.",
    )
    special_conditions: dict[str, str] = Field(default_factory=dict)


class QuoteExperienceOutput(BaseModel):
    quoted: bool
    trace_id: str
    tool_name: Literal["quote_experience"] = "quote_experience"
    experience_id: str | None = None
    experience_name: str | None = None
    participants_count: int
    unit_price: int | None = None
    subtotal: int | None = None
    currency: str = "COP"
    pricing_tier: QuotePricingTier | None = None
    requested_date: str | None = None
    notes: str | None = None
    next_step: str | None = "check_availability_or_create_reservation_draft"
    disclaimer: str | None = (
        "Esta cotizacion no confirma la reserva. La reserva se confirma solo despues "
        "de validar disponibilidad, pago y comprobante."
    )
    blocking_reasons: list[ToolBlockingReason] = Field(default_factory=list)
