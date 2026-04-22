from datetime import datetime

from pydantic import BaseModel

from app.common.enums import AssignmentPriority


class AssignmentCreateSchema(BaseModel):
    reservation_id: str
    participant_id: str
    equine_id: str
    saddle_id: str | None = None
    priority: AssignmentPriority = AssignmentPriority.STANDARD
    assigned_manually: bool = True
    notes: str | None = None


class AssignmentUpdateSchema(BaseModel):
    equine_id: str | None = None
    saddle_id: str | None = None
    priority: AssignmentPriority | None = None
    assigned_manually: bool | None = None
    notes: str | None = None


class AssignmentResponseSchema(BaseModel):
    id: str
    reservation_id: str
    participant_id: str
    equine_id: str
    saddle_id: str | None
    priority: AssignmentPriority
    assigned_manually: bool
    notes: str | None
    created_at: datetime
