from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.deps import require_permissions
from app.api.docs import COMMON_AUTH_RESPONSES
from app.common.enums import Permission
from app.documents import UserDocument
from app.schemas.experience import (
    ExperienceCreateSchema,
    ExperienceResponseSchema,
    ExperienceUpdateSchema,
)
from app.services import ExperienceService
from app.services.mappers import experience_to_response

router = APIRouter(prefix="/experiences", tags=["Experiences"])
service = ExperienceService()


@router.post(
    "",
    response_model=ExperienceResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Crear experiencia",
    description="Crea una experiencia del catálogo operativo.",
    operation_id="createExperience",
    responses=COMMON_AUTH_RESPONSES,
)
async def create_experience(
    payload: ExperienceCreateSchema,
    _: Annotated[UserDocument, Depends(require_permissions(Permission.EXPERIENCE_CREATE))],
) -> ExperienceResponseSchema:
    doc = await service.create(payload)
    return experience_to_response(doc)


@router.get(
    "",
    response_model=list[ExperienceResponseSchema],
    summary="Listar experiencias",
    description="Lista experiencias del catálogo.",
    operation_id="listExperiences",
    responses=COMMON_AUTH_RESPONSES,
)
async def list_experiences(
    _: Annotated[UserDocument, Depends(require_permissions(Permission.EXPERIENCE_READ))],
    is_active: bool | None = None,
) -> list[ExperienceResponseSchema]:
    docs = await service.list(is_active=is_active)
    return [experience_to_response(doc) for doc in docs]


@router.get(
    "/{experience_id}",
    response_model=ExperienceResponseSchema,
    summary="Consultar experiencia",
    description="Obtiene detalle de experiencia.",
    operation_id="getExperienceById",
    responses=COMMON_AUTH_RESPONSES,
)
async def get_experience(
    experience_id: str,
    _: Annotated[UserDocument, Depends(require_permissions(Permission.EXPERIENCE_READ))],
) -> ExperienceResponseSchema:
    doc = await service.get(experience_id)
    return experience_to_response(doc)


@router.patch(
    "/{experience_id}",
    response_model=ExperienceResponseSchema,
    summary="Actualizar experiencia",
    description="Actualiza datos de experiencia del catálogo.",
    operation_id="updateExperienceById",
    responses=COMMON_AUTH_RESPONSES,
)
async def update_experience(
    experience_id: str,
    payload: ExperienceUpdateSchema,
    _: Annotated[UserDocument, Depends(require_permissions(Permission.EXPERIENCE_UPDATE))],
) -> ExperienceResponseSchema:
    doc = await service.update(experience_id, payload)
    return experience_to_response(doc)
