from beanie import PydanticObjectId

from app.common.collections import Collections
from app.common.enums import AssignmentPriority
from app.documents.base import AuditDocument


class AssignmentDocument(AuditDocument):
    reservation_id: PydanticObjectId
    participant_id: PydanticObjectId
    equine_id: PydanticObjectId
    saddle_id: PydanticObjectId | None = None
    priority: AssignmentPriority = AssignmentPriority.STANDARD
    assigned_manually: bool = True
    notes: str | None = None

    class Settings:
        name = Collections.ASSIGNMENTS
