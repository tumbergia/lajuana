"""Router de equinos operativos."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status

from app.api.deps import get_equine_service, require_permissions
from app.api.docs import ENDPOINT_DOCS, endpoint_description, endpoint_responses
from app.common.enums import EquineOperationalStatus, Permission
from app.documents import UserDocument
from app.schemas.equine import (
    EquineCreateSchema,
    EquineListItemSchema,
    EquineResponseSchema,
    EquineTimelineEntrySchema,
    EquineUpdateSchema,
)
from app.services import EquineService
from app.services.mappers import equine_to_list_item, equine_to_response

router = APIRouter(prefix="/equines", tags=["Equinos"])


@router.post(
    "",
    response_model=EquineResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary=ENDPOINT_DOCS["equines_create"]["summary"],
    description=endpoint_description("equines_create"),
    operation_id="createEquine",
    responses=endpoint_responses("equines_create"),
)
async def create_equine(
    payload: EquineCreateSchema,
    _: Annotated[UserDocument, Depends(require_permissions(Permission.EQUINE_CREATE))],
    service: EquineService = Depends(get_equine_service),
) -> EquineResponseSchema:
    return equine_to_response(await service.create(payload))


@router.get(
    "",
    response_model=list[EquineResponseSchema],
    summary=ENDPOINT_DOCS["equines_list"]["summary"],
    description=endpoint_description("equines_list"),
    operation_id="listEquines",
    responses=endpoint_responses("equines_list"),
)
async def list_equines(
    _: Annotated[UserDocument, Depends(require_permissions(Permission.EQUINE_READ))],
    response: Response,
    operational_status: EquineOperationalStatus | None = None,
    is_active: bool | None = None,
    is_available: bool | None = None,
    include_deleted: bool = Query(default=False, description="Incluir equinos borrados logicamente"),
    limit: int = Query(default=200, ge=1, le=1000),
    skip: int = Query(default=0, ge=0),
    service: EquineService = Depends(get_equine_service),
) -> list[EquineResponseSchema]:
    total = await service.count(
        operational_status=operational_status,
        is_active=is_active,
        is_available=is_available,
        include_deleted=include_deleted,
    )
    response.headers["X-Total-Count"] = str(total)
    return [
        equine_to_response(item)
        for item in await service.list(
            operational_status=operational_status,
            is_active=is_active,
            is_available=is_available,
            include_deleted=include_deleted,
            limit=limit,
            skip=skip,
        )
    ]


@router.get(
    "/list",
    response_model=list[EquineListItemSchema],
    summary="Listado compacto de equinos",
    description="Retorna solo campos ligeros para cards de listado móvil.",
    operation_id="listEquineItems",
    responses=endpoint_responses("equines_list"),
)
async def list_equine_items(
    _: Annotated[UserDocument, Depends(require_permissions(Permission.EQUINE_READ))],
    response: Response,
    operational_status: EquineOperationalStatus | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    is_available: bool | None = Query(default=None),
    include_deleted: bool = Query(default=False, description="Incluir equinos borrados logicamente"),
    limit: int = Query(default=200, ge=1, le=1000),
    skip: int = Query(default=0, ge=0),
    service: EquineService = Depends(get_equine_service),
) -> list[EquineListItemSchema]:
    total = await service.count(
        operational_status=operational_status,
        is_active=is_active,
        is_available=is_available,
        include_deleted=include_deleted,
    )
    response.headers["X-Total-Count"] = str(total)
    return [
        equine_to_list_item(item)
        for item in await service.list(
            operational_status=operational_status,
            is_active=is_active,
            is_available=is_available,
            include_deleted=include_deleted,
            limit=limit,
            skip=skip,
        )
    ]


@router.get(
    "/{equine_id}",
    response_model=EquineResponseSchema,
    summary=ENDPOINT_DOCS["equines_get"]["summary"],
    description=endpoint_description("equines_get"),
    operation_id="getEquineById",
    responses=endpoint_responses("equines_get"),
)
async def get_equine(
    equine_id: str,
    _: Annotated[UserDocument, Depends(require_permissions(Permission.EQUINE_READ))],
    service: EquineService = Depends(get_equine_service),
) -> EquineResponseSchema:
    return equine_to_response(await service.get(equine_id))


@router.get(
    "/{equine_id}/timeline",
    response_model=list[EquineTimelineEntrySchema],
    summary="Timeline del equino",
    description=(
        "Retorna el historial cronológico unificado: bitácora de servicio "
        "(service_log) y eventos de cuidado (equine_event)."
    ),
    operation_id="getEquineTimeline",
    responses={
        200: {"description": "Timeline obtenido correctamente."},
        401: {"description": "No autenticado."},
        404: {"description": "Equino no encontrado."},
    },
)
async def get_equine_timeline(
    equine_id: str,
    _: Annotated[UserDocument, Depends(require_permissions(Permission.EQUINE_READ))],
    limit: int = Query(default=50, ge=1, le=500),
    service: EquineService = Depends(get_equine_service),
) -> list[EquineTimelineEntrySchema]:
    return await service.get_timeline(equine_id, limit=limit)


@router.get(
    "/available-for-reservation/{reservation_id}",
    response_model=list[EquineListItemSchema],
    summary="Equinos disponibles para reserva",
    description="Retorna todos los equinos con campo block_reason. Null = asignable. Con texto = motivo de exclusión (inactivo, no disponible, ya asignado, misma fecha).",
    operation_id="listAvailableEquinesForReservation",
    responses={
        200: {"description": "Listado de equinos disponibles."},
        401: {"description": "No autenticado."},
    },
)
async def list_available_for_reservation(
    reservation_id: str,
    _: Annotated[UserDocument, Depends(require_permissions(Permission.EQUINE_READ))],
    response: Response,
    limit: int = Query(default=200, ge=1, le=1000),
    skip: int = Query(default=0, ge=0),
    service: EquineService = Depends(get_equine_service),
) -> list[EquineListItemSchema]:
    items = await service.list_available_for_reservation(
        reservation_id, limit=limit, skip=skip,
    )
    response.headers["X-Total-Count"] = str(len(items))
    result: list[EquineListItemSchema] = []
    for equine_doc, block_reason in items:
        item = equine_to_list_item(equine_doc)
        item.block_reason = block_reason
        result.append(item)
    return result


@router.patch(
    "/{equine_id}",
    response_model=EquineResponseSchema,
    summary=ENDPOINT_DOCS["equines_update"]["summary"],
    description=endpoint_description("equines_update"),
    operation_id="updateEquineById",
    responses=endpoint_responses("equines_update"),
)
async def update_equine(
    equine_id: str,
    payload: EquineUpdateSchema,
    _: Annotated[UserDocument, Depends(require_permissions(Permission.EQUINE_UPDATE))],
    service: EquineService = Depends(get_equine_service),
) -> EquineResponseSchema:
    return equine_to_response(await service.update(equine_id, payload))


@router.delete(
    "/{equine_id}",
    response_model=EquineResponseSchema,
    summary=ENDPOINT_DOCS["equines_delete"]["summary"],
    description=endpoint_description("equines_delete"),
    operation_id="deleteEquine",
    responses=endpoint_responses("equines_delete"),
)
async def delete_equine(
    equine_id: str,
    _: Annotated[UserDocument, Depends(require_permissions(Permission.EQUINE_DELETE))],
    service: EquineService = Depends(get_equine_service),
) -> EquineResponseSchema:
    return equine_to_response(await service.soft_delete(equine_id))


@router.post(
    "/{equine_id}/restore",
    response_model=EquineResponseSchema,
    summary="Restaurar equino borrado",
    description="Quita el deleted_at para que el equino vuelva a aparecer en listados activos.",
    operation_id="restoreEquine",
    responses=endpoint_responses("equines_update"),
)
async def restore_equine(
    equine_id: str,
    _: Annotated[UserDocument, Depends(require_permissions(Permission.EQUINE_UPDATE))],
    service: EquineService = Depends(get_equine_service),
) -> EquineResponseSchema:
    return equine_to_response(await service.restore(equine_id))
