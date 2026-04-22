from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.deps import require_permissions
from app.api.docs import COMMON_AUTH_RESPONSES
from app.common.enums import Permission, ScheduleStatus
from app.documents import UserDocument
from app.schemas.schedule import ScheduleCreateSchema, ScheduleResponseSchema, ScheduleUpdateSchema
from app.services import ScheduleService
from app.services.mappers import schedule_to_response

router = APIRouter(prefix="/schedules", tags=["Schedules"])
service = ScheduleService()


@router.post(
    "",
    response_model=ScheduleResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Crear fecha operativa",
    description="Crea un schedule con capacidad y disponibilidad inicial.",
    operation_id="createSchedule",
    responses=COMMON_AUTH_RESPONSES,
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
    summary="Listar fechas operativas",
    description="Lista fechas operativas con filtros.",
    operation_id="listSchedules",
    responses=COMMON_AUTH_RESPONSES,
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
    summary="Consultar fecha operativa",
    description="Obtiene detalle de un schedule.",
    operation_id="getScheduleById",
    responses=COMMON_AUTH_RESPONSES,
)
async def get_schedule(
    schedule_id: str,
    _: Annotated[UserDocument, Depends(require_permissions(Permission.SCHEDULE_READ))],
) -> ScheduleResponseSchema:
    doc = await service.get(schedule_id)
    return schedule_to_response(doc)


@router.patch("/{schedule_id}", response_model=ScheduleResponseSchema)
async def update_schedule(
    schedule_id: str,
    payload: ScheduleUpdateSchema,
    _: Annotated[UserDocument, Depends(require_permissions(Permission.SCHEDULE_UPDATE))],
) -> ScheduleResponseSchema:
    doc = await service.update(schedule_id, payload)
    return schedule_to_response(doc)
