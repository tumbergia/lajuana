from datetime import datetime
from typing import Any, Literal

from beanie import Indexed
from pydantic import Field

from app.common.collections import Collections
from app.documents.base import AuditDocument, utc_now


class SyncOperationReceiptDocument(AuditDocument):
    user_id: Indexed(str)  # type: ignore[valid-type]
    idempotency_key: Indexed(str)  # type: ignore[valid-type]
    operation_id: str
    entity_type: str
    entity_local_id: str
    entity_remote_id: str | None = None
    status: Literal["applied", "conflict", "rejected"]
    entity_version: int | None = None
    entity_updated_at: datetime | None = None
    payload: dict[str, Any] | None = None
    error: dict[str, Any] | None = None
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    class Settings:
        name = Collections.SYNC_OPERATION_RECEIPTS
