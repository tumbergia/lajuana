from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status

from app.api.deps import get_experience_service, require_permissions
from app.api.docs import ENDPOINT_DOCS, endpoint_description, endpoint_responses
from app.common.enums import Permission
from app.documents import UserDocument
from app.schemas.experience import (
    ExperienceCreateSchema,
    ExperienceQuoteRequestSchema,
    ExperienceQuoteResponseSchema,
    ExperienceResponseSchema,
    ExperienceUpdateSchema,
)
from app.services import ExperienceService
from app.services.mappers import experience_to_response

router = APIRouter(prefix="/experiences", tags=["Experiencias"])


@router.post(
    "",
    response_model=ExperienceResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary=ENDPOINT_DOCS["experiences_create"]["summary"],
    description=endpoint_description("experiences_create"),
    operation_id="createExperience",
    responses=endpoint_responses("experiences_create"),
)
async def create_experience(
    payload: ExperienceCreateSchema,
    _: Annotated[UserDocument, Depends(require_permissions(Permission.EXPERIENCE_CREATE))],
    service: ExperienceService = Depends(get_experience_service),
) -> ExperienceResponseSchema:
    doc = await service.create(payload)
    return experience_to_response(doc)


@router.get(
    "",
    response_model=list[ExperienceResponseSchema],
    summary=ENDPOINT_DOCS["experiences_list"]["summary"],
    description=endpoint_description("experiences_list"),
    operation_id="listExperiences",
    responses=endpoint_responses("experiences_list"),
)
async def list_experiences(
    _: Annotated[UserDocument, Depends(require_permissions(Permission.EXPERIENCE_READ))],
    response: Response,
    is_active: bool | None = None,
    limit: int = Query(default=200, ge=1, le=1000),
    skip: int = Query(default=0, ge=0),
    service: ExperienceService = Depends(get_experience_service),
) -> list[ExperienceResponseSchema]:
    total = await service.count(is_active=is_active)
    response.headers["X-Total-Count"] = str(total)
    docs = await service.list(is_active=is_active, skip=skip, limit=limit)
    return [experience_to_response(doc) for doc in docs]


@router.get(
    "/{experience_id}",
    response_model=ExperienceResponseSchema,
    summary=ENDPOINT_DOCS["experiences_get"]["summary"],
    description=endpoint_description("experiences_get"),
    operation_id="getExperienceById",
    responses=endpoint_responses("experiences_get"),
)
async def get_experience(
    experience_id: str,
    _: Annotated[UserDocument, Depends(require_permissions(Permission.EXPERIENCE_READ))],
    service: ExperienceService = Depends(get_experience_service),
) -> ExperienceResponseSchema:
    doc = await service.get(experience_id)
    return experience_to_response(doc)


@router.patch(
    "/{experience_id}",
    response_model=ExperienceResponseSchema,
    summary=ENDPOINT_DOCS["experiences_update"]["summary"],
    description=endpoint_description("experiences_update"),
    operation_id="updateExperienceById",
    responses=endpoint_responses("experiences_update"),
)
async def update_experience(
    experience_id: str,
    payload: ExperienceUpdateSchema,
    _: Annotated[UserDocument, Depends(require_permissions(Permission.EXPERIENCE_UPDATE))],
    service: ExperienceService = Depends(get_experience_service),
) -> ExperienceResponseSchema:
    doc = await service.update(experience_id, payload)
    return experience_to_response(doc)


@router.delete(
    "/{experience_id}",
    response_model=ExperienceResponseSchema,
    summary=ENDPOINT_DOCS["experiences_delete"]["summary"],
    description=endpoint_description("experiences_delete"),
    operation_id="deactivateExperienceById",
    responses=endpoint_responses("experiences_delete"),
)
async def deactivate_experience(
    experience_id: str,
    _: Annotated[UserDocument, Depends(require_permissions(Permission.EXPERIENCE_DELETE))],
    service: ExperienceService = Depends(get_experience_service),
) -> ExperienceResponseSchema:
    doc = await service.deactivate(experience_id)
    return experience_to_response(doc)


@router.delete(
    "/{experience_id}/permanent",
    response_model=ExperienceResponseSchema,
    summary=ENDPOINT_DOCS["experiences_purge"]["summary"],
    description=endpoint_description("experiences_purge"),
    operation_id="purgeExperienceById",
    responses=endpoint_responses("experiences_purge"),
)
async def purge_experience(
    experience_id: str,
    _: Annotated[UserDocument, Depends(require_permissions(Permission.EXPERIENCE_DELETE))],
    service: ExperienceService = Depends(get_experience_service),
) -> ExperienceResponseSchema:
    doc = await service.purge(experience_id)
    return experience_to_response(doc)


@router.post(
    "/{experience_id}/quote",
    response_model=ExperienceQuoteResponseSchema,
    summary="Cotizar experiencia",
    description=(
        "Calcula la cotizacion oficial para una experiencia segun cantidad "
        "de participantes y tabla tarifaria vigente."
    ),
    operation_id="quoteExperienceById",
)
async def quote_experience(
    experience_id: str,
    payload: ExperienceQuoteRequestSchema,
    _: Annotated[UserDocument, Depends(require_permissions(Permission.EXPERIENCE_READ))],
    service: ExperienceService = Depends(get_experience_service),
) -> ExperienceQuoteResponseSchema:
    return await service.quote(experience_id, payload)
