"""Router de equinos operativos."""

from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.deps import require_permissions
from app.api.docs import COMMON_AUTH_RESPONSES
from app.common.enums import Permission
from app.documents import UserDocument
from app.schemas.equine import EquineCreateSchema, EquineResponseSchema, EquineUpdateSchema
from app.services import EquineService
from app.services.mappers import equine_to_response

router = APIRouter(prefix="/equines", tags=["Equines"])
service = EquineService()


@router.post(
    "",
    response_model=EquineResponseSchema,
    status_code=status.HTTP_201_CREATED,
    responses=COMMON_AUTH_RESPONSES,
)
async def create_equine(
    payload: EquineCreateSchema,
    _: Annotated[UserDocument, Depends(require_permissions(Permission.EQUINE_CREATE))],
) -> EquineResponseSchema:
    return equine_to_response(await service.create(payload))


@router.get("", response_model=list[EquineResponseSchema], responses=COMMON_AUTH_RESPONSES)
async def list_equines(
    _: Annotated[UserDocument, Depends(require_permissions(Permission.EQUINE_READ))],
) -> list[EquineResponseSchema]:
    return [equine_to_response(item) for item in await service.list()]


@router.get("/{equine_id}", response_model=EquineResponseSchema, responses=COMMON_AUTH_RESPONSES)
async def get_equine(
    equine_id: str,
    _: Annotated[UserDocument, Depends(require_permissions(Permission.EQUINE_READ))],
) -> EquineResponseSchema:
    return equine_to_response(await service.get(equine_id))


@router.patch("/{equine_id}", response_model=EquineResponseSchema, responses=COMMON_AUTH_RESPONSES)
async def update_equine(
    equine_id: str,
    payload: EquineUpdateSchema,
    _: Annotated[UserDocument, Depends(require_permissions(Permission.EQUINE_UPDATE))],
) -> EquineResponseSchema:
    return equine_to_response(await service.update(equine_id, payload))
