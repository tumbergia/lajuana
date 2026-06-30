from datetime import datetime
from enum import StrEnum

from beanie import PydanticObjectId
from pydantic import BaseModel, Field

from app.common.collections import Collections
from app.documents.base import AuditDocument, utc_now


class ServiceLogEventType(StrEnum):
    ARRIVAL = "arrival"
    DEPARTURE = "departure"
    CHECKPOINT = "checkpoint"
    CLOSURE = "closure"
    INCIDENT = "incident"
    NOTE = "note"


class ServiceLogPhoto(BaseModel):
    storage_key: str
    filename: str
    content_type: str
    size_bytes: int = 0


class ServiceLogDocument(AuditDocument):
    reservation_id: PydanticObjectId
    event_type: ServiceLogEventType
    happened_at: datetime = utc_now()
    checkpoint_name: str | None = None
    notes: str | None = None
    related_participant_id: PydanticObjectId | None = None
    related_equine_id: PydanticObjectId | None = None
    created_by: PydanticObjectId | None = None
    photos: list[ServiceLogPhoto] = Field(default_factory=list)

    class Settings:
        name = Collections.SERVICE_LOGS
