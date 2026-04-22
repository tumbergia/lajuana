from datetime import datetime

from pydantic import BaseModel

from app.documents import ServiceLogEventType


class ServiceLogCreateSchema(BaseModel):
    reservation_id: str
    event_type: ServiceLogEventType
    happened_at: datetime
    checkpoint_name: str | None = None
    notes: str | None = None
    related_participant_id: str | None = None
    related_equine_id: str | None = None


class ServiceLogUpdateSchema(BaseModel):
    event_type: ServiceLogEventType | None = None
    happened_at: datetime | None = None
    checkpoint_name: str | None = None
    notes: str | None = None
    related_participant_id: str | None = None
    related_equine_id: str | None = None


class ServiceLogResponseSchema(BaseModel):
    id: str
    reservation_id: str
    event_type: ServiceLogEventType
    happened_at: datetime
    checkpoint_name: str | None
    notes: str | None
    related_participant_id: str | None
    related_equine_id: str | None
    created_at: datetime
