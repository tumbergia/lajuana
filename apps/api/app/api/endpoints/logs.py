"""Router de bitácora de servicio."""

from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.deps import require_permissions
from app.api.docs import ENDPOINT_DOCS, endpoint_description, endpoint_responses
from app.common.enums import Permission
from app.documents import UserDocument
from app.schemas.service_log import (
    ServiceLogCreateSchema,
    ServiceLogResponseSchema,
    ServiceLogUpdateSchema,
)
from app.services import ServiceLogService
from app.services.mappers import service_log_to_response

router = APIRouter(prefix="/logs", tags=["Bitacora"])
service = ServiceLogService()


@router.post(
    "",
    response_model=ServiceLogResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary=ENDPOINT_DOCS["logs_create"]["summary"],
    description=endpoint_description("logs_create"),
    operation_id="createLog",
    responses=endpoint_responses("logs_create"),
)
async def create_log(
    payload: ServiceLogCreateSchema,
    _: Annotated[UserDocument, Depends(require_permissions(Permission.LOG_CREATE))],
) -> ServiceLogResponseSchema:
    return service_log_to_response(await service.create(payload))


@router.get(
    "/{log_id}",
    response_model=ServiceLogResponseSchema,
    summary=ENDPOINT_DOCS["logs_get"]["summary"],
    description=endpoint_description("logs_get"),
    operation_id="getLogById",
    responses=endpoint_responses("logs_get"),
)
async def get_log(
    log_id: str,
    _: Annotated[UserDocument, Depends(require_permissions(Permission.LOG_READ))],
) -> ServiceLogResponseSchema:
    return service_log_to_response(await service.get(log_id))


@router.patch(
    "/{log_id}",
    response_model=ServiceLogResponseSchema,
    summary=ENDPOINT_DOCS["logs_update"]["summary"],
    description=endpoint_description("logs_update"),
    operation_id="updateLogById",
    responses=endpoint_responses("logs_update"),
)
async def update_log(
    log_id: str,
    payload: ServiceLogUpdateSchema,
    _: Annotated[UserDocument, Depends(require_permissions(Permission.LOG_UPDATE))],
) -> ServiceLogResponseSchema:
    return service_log_to_response(await service.update(log_id, payload))
