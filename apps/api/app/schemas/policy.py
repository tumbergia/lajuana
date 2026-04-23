from datetime import datetime

from pydantic import BaseModel

from app.schemas.common import AuditMetadataSchema


class PolicyCreateSchema(BaseModel):
    reservation_id: str
    provider_id: str | None = None
    policy_number: str
    issued_at: datetime | None = None
    expires_at: datetime | None = None
    notes: str | None = None


class PolicyUpdateSchema(BaseModel):
    provider_id: str | None = None
    policy_number: str | None = None
    issued_at: datetime | None = None
    expires_at: datetime | None = None
    notes: str | None = None


class PolicyResponseSchema(AuditMetadataSchema):
    id: str
    reservation_id: str
    provider_id: str | None
    policy_number: str
    issued_at: datetime | None
    expires_at: datetime | None
    notes: str | None
