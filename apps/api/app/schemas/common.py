from datetime import datetime
from typing import Any

from pydantic import BaseModel


class ApiErrorResponse(BaseModel):
    code: str
    message: str
    details: dict[str, Any] | None = None


class AuditMetadataSchema(BaseModel):
    version: int
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None
