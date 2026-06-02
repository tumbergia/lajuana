from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel

from app.common.enums import AssignmentSource, AssignmentStatus
from app.schemas.common import AuditMetadataSchema
from app.schemas.equine import EquineListItemSchema
from app.schemas.saddle import SaddleListItemSchema


class AssignmentCreateSchema(BaseModel):
    reservation_id: str
    participant_id: str
    equine_id: str
    saddle_id: str | None = None
    status: AssignmentStatus = AssignmentStatus.CONFIRMED
    notes: str | None = None


class AssignmentUpdateSchema(BaseModel):
    equine_id: str | None = None
    saddle_id: str | None = None
    status: AssignmentStatus | None = None
    notes: str | None = None


class AssignmentResponseSchema(AuditMetadataSchema):
    id: str
    reservation_id: str
    participant_id: str
    participant_name: str | None = None
    equine_id: str
    equine_name: str | None = None
    saddle_id: str | None = None
    saddle_label: str | None = None
    status: AssignmentStatus
    source: AssignmentSource
    safety_flags: list[str] = []
    validation_warnings: list[str] = []
    notes: str | None = None
    is_active: bool = True
    assigned_by_user_id: str | None = None
    finalized_by_user_id: str | None = None
    assigned_at: datetime | None = None
    finalized_at: datetime | None = None


# ── Assignment Board schemas ──


class AssignmentOnBoardSchema(BaseModel):
    assignment_id: str | None = None
    equine_id: str | None = None
    equine_name: str | None = None
    saddle_id: str | None = None
    saddle_label: str | None = None
    status: AssignmentStatus | None = None
    warnings: list[str] = []


class AssignmentBoardParticipantSchema(BaseModel):
    participant_id: str
    full_name: str
    age_years: int | None = None
    weight_kg: Decimal | None = None
    height_cm: Decimal | None = None
    experience_level: str | None = None
    assignment: AssignmentOnBoardSchema | None = None
    blocking_reasons: list[str] = []


class AssignmentBoardSummarySchema(BaseModel):
    participants_total: int = 0
    assigned_total: int = 0
    pending_total: int = 0
    blocking_total: int = 0


class AssignmentBoardResponseSchema(BaseModel):
    reservation_id: str
    reservation_status: str
    scheduled_date: str | None = None
    participants: list[AssignmentBoardParticipantSchema] = []
    available_equines: list[EquineListItemSchema] = []
    available_saddles: list[SaddleListItemSchema] = []
    summary: AssignmentBoardSummarySchema = AssignmentBoardSummarySchema()
