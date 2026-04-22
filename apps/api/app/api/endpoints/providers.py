"""Router de proveedores."""

from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.deps import require_permissions
from app.api.docs import COMMON_AUTH_RESPONSES
from app.common.enums import Permission
from app.documents import UserDocument
from app.schemas.provider import ProviderCreateSchema, ProviderResponseSchema, ProviderUpdateSchema
from app.services import ProviderService
from app.services.mappers import provider_to_response

router = APIRouter(prefix="/providers", tags=["Providers"])
service = ProviderService()


@router.post(
    "",
    response_model=ProviderResponseSchema,
    status_code=status.HTTP_201_CREATED,
    responses=COMMON_AUTH_RESPONSES,
)
async def create_provider(
    payload: ProviderCreateSchema,
    _: Annotated[UserDocument, Depends(require_permissions(Permission.PROVIDER_CREATE))],
) -> ProviderResponseSchema:
    return provider_to_response(await service.create(payload))


@router.get(
    "/{provider_id}",
    response_model=ProviderResponseSchema,
    responses=COMMON_AUTH_RESPONSES,
)
async def get_provider(
    provider_id: str,
    _: Annotated[UserDocument, Depends(require_permissions(Permission.PROVIDER_READ))],
) -> ProviderResponseSchema:
    return provider_to_response(await service.get(provider_id))


@router.patch(
    "/{provider_id}",
    response_model=ProviderResponseSchema,
    responses=COMMON_AUTH_RESPONSES,
)
async def update_provider(
    provider_id: str,
    payload: ProviderUpdateSchema,
    _: Annotated[UserDocument, Depends(require_permissions(Permission.PROVIDER_UPDATE))],
) -> ProviderResponseSchema:
    return provider_to_response(await service.update(provider_id, payload))


@router.delete(
    "/{provider_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=COMMON_AUTH_RESPONSES,
)
async def delete_provider(
    provider_id: str,
    _: Annotated[UserDocument, Depends(require_permissions(Permission.PROVIDER_DELETE))],
) -> None:
    await service.delete(provider_id)
