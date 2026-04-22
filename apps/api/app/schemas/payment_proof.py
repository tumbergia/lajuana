from datetime import datetime

from pydantic import BaseModel, Field

from app.common.enums import PaymentStatus


class PaymentProofCreateSchema(BaseModel):
    filename: str
    content_type: str
    size_bytes: int = Field(gt=0)
    sha256: str
    content_base64: str


class PaymentProofUpdateSchema(BaseModel):
    status: PaymentStatus | None = None
    reservation_id: str | None = None
    filename: str | None = None
    content_type: str | None = None
    size_bytes: int | None = Field(default=None, gt=0)
    sha256: str | None = None


class PaymentProofResponseSchema(BaseModel):
    id: str
    reservation_id: str
    storage_key: str
    filename: str
    content_type: str
    size_bytes: int
    sha256: str
    status: PaymentStatus
    uploaded_at: datetime
