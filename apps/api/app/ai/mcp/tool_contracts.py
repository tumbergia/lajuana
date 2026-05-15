from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ToolBlockingReason(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str
    message: str
    details: dict = Field(default_factory=dict)


class ExperienceSummaryItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    experience_id: str
    name: str
    slug: str | None = None
    short_description: str | None = None
    duration: str | None = None
    difficulty: str | None = None
    level: str | None = None
    starting_price: int | None = None
    currency: str = "COP"
    tags: list[str] = Field(default_factory=list)


class ListExperiencesInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    is_active: bool = True
    limit: int = Field(default=20, ge=1, le=50)


class ListExperiencesOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    trace_id: str
    tool_name: Literal["list_experiences"] = "list_experiences"
    experiences: list[ExperienceSummaryItem]
    total: int


class GetExperienceDetailInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    experience_id: str | None = None
    experience_query: str | None = None

    @model_validator(mode="after")
    def require_identifier(self):
        if not self.experience_id and not self.experience_query:
            raise ValueError("experience_id_or_experience_query_required")
        return self


class ExperienceDetailOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    trace_id: str
    tool_name: Literal["get_experience_detail"] = "get_experience_detail"
    found: bool
    experience_id: str | None = None
    name: str | None = None
    slug: str | None = None
    description: str | None = None
    short_description: str | None = None
    duration: str | None = None
    difficulty: str | None = None
    level: str | None = None
    includes: list[str] = Field(default_factory=list)
    restrictions: list[str] = Field(default_factory=list)
    starting_price: int | None = None
    currency: str = "COP"
    blocking_reasons: list[ToolBlockingReason] = Field(default_factory=list)


class PublicBusinessRulesInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    include_reservation_rules: bool = True
    include_behavior_rules: bool = True


class PublicBusinessRulesOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    trace_id: str
    tool_name: Literal["get_public_business_rules"] = "get_public_business_rules"
    family_focus: str
    alcohol_policy: str
    behavior_policy: str
    reservation_notice_days: int | None = None
    general_restrictions: list[str] = Field(default_factory=list)
    disclaimer: str


class CheckExperienceAvailabilityInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    experience_id: str | None = None
    experience_query: str | None = None
    requested_date: date
    participant_count: int = Field(ge=1, le=30)

    @model_validator(mode="after")
    def require_experience(self):
        if not self.experience_id and not self.experience_query:
            raise ValueError("experience_id_or_experience_query_required")
        return self


class CheckExperienceAvailabilityOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

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


class AvailableScheduleItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schedule_id: str
    experience_id: str
    experience_name: str
    scheduled_date: date
    start_time: str | None = None
    capacity_total: int
    capacity_available: int
    status: str


class ListAvailableSchedulesInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    experience_id: str | None = None
    experience_query: str | None = None
    date_from: date | None = None
    date_to: date | None = None
    participant_count: int | None = Field(default=None, ge=1, le=30)
    limit: int = Field(default=10, ge=1, le=30)


class ListAvailableSchedulesOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    trace_id: str
    tool_name: Literal["list_available_schedules"] = "list_available_schedules"
    date_from: date
    date_to: date
    participant_count: int | None = None
    schedules: list[AvailableScheduleItem]
    total: int
    blocking_reasons: list[ToolBlockingReason] = Field(default_factory=list)


class QuotePricingTier(BaseModel):
    model_config = ConfigDict(extra="forbid")

    min_participants: int
    max_participants: int
    price_per_person: int


class QuoteExperienceInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    experience_id: str | None = None
    experience_query: str | None = None
    requested_date: date | None = None
    participant_count: int = Field(ge=1, le=30)
    notes: str | None = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def require_experience(self):
        if not self.experience_id and not self.experience_query:
            raise ValueError("experience_id_or_experience_query_required")
        return self


class QuoteExperienceOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    quoted: bool
    trace_id: str
    tool_name: Literal["quote_experience"] = "quote_experience"
    experience_id: str | None = None
    experience_name: str | None = None
    requested_date: date | None = None
    participant_count: int
    unit_price: int | None = None
    subtotal: int | None = None
    currency: str = "COP"
    pricing_tier: QuotePricingTier | None = None
    notes: str | None = None
    quote_snapshot: dict | None = None
    response: str | None = None
    blocking_reasons: list[ToolBlockingReason] = Field(default_factory=list)


class SuggestAlternativeDatesInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    experience_id: str | None = None
    experience_query: str | None = None
    requested_date: date
    participant_count: int = Field(ge=1, le=30)
    search_days_before: int = Field(default=15, ge=0, le=60)
    search_days_after: int = Field(default=30, ge=1, le=90)
    limit: int = Field(default=5, ge=1, le=10)
    exclude_dates: list[date] = Field(default_factory=list)

    @model_validator(mode="after")
    def require_experience(self):
        if not self.experience_id and not self.experience_query:
            raise ValueError("experience_id_or_experience_query_required")
        return self


class SuggestAlternativeDatesOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    trace_id: str
    tool_name: Literal["suggest_alternative_dates"] = "suggest_alternative_dates"
    requested_date: date
    participant_count: int
    alternatives: list[AvailableScheduleItem]
    total: int
    blocking_reasons: list[ToolBlockingReason] = Field(default_factory=list)


class RequestHumanReviewInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    conversation_id: str
    reason_code: Literal[
        "customer_requests_human",
        "unclear_experience",
        "special_condition",
        "availability_conflict",
        "payment_or_confirmation",
        "safety_or_incident",
        "other",
    ]
    summary: str = Field(min_length=10, max_length=1000)
    priority: Literal["low", "normal", "high", "urgent"] = "normal"


class RequestHumanReviewOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    trace_id: str
    tool_name: Literal["request_human_review"] = "request_human_review"
    requested: bool
    review_id: str
    status: Literal["open", "already_open"]
    message: str


class CreateReservationDraftInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    experience_id: str
    schedule_id: str
    participant_count: int
    holder_phone: str
    holder_name: str | None = None
    requested_date: date
    quote_snapshot: dict
    conversation_id: str | None = None


class CreateReservationDraftOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    created: bool
    code: str | None = None
    status: str = ""
    expire_at: datetime | None = None
    message: str = ""
    response: str | None = None
    blocking_reasons: list[ToolBlockingReason] = []


class GetReservationPublicSummaryOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    found: bool
    code: str | None = None
    status: str = ""
    expire_at: datetime | None = None
    participant_count: int | None = None
    blocking_reasons: list[ToolBlockingReason] = []


class GetReservationPublicSummaryInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str
    holder_phone: str


class GetReservationStatusByPhoneInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    holder_phone: str


class GetReservationStatusByPhoneOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    found: bool
    code: str | None = None
    status: str = ""
    expire_at: datetime | None = None
    participant_count: int | None = None
    blocking_reasons: list[ToolBlockingReason] = []


class AttachPaymentProofToReservationInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reservation_id: str | None = None
    public_reservation_code: str | None = None
    from_phone: str
    whatsapp_message_id: str
    media_id: str
    media_mime_type: str
    filename: str | None = None
    caption: str | None = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def require_reservation_identifier(self):
        if not self.reservation_id and not self.public_reservation_code:
            raise ValueError("reservation_id_or_public_reservation_code_required")
        return self


class AttachPaymentProofToReservationOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    attached: bool
    idempotent: bool = False
    trace_id: str
    tool_name: Literal["attach_payment_proof_to_reservation"] = "attach_payment_proof_to_reservation"
    reservation_code: str | None = None
    reservation_status: Literal["pending_payment", "payment_received", "unknown"] = "unknown"
    proof_status: Literal["received", "under_review", "duplicate", "rejected"] = "received"
    message: str
    response: str
    blocking_reasons: list[ToolBlockingReason] = Field(default_factory=list)
