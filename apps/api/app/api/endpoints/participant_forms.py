from typing import Annotated

from fastapi import APIRouter, Depends, Request, status

from app.api.deps import (
    get_notification_service,
    get_participant_form_link_service,
    get_participant_service,
    require_permissions,
)
from app.common.enums import Permission
from app.core.config import settings
from app.documents import ExperienceDocument, ReservationDocument, UserDocument
from app.schemas.participant import (
    ParticipantNestedCreateSchema,
    ParticipantPublicCreateSchema,
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
from app.services.notification_service import NotificationService
from app.services.participant_form_link_service import ParticipantFormLinkService

router = APIRouter()


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
    form_link_service: ParticipantFormLinkService = Depends(get_participant_form_link_service),
) -> ParticipantFormTokenValidationResponse:
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
        participant_limit=doc.max_participants,
        participants_registered=doc.used_count,
        participants_remaining=max(0, doc.max_participants - doc.used_count),
    )


@router.get(
    "/public/participant-form/{token}",
    response_model=ParticipantFormTokenValidationResponse,
    summary="Validar token (formato Vercel)",
    description=(
        "Alias compatible con el frontend desplegado en Vercel. Valida el token del formulario."
    ),
    operation_id="validateParticipantFormTokenVercel",
    tags=["Formulario de participantes"],
)
async def validate_participant_form_token_vercel(
    token: str,
    form_link_service: ParticipantFormLinkService = Depends(get_participant_form_link_service),
) -> ParticipantFormTokenValidationResponse:
    """Reenvía a la lógica del endpoint /validate estándar."""
    return await validate_participant_form_token(token, form_link_service)


@router.post(
    "/public/participant-form/{token}",
    response_model=ParticipantResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar participante (formato Vercel)",
    description=(
        "Alias compatible con el frontend desplegado en Vercel. "
        "Crea un participante mediante el token del formulario."
    ),
    operation_id="createParticipantViaFormVercel",
    tags=["Formulario de participantes"],
)
async def create_participant_via_form_vercel(
    token: str,
    payload: ParticipantPublicCreateSchema,
    request: Request,
    participant_service: ParticipantService = Depends(get_participant_service),
) -> ParticipantResponseSchema:
    """Reenvía a la lógica del endpoint /participants estándar."""
    return await create_participant_via_form(token, payload, request, participant_service)


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
    form_link_service: ParticipantFormLinkService = Depends(get_participant_form_link_service),
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
async def create_participant_via_form_route(
    token: str,
    payload: ParticipantPublicCreateSchema,
    request: Request,
    participant_service: ParticipantService = Depends(get_participant_service),
) -> ParticipantResponseSchema:
    return await create_participant_via_form(token, payload, request, participant_service)


def _convert_public_to_nested(
    payload: ParticipantPublicCreateSchema,
) -> ParticipantNestedCreateSchema:
    """Convert flat frontend fields to the nested schema expected by the service."""
    eps = payload.eps or payload.travel_insurance or None
    return ParticipantNestedCreateSchema(
        first_name=payload.first_name,
        last_name=payload.last_name,
        email=payload.email,
        birth_date=payload.birth_date,
        document_type=payload.document_type,
        document_number=payload.document_number,
        phone=payload.phone,
        country=payload.country,
        city=payload.city,
        height_cm=payload.height_cm,
        weight_kg=payload.weight_kg,
        experience_level=payload.experience_level,
        dietary_restrictions=payload.dietary_restrictions,
        blood_type=payload.blood_type,
        eps_or_travel_insurance=eps,
        health_conditions=payload.medical_conditions,
        sensory_disabilities=payload.functional_conditions,
        emergency_contact={
            "name": payload.emergency_contact_name,
            "phone": payload.emergency_contact_phone,
            "relationship": payload.emergency_contact_relationship,
            "country": payload.emergency_contact_country,
        },
        accepted_data_processing=payload.accepted_data_processing,
        accepted_media_usage=payload.accepted_media_usage,
        accepted_risk_release=payload.accepted_risk_release,
        risk_release_text_version=payload.risk_release_text_version,
    )


async def create_participant_via_form(
    token: str,
    payload: ParticipantPublicCreateSchema,
    request: Request,
    participant_service: ParticipantService,
) -> ParticipantResponseSchema:
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    nested = _convert_public_to_nested(payload)
    doc = await participant_service.create_from_form(
        token, nested, ip_address=ip_address, user_agent=user_agent
    )
    return participant_to_response(doc)


@router.get(
    "/public/participant-forms/risk-release-text",
    summary="Obtener texto de liberación de responsabilidad",
    description="Retorna el texto vigente de liberación de responsabilidad y asunción de riesgos.",
    operation_id="getRiskReleaseText",
    tags=["Formulario de participantes"],
)
async def get_risk_release_text(
    participant_service: ParticipantService = Depends(get_participant_service),
) -> dict:
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
    form_link_service: ParticipantFormLinkService = Depends(get_participant_form_link_service),
) -> ParticipantFormLinkGenerateResponse:
    doc, raw_token = await form_link_service.generate(
        reservation_id=reservation_id,
        expected_participants_count=payload.expected_participants_count,
    )
    form_url = f"{settings.participant_form_base_url}/?token={raw_token}"
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
    form_link_service: ParticipantFormLinkService = Depends(get_participant_form_link_service),
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
    notification_service: NotificationService = Depends(get_notification_service),
) -> ReservationResponseSchema:
    reservation = await ReservationDocument.get(reservation_id)
    if reservation is None:
        from app.common.labels import ErrorCode
        from app.core.errors import ApiError

        raise ApiError(
            status_code=404,
            code=ErrorCode.RESERVATION_NOT_FOUND,
            message="Reserva no encontrada.",
        )

    experience = await ExperienceDocument.get(reservation.experience_id)
    await notification_service.enqueue_participant_form_resent(
        reservation=reservation,
        experience_name=experience.name if experience else "",
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
    form_link_service: ParticipantFormLinkService = Depends(get_participant_form_link_service),
) -> ParticipantFormLinkStatusResponse | None:
    doc = await form_link_service.get_link_by_reservation(reservation_id)
    if doc is None:
        return None
    return form_link_to_status_response(doc)
