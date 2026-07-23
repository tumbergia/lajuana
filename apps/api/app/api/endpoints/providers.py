"""Router de proveedores."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status

from app.api.deps import get_provider_service, require_permissions
from app.api.docs import ENDPOINT_DOCS, endpoint_description, endpoint_responses
from app.common.enums import Permission
from app.documents import ProviderStatus, ProviderType, UserDocument
from app.schemas.provider import (
    ProviderCreateSchema,
    ProviderListItemSchema,
    ProviderResponseSchema,
    ProviderUpdateSchema,
)
from app.services import ProviderService
from app.services.mappers import provider_to_list_item, provider_to_response

router = APIRouter(prefix="/providers", tags=["Proveedores"])


@router.post(
    "",
    response_model=ProviderResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary=ENDPOINT_DOCS["providers_create"]["summary"],
    description=endpoint_description("providers_create"),
    operation_id="createProvider",
    responses=endpoint_responses("providers_create"),
)
async def create_provider(
    payload: ProviderCreateSchema,
    _: Annotated[UserDocument, Depends(require_permissions(Permission.PROVIDER_CREATE))],
    service: ProviderService = Depends(get_provider_service),
) -> ProviderResponseSchema:
    return provider_to_response(await service.create(payload))


@router.get(
    "",
    response_model=list[ProviderListItemSchema],
    summary=ENDPOINT_DOCS["providers_list"]["summary"],
    description=endpoint_description("providers_list"),
    operation_id="listProviders",
    responses=endpoint_responses("providers_list"),
)
async def list_providers(
    _: Annotated[UserDocument, Depends(require_permissions(Permission.PROVIDER_READ))],
    response: Response,
    provider_type: ProviderType | None = Query(default=None, alias="type"),
    status_filter: ProviderStatus | None = Query(default=None, alias="status"),
    q: str | None = None,
    service_category: str | None = None,
    is_active: bool | None = None,
    include_deleted: bool = Query(
        default=False, description="Incluir proveedores borrados logicamente"
    ),
    limit: int = Query(default=200, ge=1, le=1000),
    skip: int = Query(default=0, ge=0),
    service: ProviderService = Depends(get_provider_service),
) -> list[ProviderListItemSchema]:
    total = await service.count(
        provider_type=provider_type,
        status=status_filter,
        q=q,
        service_category=service_category,
        is_active=is_active,
        include_deleted=include_deleted,
    )
    response.headers["X-Total-Count"] = str(total)
    return [
        provider_to_list_item(item)
        for item in await service.list(
            provider_type=provider_type,
            status=status_filter,
            q=q,
            service_category=service_category,
            is_active=is_active,
            include_deleted=include_deleted,
            limit=limit,
            skip=skip,
        )
    ]


@router.get(
    "/{provider_id}",
    response_model=ProviderResponseSchema,
    summary=ENDPOINT_DOCS["providers_get"]["summary"],
    description=endpoint_description("providers_get"),
    operation_id="getProviderById",
    responses=endpoint_responses("providers_get"),
)
async def get_provider(
    provider_id: str,
    _: Annotated[UserDocument, Depends(require_permissions(Permission.PROVIDER_READ))],
    service: ProviderService = Depends(get_provider_service),
) -> ProviderResponseSchema:
    return provider_to_response(await service.get(provider_id))


@router.patch(
    "/{provider_id}",
    response_model=ProviderResponseSchema,
    summary=ENDPOINT_DOCS["providers_update"]["summary"],
    description=endpoint_description("providers_update"),
    operation_id="updateProviderById",
    responses=endpoint_responses("providers_update"),
)
async def update_provider(
    provider_id: str,
    payload: ProviderUpdateSchema,
    _: Annotated[UserDocument, Depends(require_permissions(Permission.PROVIDER_UPDATE))],
    service: ProviderService = Depends(get_provider_service),
) -> ProviderResponseSchema:
    return provider_to_response(await service.update(provider_id, payload))


@router.delete(
    "/{provider_id}",
    status_code=status.HTTP_200_OK,
    summary=ENDPOINT_DOCS["providers_delete"]["summary"],
    description=endpoint_description("providers_delete"),
    operation_id="deactivateProviderById",
    responses=endpoint_responses("providers_delete"),
)
async def delete_provider(
    provider_id: str,
    _: Annotated[UserDocument, Depends(require_permissions(Permission.PROVIDER_DELETE))],
    service: ProviderService = Depends(get_provider_service),
) -> None:
    await service.delete(provider_id)
