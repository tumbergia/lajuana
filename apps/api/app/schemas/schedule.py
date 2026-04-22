from datetime import date, time

from pydantic import BaseModel, Field

from app.common.enums import ScheduleStatus


class ScheduleCreateSchema(BaseModel):
    experience_id: str
    date: date
    start_time: time
    capacity_total: int = Field(gt=0)
    reserved_slots: int = Field(default=0, ge=0)
    internal_slots: int = Field(default=0, ge=0)
    blocked_slots: int = Field(default=0, ge=0)
    custom_request_only: bool = False
    notes: str | None = None


class ScheduleUpdateSchema(BaseModel):
    capacity_total: int | None = Field(default=None, gt=0)
    reserved_slots: int | None = Field(default=None, ge=0)
    internal_slots: int | None = Field(default=None, ge=0)
    blocked_slots: int | None = Field(default=None, ge=0)
    custom_request_only: bool | None = None
    notes: str | None = None
    status: ScheduleStatus | None = None


class ScheduleResponseSchema(BaseModel):
    id: str
    experience_id: str
    date: date
    start_time: time
    capacity_total: int
    reserved_slots: int
    internal_slots: int
    blocked_slots: int
    available_slots: int
    status: ScheduleStatus
    custom_request_only: bool
    notes: str | None
