"""Router de sillas operativas."""

from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.deps import require_permissions
from app.api.docs import COMMON_AUTH_RESPONSES
from app.common.enums import Permission
from app.documents import UserDocument
from app.schemas.saddle import SaddleCreateSchema, SaddleResponseSchema, SaddleUpdateSchema
from app.services import SaddleService
from app.services.mappers import saddle_to_response

router = APIRouter(prefix="/saddles", tags=["Saddles"])
service = SaddleService()


@router.post(
    "",
    response_model=SaddleResponseSchema,
    status_code=status.HTTP_201_CREATED,
    responses=COMMON_AUTH_RESPONSES,
)
async def create_saddle(
    payload: SaddleCreateSchema,
    _: Annotated[UserDocument, Depends(require_permissions(Permission.SADDLE_CREATE))],
) -> SaddleResponseSchema:
    return saddle_to_response(await service.create(payload))


@router.get("", response_model=list[SaddleResponseSchema], responses=COMMON_AUTH_RESPONSES)
async def list_saddles(
    _: Annotated[UserDocument, Depends(require_permissions(Permission.SADDLE_READ))],
) -> list[SaddleResponseSchema]:
    return [saddle_to_response(item) for item in await service.list()]


@router.get("/{saddle_id}", response_model=SaddleResponseSchema, responses=COMMON_AUTH_RESPONSES)
async def get_saddle(
    saddle_id: str,
    _: Annotated[UserDocument, Depends(require_permissions(Permission.SADDLE_READ))],
) -> SaddleResponseSchema:
    return saddle_to_response(await service.get(saddle_id))


@router.patch("/{saddle_id}", response_model=SaddleResponseSchema, responses=COMMON_AUTH_RESPONSES)
async def update_saddle(
    saddle_id: str,
    payload: SaddleUpdateSchema,
    _: Annotated[UserDocument, Depends(require_permissions(Permission.SADDLE_UPDATE))],
) -> SaddleResponseSchema:
    return saddle_to_response(await service.update(saddle_id, payload))
