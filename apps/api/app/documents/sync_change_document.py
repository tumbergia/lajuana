from datetime import datetime
from typing import Any, Literal

from beanie import Indexed
from pydantic import Field

from app.common.collections import Collections
from app.documents.base import AuditDocument, utc_now


class SyncChangeDocument(AuditDocument):
    stream: str
    entity_type: str
    entity_id: Indexed(str)  # type: ignore[valid-type]
    change_type: Literal["upsert", "delete", "purge"] = "upsert"
    version: int
    entity_updated_at: datetime
    payload: dict[str, Any] | None = None
    cursor: Indexed(str) = Field(default_factory=lambda: utc_now().isoformat())  # type: ignore[valid-type]
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    class Settings:
        name = Collections.SYNC_CHANGES
