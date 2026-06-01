from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import get_participant_service, require_permissions
from app.api.docs import ENDPOINT_DOCS, endpoint_description, endpoint_responses
from app.common.enums import Permission
from app.documents import UserDocument
from app.schemas.participant import ParticipantResponseSchema, ParticipantUpdateSchema
from app.services import ParticipantService
from app.services.mappers import participant_to_response

router = APIRouter(prefix="/participants", tags=["Participantes"])


@router.get(
    "/{participant_id}",
    response_model=ParticipantResponseSchema,
    summary=ENDPOINT_DOCS["participants_get"]["summary"],
    description=endpoint_description("participants_get"),
    operation_id="getParticipantById",
    responses=endpoint_responses("participants_get"),
)
async def get_participant(
    participant_id: str,
    _: Annotated[UserDocument, Depends(require_permissions(Permission.PARTICIPANT_READ))],
    service: ParticipantService = Depends(get_participant_service),
) -> ParticipantResponseSchema:
    doc = await service.get(participant_id)
    return participant_to_response(doc)


@router.patch(
    "/{participant_id}",
    response_model=ParticipantResponseSchema,
    summary=ENDPOINT_DOCS["participants_update"]["summary"],
    description=endpoint_description("participants_update"),
    operation_id="updateParticipantById",
    responses=endpoint_responses("participants_update"),
)
async def update_participant(
    participant_id: str,
    payload: ParticipantUpdateSchema,
    _: Annotated[UserDocument, Depends(require_permissions(Permission.PARTICIPANT_UPDATE))],
    service: ParticipantService = Depends(get_participant_service),
) -> ParticipantResponseSchema:
    doc = await service.update(participant_id, payload)
    return participant_to_response(doc)
