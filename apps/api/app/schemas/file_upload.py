from datetime import datetime

from pydantic import BaseModel, Field


class FileInitUploadRequestSchema(BaseModel):
    context: str
    filename: str
    mime_type: str
    size_bytes: int = Field(gt=0)
    sha256_hash: str


class FileInitUploadResponseSchema(BaseModel):
    upload_id: str
    storage_key: str
    upload_url: str
    expires_at: datetime


class FileCompleteUploadResponseSchema(BaseModel):
    upload_id: str
    storage_key: str
    size_bytes: int
    sha256_hash: str
    status: str
