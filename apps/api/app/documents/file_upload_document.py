from datetime import datetime
from typing import Literal

from beanie import Indexed
from pydantic import Field

from app.common.collections import Collections
from app.documents.base import AuditDocument, utc_now


class FileUploadDocument(AuditDocument):
    upload_id: Indexed(str, unique=True)  # type: ignore[valid-type]
    user_id: str
    context: str
    filename: str
    mime_type: str
    size_bytes: int
    sha256_hash: str
    storage_key: str
    upload_url: str
    expires_at: datetime
    status: Literal["initialized", "ready", "expired"] = "initialized"
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    class Settings:
        name = Collections.FILE_UPLOADS
