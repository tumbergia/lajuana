"""Schemas for role assignment requests."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field

from app.common.enums import RoleRequestStatus, UserRole
from app.schemas.common import AuditMetadataSchema


class RoleRequestCreateSchema(BaseModel):
    requested_role: UserRole


class RoleRequestDecisionSchema(BaseModel):
    action: Literal["approve", "reject"]
    assigned_role: UserRole | None = None
    note: str | None = Field(default=None, max_length=500)


class RoleRequestResponseSchema(AuditMetadataSchema):
    id: str
    user_id: str
    user_email: EmailStr
    user_full_name: str
    user_role: UserRole
    requested_role: UserRole
    status: RoleRequestStatus
    decided_role: UserRole | None = None
    decided_by: str | None = None
    decided_at: datetime | None = None
    note: str | None = None
