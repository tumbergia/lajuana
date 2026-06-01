from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status

from app.api.deps import get_schedule_service, require_permissions
from app.api.docs import ENDPOINT_DOCS, endpoint_description, endpoint_responses
from app.common.enums import Permission, ScheduleStatus
from app.documents import UserDocument
from app.schemas.schedule import ScheduleCreateSchema, ScheduleResponseSchema, ScheduleUpdateSchema
from app.services import ScheduleService
from app.services.mappers import schedule_to_response

router = APIRouter(prefix="/schedules", tags=["Fechas operativas"])


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
    service: ScheduleService = Depends(get_schedule_service),
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
    response: Response,
    experience_id: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    status_filter: ScheduleStatus | None = Query(default=None, alias="status"),
    is_active: bool | None = None,
    limit: int = Query(default=200, ge=1, le=1000),
    skip: int = Query(default=0, ge=0),
    service: ScheduleService = Depends(get_schedule_service),
) -> list[ScheduleResponseSchema]:
    total = await service.count(
        experience_id=experience_id,
        date_from=date_from,
        date_to=date_to,
        status=status_filter,
        is_active=is_active,
    )
    response.headers["X-Total-Count"] = str(total)
    docs = await service.list(
        experience_id=experience_id,
        date_from=date_from,
        date_to=date_to,
        status=status_filter,
        is_active=is_active,
        limit=limit,
        skip=skip,
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
    service: ScheduleService = Depends(get_schedule_service),
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
    service: ScheduleService = Depends(get_schedule_service),
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
    service: ScheduleService = Depends(get_schedule_service),
) -> ScheduleResponseSchema:
    doc = await service.deactivate(schedule_id)
    return schedule_to_response(doc)
