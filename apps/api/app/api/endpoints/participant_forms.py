from typing import Annotated

from fastapi import APIRouter, Depends, Request, status

from app.api.deps import require_permissions
from app.common.enums import Permission
from app.core.config import settings
from app.documents import ExperienceDocument, ReservationDocument, UserDocument
from app.notifications.reservation_whatsapp_notification_service import (
    ReservationWhatsAppNotificationService,
)
from app.schemas.participant import (
    ParticipantNestedCreateSchema,
    ParticipantResponseSchema,
)
from app.schemas.participant_form_link import (
    ParticipantFormLinkGenerateRequest,
    ParticipantFormLinkGenerateResponse,
    ParticipantFormLinkStatusResponse,
    ParticipantFormPublicStatusResponse,
    ParticipantFormTokenValidationResponse,
)
from app.schemas.reservation import ReservationResponseSchema
from app.services import ParticipantService
from app.services.mappers import (
    form_link_to_status_response,
    participant_to_response,
    reservation_to_response,
)
from app.services.participant_form_link_service import ParticipantFormLinkService

router = APIRouter()
form_link_service = ParticipantFormLinkService()
participant_service = ParticipantService()


@router.get(
    "/public/participant-forms/{token}/validate",
    response_model=ParticipantFormTokenValidationResponse,
    summary="Validar token del formulario",
    description="Valida que un token de formulario sea válido, no haya expirado y tenga cupos.",
    operation_id="validateParticipantFormToken",
    tags=["Formulario de participantes"],
)
async def validate_participant_form_token(
    token: str,
) -> ParticipantFormTokenValidationResponse:
    try:
        doc = await form_link_service.validate_token(token)
        reservation = await ReservationDocument.get(doc.reservation_id)
        experience_name = None
        reservation_code = None
        if reservation is not None:
            reservation_code = reservation.code
            experience = await ExperienceDocument.get(reservation.experience_id)
            if experience is not None:
                experience_name = experience.name

        return ParticipantFormTokenValidationResponse(
            valid=True,
            reservation_code=reservation_code,
            experience_name=experience_name,
            expires_at=doc.expires_at,
            max_participants=doc.max_participants,
            used_count=doc.used_count,
        )
    except Exception:
        return ParticipantFormTokenValidationResponse(valid=False)


@router.get(
    "/public/participant-forms/{token}/status",
    response_model=ParticipantFormPublicStatusResponse,
    summary="Estado público del formulario",
    description=(
        "Retorna estado agregado del formulario: completados y esperados, sin datos sensibles."
    ),
    operation_id="getPublicParticipantFormStatus",
    tags=["Formulario de participantes"],
)
async def get_public_participant_form_status(
    token: str,
) -> ParticipantFormPublicStatusResponse:
    status_data = await form_link_service.get_public_status(token)
    return ParticipantFormPublicStatusResponse(**status_data)


@router.post(
    "/public/participant-forms/{token}/participants",
    response_model=ParticipantResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar participante desde formulario público",
    description=(
        "Crea un participante asociado a la reserva mediante un token válido del formulario."
    ),
    operation_id="createParticipantViaForm",
    tags=["Formulario de participantes"],
)
async def create_participant_via_form(
    token: str,
    payload: ParticipantNestedCreateSchema,
    request: Request,
) -> ParticipantResponseSchema:
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    doc = await participant_service.create_from_form(
        token, payload, ip_address=ip_address, user_agent=user_agent
    )
    return participant_to_response(doc)


@router.get(
    "/public/participant-forms/risk-release-text",
    summary="Obtener texto de liberación de responsabilidad",
    description="Retorna el texto vigente de liberación de responsabilidad y asunción de riesgos.",
    operation_id="getRiskReleaseText",
    tags=["Formulario de participantes"],
)
async def get_risk_release_text() -> dict:
    return {"risk_release_text": participant_service.get_risk_release_text()}


@router.post(
    "/reservations/{reservation_id}/participant-form-link",
    response_model=ParticipantFormLinkGenerateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generar enlace de formulario",
    description=(
        "Genera un enlace temporal para que los participantes de una reserva "
        "confirmada diligencien sus datos. El enlace expira en 48 horas. "
        "No requiere autenticación; la reserva debe estar confirmada."
    ),
    operation_id="generateParticipantFormLink",
    tags=["Formulario de participantes"],
)
async def generate_participant_form_link(
    reservation_id: str,
    payload: ParticipantFormLinkGenerateRequest,
) -> ParticipantFormLinkGenerateResponse:
    doc, raw_token = await form_link_service.generate(
        reservation_id=reservation_id,
        expected_participants_count=payload.expected_participants_count,
    )
    form_url = (
        f"{settings.app_base_url}"
        f"/formulario-participantes?t={raw_token}"
    )
    return ParticipantFormLinkGenerateResponse(
        id=str(doc.id),
        reservation_id=str(doc.reservation_id),
        token=raw_token,
        expires_at=doc.expires_at,
        max_participants=doc.max_participants,
        form_url=form_url,
    )


@router.post(
    "/reservations/{reservation_id}/participant-form-link/revoke",
    response_model=ParticipantFormLinkStatusResponse,
    summary="Revocar enlace de formulario",
    description="Revoca manualmente un enlace de formulario activo. No requiere autenticación.",
    operation_id="revokeParticipantFormLink",
    tags=["Formulario de participantes"],
)
async def revoke_participant_form_link(
    reservation_id: str,
) -> ParticipantFormLinkStatusResponse:
    doc = await form_link_service.revoke(reservation_id)
    return form_link_to_status_response(doc)


@router.post(
    "/reservations/{reservation_id}/participant-form-link/resend",
    response_model=ReservationResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Reenviar formulario de participantes por WhatsApp",
    description=(
        "Reenvía manualmente el enlace del formulario de participantes "
        "al titular de la reserva vía WhatsApp. Solo administradores."
    ),
    operation_id="resendParticipantFormLink",
    tags=["Formulario de participantes"],
)
async def resend_participant_form_link(
    reservation_id: str,
    current_user: Annotated[UserDocument, Depends(require_permissions(Permission.PAYMENT_VERIFY))],
) -> ReservationResponseSchema:
    reservation = await ReservationDocument.get(reservation_id)
    if reservation is None:
        from app.core.errors import ApiError
        from app.common.labels import ErrorCode

        raise ApiError(
            status_code=404,
            code=ErrorCode.RESERVATION_NOT_FOUND,
            message="Reserva no encontrada.",
        )

    whatsapp_notif = ReservationWhatsAppNotificationService()
    await whatsapp_notif.resend_participant_form(
        reservation=reservation,
        actor_id=current_user.id,
    )
    return await reservation_to_response(reservation)


@router.get(
    "/reservations/{reservation_id}/participant-form-link",
    response_model=ParticipantFormLinkStatusResponse | None,
    summary="Consultar enlace de formulario",
    description="Retorna el estado del enlace de formulario activo o el último generado.",
    operation_id="getParticipantFormLinkStatus",
    tags=["Formulario de participantes"],
)
async def get_participant_form_link_status(
    reservation_id: str,
) -> ParticipantFormLinkStatusResponse | None:
    doc = await form_link_service.get_link_by_reservation(reservation_id)
    if doc is None:
        return None
    return form_link_to_status_response(doc)
