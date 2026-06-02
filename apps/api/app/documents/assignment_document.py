from datetime import datetime

from beanie import PydanticObjectId
from pymongo import IndexModel

from app.common.collections import Collections
from app.common.enums import AssignmentSource, AssignmentStatus
from app.documents.base import AuditDocument


class AssignmentDocument(AuditDocument):
    reservation_id: PydanticObjectId
    participant_id: PydanticObjectId
    equine_id: PydanticObjectId
    saddle_id: PydanticObjectId | None = None

    # ── Contract fields ──
    status: AssignmentStatus = AssignmentStatus.DRAFT
    source: AssignmentSource = AssignmentSource.MANUAL_ADMIN
    notes: str | None = None

    safety_flags: list[str] = []
    validation_warnings: list[str] = []

    assigned_by_user_id: PydanticObjectId | None = None
    finalized_by_user_id: PydanticObjectId | None = None
    assigned_at: datetime | None = None
    finalized_at: datetime | None = None

    is_active: bool = True
    replaced_by_assignment_id: PydanticObjectId | None = None

    # ── Deprecated (mantener para backward compat con docs existentes) ──
    priority: str = "standard"
    assigned_manually: bool = True

    class Settings:
        name = Collections.ASSIGNMENTS
        indexes = [
            IndexModel(
                [("reservation_id", 1), ("participant_id", 1), ("is_active", 1)],
            ),
        ]
