from fastapi import APIRouter

from app.schemas.participant import ParticipantResponseSchema, ParticipantUpdateSchema
from app.services import ParticipantService
from app.services.mappers import participant_to_response

router = APIRouter(prefix="/participants", tags=["participants"])
service = ParticipantService()


@router.patch("/{participant_id}", response_model=ParticipantResponseSchema)
async def update_participant(
    participant_id: str, payload: ParticipantUpdateSchema
) -> ParticipantResponseSchema:
    doc = await service.update(participant_id, payload)
    return participant_to_response(doc)
