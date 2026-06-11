from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field

from app.common.enums import EquineOperationalStatus
from app.documents.equine_event_document import EquineEventType
from app.schemas.common import AuditMetadataSchema

EquineEventSeverity = Literal["low", "medium", "high", "critical"]
EquineEventSource = Literal["mobile_app", "admin_app", "system", "ai_tool"]


class EquineEventCreateSchema(BaseModel):
    event_type: EquineEventType
    happened_at: datetime
    title: str = Field(min_length=1, max_length=200)
    description: str | None = None
    severity: EquineEventSeverity | None = None

    reservation_id: str | None = None
    assignment_id: str | None = None
    participant_id: str | None = None

    measured_weight_kg: Decimal | None = Field(default=None, gt=0)
    measured_height_m: Decimal | None = Field(default=None, gt=0)

    next_due_at: datetime | None = None
    performed_by: str | None = None
    medication_name: str | None = None
    dosage: str | None = None
    lab_result_summary: str | None = None

    affects_availability: bool = False
    resulting_operational_status: EquineOperationalStatus | None = None
    rest_until: datetime | None = None

    source: EquineEventSource = "mobile_app"


class EquineEventUpdateSchema(BaseModel):
    event_type: EquineEventType | None = None
    happened_at: datetime | None = None
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    severity: EquineEventSeverity | None = None

    reservation_id: str | None = None
    assignment_id: str | None = None
    participant_id: str | None = None

    measured_weight_kg: Decimal | None = Field(default=None, gt=0)
    measured_height_m: Decimal | None = Field(default=None, gt=0)

    next_due_at: datetime | None = None
    performed_by: str | None = None
    medication_name: str | None = None
    dosage: str | None = None
    lab_result_summary: str | None = None

    affects_availability: bool | None = None
    resulting_operational_status: EquineOperationalStatus | None = None
    rest_until: datetime | None = None

    source: EquineEventSource | None = None


class EquineEventResponseSchema(AuditMetadataSchema):
    id: str
    equine_id: str
    event_type: EquineEventType
    happened_at: datetime
    title: str
    description: str | None = None
    severity: EquineEventSeverity | None = None

    reservation_id: str | None = None
    assignment_id: str | None = None
    participant_id: str | None = None

    measured_weight_kg: Decimal | None = None
    measured_height_m: Decimal | None = None

    next_due_at: datetime | None = None
    performed_by: str | None = None
    medication_name: str | None = None
    dosage: str | None = None
    lab_result_summary: str | None = None

    affects_availability: bool = False
    resulting_operational_status: EquineOperationalStatus | None = None
    rest_until: datetime | None = None

    source: EquineEventSource = "mobile_app"


class EquineEventListFilters(BaseModel):
    event_type: EquineEventType | None = None
    date_from: datetime | None = None
    date_to: datetime | None = None
    severity: EquineEventSeverity | None = None
    reservation_id: str | None = None
    affects_availability: bool | None = None
    limit: int = Field(default=50, ge=1, le=500)
