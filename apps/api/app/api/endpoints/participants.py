import base64
import io
from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.responses import StreamingResponse

from app.api.deps import require_permissions
from app.api.docs import ENDPOINT_DOCS, endpoint_description, endpoint_responses
from app.common.enums import Permission
from app.common.labels import ErrorCode
from app.core.errors import ApiError
from app.documents import LiabilityReleaseDocument, UserDocument
from app.schemas.participant import ParticipantResponseSchema, ParticipantUpdateSchema
from app.services import ParticipantService
from app.services.mappers import participant_to_response

router = APIRouter(prefix="/participants", tags=["Participantes"])
service = ParticipantService()


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
) -> ParticipantResponseSchema:
    doc = await service.update(participant_id, payload)
    return participant_to_response(doc)


@router.get(
    "/{participant_id}/liability-release/download",
    response_model=None,
    status_code=status.HTTP_200_OK,
    summary="Descargar liberacion de responsabilidad en PDF",
    description="Descarga el documento PDF de la liberacion de responsabilidad firmada por el participante.",
    operation_id="downloadLiabilityReleasePdf",
)
async def download_liability_release_pdf(
    participant_id: str,
    _: Annotated[UserDocument, Depends(require_permissions(Permission.PARTICIPANT_READ))],
):
    liability = await LiabilityReleaseDocument.find_one({"participant_id": participant_id})
    if liability is None:
        raise ApiError(
            status_code=404,
            code=ErrorCode.PARTICIPANT_NOT_FOUND,
            message="No se encontro la liberacion de responsabilidad para este participante.",
        )

    pdf_bytes = base64.b64decode(liability.pdf_base64)
    filename = f"liberacion-responsabilidad-{participant_id}.pdf"
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )
