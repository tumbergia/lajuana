from datetime import date

from beanie import PydanticObjectId
from pydantic import field_validator
from pymongo import ASCENDING, IndexModel

from app.common.collections import Collections
from app.common.enums import ScheduleStatus
from app.documents.base import AuditDocument

TIME_PATTERN = r"^\d{2}:\d{2}:\d{2}$"


class ScheduleDocument(AuditDocument):
    experience_id: PydanticObjectId
    date: date
    start_time: str

    @field_validator("start_time")
    @classmethod
    def validate_start_time(cls, v: str) -> str:
        import re
        if not re.match(TIME_PATTERN, v):
            raise ValueError(f"start_time must match HH:MM:SS format, got {v!r}")
        return v
    is_active: bool = True
    capacity_total: int
    reserved_slots: int = 0
    internal_slots: int = 0
    held_slots: int = 0
    blocked_slots: int = 0
    available_slots: int
    status: ScheduleStatus = ScheduleStatus.OPEN
    custom_request_only: bool = False
    notes: str | None = None

    class Settings:
        name = Collections.SCHEDULES
        indexes = [
            IndexModel(
                [
                    ("experience_id", ASCENDING),
                    ("date", ASCENDING),
                    ("start_time", ASCENDING),
                ],
                unique=True,
                name="uq_schedule_experience_date_start_time",
            ),
        ]
