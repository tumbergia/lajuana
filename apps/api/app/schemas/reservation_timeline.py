from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.service_log import ServiceLogPhotoSchema


class ReservationTimelineEntrySchema(BaseModel):
    """Entrada unificada de la bitácora de una reserva."""

    id: str
    source: Literal["service_log", "audit_log", "derived"]
    kind: str
    happened_at: datetime
    title: str
    description: str | None = None
    actor_name: str | None = None
    actor_role: str | None = None
    editable: bool = False
    deletable: bool = False
    related_participant_id: str | None = None
    service_log_id: str | None = None
    photos: list[ServiceLogPhotoSchema] = Field(default_factory=list)
    photos_total: int = 0
