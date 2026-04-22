from fastapi import APIRouter

from app.schemas.experience import (
    ExperienceCreateSchema,
    ExperienceResponseSchema,
    ExperienceUpdateSchema,
)
from app.services import ExperienceService
from app.services.mappers import experience_to_response

router = APIRouter(prefix="/experiences", tags=["experiences"])
service = ExperienceService()


@router.post("", response_model=ExperienceResponseSchema, status_code=201)
async def create_experience(payload: ExperienceCreateSchema) -> ExperienceResponseSchema:
    doc = await service.create(payload)
    return experience_to_response(doc)


@router.get("", response_model=list[ExperienceResponseSchema])
async def list_experiences(is_active: bool | None = None) -> list[ExperienceResponseSchema]:
    docs = await service.list(is_active=is_active)
    return [experience_to_response(doc) for doc in docs]


@router.get("/{experience_id}", response_model=ExperienceResponseSchema)
async def get_experience(experience_id: str) -> ExperienceResponseSchema:
    doc = await service.get(experience_id)
    return experience_to_response(doc)


@router.patch("/{experience_id}", response_model=ExperienceResponseSchema)
async def update_experience(
    experience_id: str, payload: ExperienceUpdateSchema
) -> ExperienceResponseSchema:
    doc = await service.update(experience_id, payload)
    return experience_to_response(doc)
