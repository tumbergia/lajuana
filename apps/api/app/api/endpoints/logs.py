"""Router de bitácora de servicio."""

from typing import Annotated

from fastapi import APIRouter, Depends, File, Query, UploadFile, status
from fastapi.responses import Response

from app.api.deps import get_service_log_service, require_permissions
from app.api.docs import ENDPOINT_DOCS, endpoint_description, endpoint_responses
from app.common.enums import Permission
from app.documents import UserDocument
from app.schemas.service_log import (
    ServiceLogCreateSchema,
    ServiceLogPhotoUploadResponseSchema,
    ServiceLogResponseSchema,
    ServiceLogUpdateSchema,
)
from app.services import ServiceLogService
from app.services.mappers import service_log_to_response

router = APIRouter(prefix="/logs", tags=["Bitacora"])


@router.post(
    "/photos/upload",
    response_model=ServiceLogPhotoUploadResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary=ENDPOINT_DOCS["logs_photo_upload"]["summary"],
    description=endpoint_description("logs_photo_upload"),
    operation_id="uploadLogPhoto",
    responses=endpoint_responses("logs_photo_upload"),
)
async def upload_log_photo(
    reservation_id: str,
    current_user: Annotated[UserDocument, Depends(require_permissions(Permission.LOG_CREATE))],
    service: ServiceLogService = Depends(get_service_log_service),
    file: UploadFile = File(...),
) -> ServiceLogPhotoUploadResponseSchema:
    return await service.upload_photo(reservation_id=reservation_id, upload=file)


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
    current_user: Annotated[UserDocument, Depends(require_permissions(Permission.LOG_CREATE))],
    service: ServiceLogService = Depends(get_service_log_service),
) -> ServiceLogResponseSchema:
    return service_log_to_response(
        await service.create(payload, actor_id=current_user.id),
    )


@router.get(
    "",
    response_model=list[ServiceLogResponseSchema],
    summary=ENDPOINT_DOCS["logs_list"]["summary"],
    description=endpoint_description("logs_list"),
    operation_id="listLogs",
    responses=endpoint_responses("logs_list"),
)
async def list_logs(
    reservation_id: str,
    _: Annotated[UserDocument, Depends(require_permissions(Permission.LOG_READ))],
    service: ServiceLogService = Depends(get_service_log_service),
    limit: int = Query(default=200, ge=1, le=1000),
    skip: int = Query(default=0, ge=0),
) -> list[ServiceLogResponseSchema]:
    docs = await service.list_by_reservation(reservation_id, limit=limit, skip=skip)
    return [service_log_to_response(doc) for doc in docs]


@router.get(
    "/{log_id}/photos/{photo_index}/download",
    summary=ENDPOINT_DOCS["logs_photo_download"]["summary"],
    description=endpoint_description("logs_photo_download"),
    operation_id="downloadLogPhoto",
    responses=endpoint_responses("logs_photo_download"),
)
async def download_log_photo(
    log_id: str,
    photo_index: int,
    _: Annotated[UserDocument, Depends(require_permissions(Permission.LOG_READ))],
    service: ServiceLogService = Depends(get_service_log_service),
) -> Response:
    content_type, file_bytes = await service.get_photo_download(log_id, photo_index)
    return Response(content=file_bytes, media_type=content_type)


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
    service: ServiceLogService = Depends(get_service_log_service),
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
    current_user: Annotated[UserDocument, Depends(require_permissions(Permission.LOG_UPDATE))],
    service: ServiceLogService = Depends(get_service_log_service),
) -> ServiceLogResponseSchema:
    return service_log_to_response(
        await service.update(log_id, payload, actor_role=current_user.role),
    )


@router.delete(
    "/{log_id}",
    response_model=ServiceLogResponseSchema,
    summary=ENDPOINT_DOCS["logs_delete"]["summary"],
    description=endpoint_description("logs_delete"),
    operation_id="deleteLogById",
    responses=endpoint_responses("logs_delete"),
)
async def delete_log(
    log_id: str,
    current_user: Annotated[UserDocument, Depends(require_permissions(Permission.LOG_UPDATE))],
    service: ServiceLogService = Depends(get_service_log_service),
) -> ServiceLogResponseSchema:
    doc = await service.soft_delete(log_id, actor_role=current_user.role)
    return service_log_to_response(doc)
