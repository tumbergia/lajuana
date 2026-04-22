from datetime import UTC, datetime

from beanie import Document
from pydantic import Field


def utc_now() -> datetime:
    return datetime.now(UTC)


class AuditDocument(Document):
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

