"""Router de equinos operativos."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import require_permissions
from app.api.docs import ENDPOINT_DOCS, endpoint_description, endpoint_responses
from app.common.enums import EquineOperationalStatus, Permission
from app.documents import UserDocument
from app.schemas.equine import (
    EquineCreateSchema,
    EquineListItemSchema,
    EquineResponseSchema,
    EquineUpdateSchema,
)
from app.services import EquineService
from app.services.mappers import equine_to_list_item, equine_to_response

router = APIRouter(prefix="/equines", tags=["Equinos"])
service = EquineService()


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
    operational_status: EquineOperationalStatus | None = None,
    is_active: bool | None = None,
    is_available: bool | None = None,
) -> list[EquineResponseSchema]:
    return [
        equine_to_response(item)
        for item in await service.list(
            operational_status=operational_status,
            is_active=is_active,
            is_available=is_available,
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
    operational_status: EquineOperationalStatus | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    is_available: bool | None = Query(default=None),
) -> list[EquineListItemSchema]:
    return [
        equine_to_list_item(item)
        for item in await service.list_items(
            operational_status=operational_status,
            is_active=is_active,
            is_available=is_available,
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
) -> EquineResponseSchema:
    return equine_to_response(await service.get(equine_id))


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
) -> EquineResponseSchema:
    return equine_to_response(await service.update(equine_id, payload))


@router.delete(
    "/{equine_id}",
    response_model=EquineResponseSchema,
    summary=ENDPOINT_DOCS["equines_delete"]["summary"],
    description=endpoint_description("equines_delete"),
    operation_id="deactivateEquineById",
    responses=endpoint_responses("equines_delete"),
)
async def deactivate_equine(
    equine_id: str,
    _: Annotated[UserDocument, Depends(require_permissions(Permission.EQUINE_UPDATE))],
) -> EquineResponseSchema:
    return equine_to_response(await service.deactivate(equine_id))
