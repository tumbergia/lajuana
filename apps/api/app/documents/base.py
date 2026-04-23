from datetime import UTC, datetime

from beanie import Document
from pydantic import Field


def utc_now() -> datetime:
    return datetime.now(UTC)


class AuditDocument(Document):
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    version: int = 1
    deleted_at: datetime | None = None

    async def insert(self, *args, **kwargs):  # type: ignore[override]
        now = utc_now()
        self.created_at = now
        self.updated_at = now
        if self.version < 1:
            self.version = 1
        result = await super().insert(*args, **kwargs)
        await self._emit_sync_change()
        return result

    async def save(self, *args, **kwargs):  # type: ignore[override]
        self.updated_at = utc_now()
        if self.id is not None:
            self.version += 1
        elif self.version < 1:
            self.version = 1
        result = await super().save(*args, **kwargs)
        await self._emit_sync_change()
        return result

    async def mark_deleted(self):
        self.deleted_at = utc_now()
        self.updated_at = self.deleted_at
        self.version += 1
        result = await super().save()
        await self._emit_sync_change(change_type="delete")
        return result

    async def _emit_sync_change(self, change_type: str = "upsert") -> None:
        # Evita recursión sobre colecciones técnicas.
        technical_collections = {"sync_changes", "sync_operation_receipts", "file_uploads"}
        collection_name = getattr(getattr(self, "Settings", object), "name", "")
        if collection_name in technical_collections:
            return
        from app.services.sync_change_service import record_document_change

        await record_document_change(self, change_type=change_type)
