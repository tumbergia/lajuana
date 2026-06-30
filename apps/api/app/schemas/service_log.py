from datetime import datetime

from pydantic import BaseModel, Field

from app.documents import ServiceLogEventType
from app.schemas.common import AuditMetadataSchema


class ServiceLogPhotoSchema(BaseModel):
    index: int
    storage_key: str
    filename: str
    content_type: str
    size_bytes: int = 0


class ServiceLogPhotoInputSchema(BaseModel):
    storage_key: str
    filename: str
    content_type: str
    size_bytes: int = 0


class ServiceLogPhotoUploadResponseSchema(BaseModel):
    storage_key: str
    filename: str
    content_type: str
    size_bytes: int


class ServiceLogCreateSchema(BaseModel):
    reservation_id: str
    event_type: ServiceLogEventType
    happened_at: datetime
    checkpoint_name: str | None = None
    notes: str | None = None
    related_participant_id: str | None = None
    related_equine_id: str | None = None
    photos: list[ServiceLogPhotoInputSchema] = Field(default_factory=list)


class ServiceLogUpdateSchema(BaseModel):
    event_type: ServiceLogEventType | None = None
    happened_at: datetime | None = None
    checkpoint_name: str | None = None
    notes: str | None = None
    related_participant_id: str | None = None
    related_equine_id: str | None = None
    photos: list[ServiceLogPhotoInputSchema] | None = None


class ServiceLogResponseSchema(AuditMetadataSchema):
    id: str
    reservation_id: str
    event_type: ServiceLogEventType
    happened_at: datetime
    checkpoint_name: str | None
    notes: str | None
    related_participant_id: str | None
    related_equine_id: str | None
    created_by: str | None = None
    photos: list[ServiceLogPhotoSchema] = Field(default_factory=list)
