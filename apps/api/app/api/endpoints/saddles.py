"""Router de sillas operativas."""

from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.deps import require_permissions
from app.api.docs import ENDPOINT_DOCS, endpoint_description, endpoint_responses
from app.common.enums import Permission
from app.documents import UserDocument
from app.schemas.saddle import SaddleCreateSchema, SaddleResponseSchema, SaddleUpdateSchema
from app.services import SaddleService
from app.services.mappers import saddle_to_response

router = APIRouter(prefix="/saddles", tags=["Sillas"])
service = SaddleService()


@router.post(
    "",
    response_model=SaddleResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary=ENDPOINT_DOCS["saddles_create"]["summary"],
    description=endpoint_description("saddles_create"),
    operation_id="createSaddle",
    responses=endpoint_responses("saddles_create"),
)
async def create_saddle(
    payload: SaddleCreateSchema,
    _: Annotated[UserDocument, Depends(require_permissions(Permission.SADDLE_CREATE))],
) -> SaddleResponseSchema:
    return saddle_to_response(await service.create(payload))


@router.get(
    "",
    response_model=list[SaddleResponseSchema],
    summary=ENDPOINT_DOCS["saddles_list"]["summary"],
    description=endpoint_description("saddles_list"),
    operation_id="listSaddles",
    responses=endpoint_responses("saddles_list"),
)
async def list_saddles(
    _: Annotated[UserDocument, Depends(require_permissions(Permission.SADDLE_READ))],
) -> list[SaddleResponseSchema]:
    return [saddle_to_response(item) for item in await service.list()]


@router.get(
    "/{saddle_id}",
    response_model=SaddleResponseSchema,
    summary=ENDPOINT_DOCS["saddles_get"]["summary"],
    description=endpoint_description("saddles_get"),
    operation_id="getSaddleById",
    responses=endpoint_responses("saddles_get"),
)
async def get_saddle(
    saddle_id: str,
    _: Annotated[UserDocument, Depends(require_permissions(Permission.SADDLE_READ))],
) -> SaddleResponseSchema:
    return saddle_to_response(await service.get(saddle_id))


@router.patch(
    "/{saddle_id}",
    response_model=SaddleResponseSchema,
    summary=ENDPOINT_DOCS["saddles_update"]["summary"],
    description=endpoint_description("saddles_update"),
    operation_id="updateSaddleById",
    responses=endpoint_responses("saddles_update"),
)
async def update_saddle(
    saddle_id: str,
    payload: SaddleUpdateSchema,
    _: Annotated[UserDocument, Depends(require_permissions(Permission.SADDLE_UPDATE))],
) -> SaddleResponseSchema:
    return saddle_to_response(await service.update(saddle_id, payload))
