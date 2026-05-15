from fastapi import APIRouter, status

from app.api.docs import ENDPOINT_DOCS, endpoint_description, endpoint_responses
from app.schemas.participant import (
    ParticipantFormCreateResponse,
    ParticipantFormInfoSchema,
    ParticipantPublicCreateSchema,
)
from app.services import ParticipantFormService

router = APIRouter(prefix="/public/participant-form", tags=["Participantes - Formulario público"])
service = ParticipantFormService()


@router.get(
    "/{token}",
    response_model=ParticipantFormInfoSchema,
    summary=ENDPOINT_DOCS["participant_form_info"]["summary"],
    description=endpoint_description("participant_form_info"),
    operation_id="getParticipantFormInfo",
    responses=endpoint_responses("participant_form_info"),
)
async def get_participant_form_info(
    token: str,
) -> ParticipantFormInfoSchema:
    return await service.get_form_info(token)


@router.post(
    "/{token}",
    response_model=ParticipantFormCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary=ENDPOINT_DOCS["participant_form_register"]["summary"],
    description=endpoint_description("participant_form_register"),
    operation_id="registerParticipantFromForm",
    responses=endpoint_responses("participant_form_register"),
)
async def register_participant_from_form(
    token: str,
    payload: ParticipantPublicCreateSchema,
) -> ParticipantFormCreateResponse:
    return await service.register_participant(token, payload)
