from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.deps import require_permissions
from app.api.docs import ENDPOINT_DOCS, endpoint_description, endpoint_responses
from app.common.enums import Permission, ScheduleStatus
from app.documents import UserDocument
from app.schemas.schedule import ScheduleCreateSchema, ScheduleResponseSchema, ScheduleUpdateSchema
from app.services import ScheduleService
from app.services.mappers import schedule_to_response

router = APIRouter(prefix="/schedules", tags=["Fechas operativas"])
service = ScheduleService()


@router.post(
    "",
    response_model=ScheduleResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary=ENDPOINT_DOCS["schedules_create"]["summary"],
    description=endpoint_description("schedules_create"),
    operation_id="createSchedule",
    responses=endpoint_responses("schedules_create"),
)
async def create_schedule(
    payload: ScheduleCreateSchema,
    _: Annotated[UserDocument, Depends(require_permissions(Permission.SCHEDULE_CREATE))],
) -> ScheduleResponseSchema:
    doc = await service.create(payload)
    return schedule_to_response(doc)


@router.get(
    "",
    response_model=list[ScheduleResponseSchema],
    summary=ENDPOINT_DOCS["schedules_list"]["summary"],
    description=endpoint_description("schedules_list"),
    operation_id="listSchedules",
    responses=endpoint_responses("schedules_list"),
)
async def list_schedules(
    _: Annotated[UserDocument, Depends(require_permissions(Permission.SCHEDULE_READ))],
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


@router.get(
    "/{schedule_id}",
    response_model=ScheduleResponseSchema,
    summary=ENDPOINT_DOCS["schedules_get"]["summary"],
    description=endpoint_description("schedules_get"),
    operation_id="getScheduleById",
    responses=endpoint_responses("schedules_get"),
)
async def get_schedule(
    schedule_id: str,
    _: Annotated[UserDocument, Depends(require_permissions(Permission.SCHEDULE_READ))],
) -> ScheduleResponseSchema:
    doc = await service.get(schedule_id)
    return schedule_to_response(doc)


@router.patch(
    "/{schedule_id}",
    response_model=ScheduleResponseSchema,
    summary=ENDPOINT_DOCS["schedules_update"]["summary"],
    description=endpoint_description("schedules_update"),
    operation_id="updateScheduleById",
    responses=endpoint_responses("schedules_update"),
)
async def update_schedule(
    schedule_id: str,
    payload: ScheduleUpdateSchema,
    _: Annotated[UserDocument, Depends(require_permissions(Permission.SCHEDULE_UPDATE))],
) -> ScheduleResponseSchema:
    doc = await service.update(schedule_id, payload)
    return schedule_to_response(doc)


@router.delete(
    "/{schedule_id}",
    response_model=ScheduleResponseSchema,
    summary=ENDPOINT_DOCS["schedules_delete"]["summary"],
    description=endpoint_description("schedules_delete"),
    operation_id="deactivateScheduleById",
    responses=endpoint_responses("schedules_delete"),
)
async def deactivate_schedule(
    schedule_id: str,
    _: Annotated[UserDocument, Depends(require_permissions(Permission.SCHEDULE_DELETE))],
) -> ScheduleResponseSchema:
    doc = await service.deactivate(schedule_id)
    return schedule_to_response(doc)
