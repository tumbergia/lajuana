from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.common.enums import PaymentStatus
from app.schemas.common import AuditMetadataSchema


class PaymentProofCreateSchema(BaseModel):
    filename: str
    content_type: str
    size_bytes: int = Field(gt=0)
    sha256: str
    storage_key: str


class PaymentProofUpdateSchema(BaseModel):
    reservation_id: str | None = None
    filename: str | None = None
    content_type: str | None = None
    size_bytes: int | None = Field(default=None, gt=0)
    sha256: str | None = None

    model_config = {"extra": "forbid"}


class PaymentProofVerifySchema(BaseModel):
    confirmation_token: Literal["VERIFY_PAYMENT"]
    amount: float | None = Field(default=None, gt=0)
    reference: str | None = None
    note: str | None = None


class PaymentProofApproveSchema(BaseModel):
    confirmation_token: Literal["APPROVE_PAYMENT"]
    note: str | None = None


class PaymentProofRejectSchema(BaseModel):
    confirmation_token: Literal["REJECT_PAYMENT"]
    reason: str = Field(min_length=1)


class PaymentProofUnverifySchema(BaseModel):
    confirmation_token: Literal["UNVERIFY_PAYMENT"]
    note: str | None = None


class PaymentProofUnrejectSchema(BaseModel):
    confirmation_token: Literal["UNREJECT_PAYMENT"]
    note: str | None = None


class PaymentProofResponseSchema(AuditMetadataSchema):
    id: str
    reservation_id: str
    storage_key: str
    filename: str
    content_type: str
    size_bytes: int
    sha256: str
    status: PaymentStatus
    uploaded_at: datetime
