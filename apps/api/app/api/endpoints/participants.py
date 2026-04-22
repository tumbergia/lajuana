from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import require_permissions
from app.api.docs import COMMON_AUTH_RESPONSES
from app.common.enums import Permission
from app.documents import UserDocument
from app.schemas.participant import ParticipantResponseSchema, ParticipantUpdateSchema
from app.services import ParticipantService
from app.services.mappers import participant_to_response

router = APIRouter(prefix="/participants", tags=["Participants"])
service = ParticipantService()


@router.get(
    "/{participant_id}",
    response_model=ParticipantResponseSchema,
    summary="Consultar participante",
    description="Retorna detalle de participante.",
    operation_id="getParticipantById",
    responses=COMMON_AUTH_RESPONSES,
)
async def get_participant(
    participant_id: str,
    _: Annotated[UserDocument, Depends(require_permissions(Permission.PARTICIPANT_READ))],
) -> ParticipantResponseSchema:
    doc = await service.get(participant_id)
    return participant_to_response(doc)


@router.patch("/{participant_id}", response_model=ParticipantResponseSchema)
async def update_participant(
    participant_id: str,
    payload: ParticipantUpdateSchema,
    _: Annotated[UserDocument, Depends(require_permissions(Permission.PARTICIPANT_UPDATE))],
) -> ParticipantResponseSchema:
    doc = await service.update(participant_id, payload)
    return participant_to_response(doc)
