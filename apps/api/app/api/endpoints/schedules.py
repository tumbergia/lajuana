from datetime import date

from fastapi import APIRouter

from app.common.enums import ScheduleStatus
from app.schemas.schedule import ScheduleCreateSchema, ScheduleResponseSchema, ScheduleUpdateSchema
from app.services import ScheduleService
from app.services.mappers import schedule_to_response

router = APIRouter(prefix="/schedules", tags=["schedules"])
service = ScheduleService()


@router.post("", response_model=ScheduleResponseSchema, status_code=201)
async def create_schedule(payload: ScheduleCreateSchema) -> ScheduleResponseSchema:
    doc = await service.create(payload)
    return schedule_to_response(doc)


@router.get("", response_model=list[ScheduleResponseSchema])
async def list_schedules(
    experience_id: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    status: ScheduleStatus | None = None,
) -> list[ScheduleResponseSchema]:
    docs = await service.list(
        experience_id=experience_id,
        date_from=date_from,
        date_to=date_to,
        status=status,
    )
    return [schedule_to_response(doc) for doc in docs]


@router.get("/{schedule_id}", response_model=ScheduleResponseSchema)
async def get_schedule(schedule_id: str) -> ScheduleResponseSchema:
    doc = await service.get(schedule_id)
    return schedule_to_response(doc)


@router.patch("/{schedule_id}", response_model=ScheduleResponseSchema)
async def update_schedule(
    schedule_id: str,
    payload: ScheduleUpdateSchema,
) -> ScheduleResponseSchema:
    doc = await service.update(schedule_id, payload)
    return schedule_to_response(doc)
