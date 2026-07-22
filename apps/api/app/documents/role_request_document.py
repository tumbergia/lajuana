from datetime import datetime

from beanie import PydanticObjectId
from pydantic import Field

from app.common.collections import Collections
from app.common.enums import RoleRequestStatus, UserRole
from app.documents.base import AuditDocument


class RoleRequestDocument(AuditDocument):
    user_id: PydanticObjectId
    requested_role: UserRole
    status: RoleRequestStatus = RoleRequestStatus.PENDING
    decided_role: UserRole | None = None
    decided_by: PydanticObjectId | None = None
    decided_at: datetime | None = None
    note: str | None = Field(default=None, max_length=500)

    class Settings:
        name = Collections.ROLE_REQUESTS
        indexes = [
            "user_id",
            "status",
            [("user_id", 1), ("status", 1)],
            [("status", 1), ("created_at", -1)],
        ]
