from datetime import date, time

from beanie import PydanticObjectId

from app.common.collections import Collections
from app.common.enums import ScheduleStatus
from app.documents.base import AuditDocument


class ScheduleDocument(AuditDocument):
    experience_id: PydanticObjectId
    date: date
    start_time: time
    is_active: bool = True
    capacity_total: int
    reserved_slots: int = 0
    internal_slots: int = 0
    blocked_slots: int = 0
    available_slots: int
    status: ScheduleStatus = ScheduleStatus.OPEN
    custom_request_only: bool = False
    notes: str | None = None

    class Settings:
        name = Collections.SCHEDULES
