"""Administración de números de WhatsApp conectados (Cloud API / Coexistence).

No implementa el intercambio OAuth de Embedded Signup (requiere app_id/
config_id de Meta, pendientes del trámite en Meta for Developers). Una vez
completado ese trámite, este endpoint permite registrar el `phone_number_id`
resultante sin tocar código: el resolver (`WhatsAppIntegrationService`) lo
usará automáticamente para enrutar mensajes entrantes y salientes de ese
número.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_whatsapp_integration_service, require_permissions
from app.channels.whatsapp.integration_service import WhatsAppIntegrationService
from app.common.enums import Permission
from app.documents import UserDocument, WhatsAppIntegrationDocument
from app.schemas.whatsapp import (
    WhatsAppIntegrationCreateSchema,
    WhatsAppIntegrationResponseSchema,
)

router = APIRouter(prefix="/integrations/whatsapp", tags=["WhatsApp Integrations"])


def _to_response(integration: WhatsAppIntegrationDocument) -> WhatsAppIntegrationResponseSchema:
    return WhatsAppIntegrationResponseSchema(
        id=str(integration.id),
        business_id=integration.business_id,
        waba_id=integration.waba_id,
        phone_number_id=integration.phone_number_id,
        display_phone_number=integration.display_phone_number,
        verified_name=integration.verified_name,
        connection_mode=integration.connection_mode,
        status=integration.status,
        is_default=integration.is_default,
        is_enabled=integration.is_enabled,
        coexistence_enabled=integration.coexistence_enabled,
        webhook_subscribed=integration.webhook_subscribed,
        last_validated_at=integration.last_validated_at,
        last_error_message=integration.last_error_message,
        created_at=integration.created_at,
        updated_at=integration.updated_at,
    )


@router.get("", response_model=list[WhatsAppIntegrationResponseSchema])
async def list_integrations(
    _: Annotated[UserDocument, Depends(require_permissions(Permission.WHATSAPP_INTEGRATION_READ))],
    service: WhatsAppIntegrationService = Depends(get_whatsapp_integration_service),
) -> list[WhatsAppIntegrationResponseSchema]:
    integrations = await service.list_integrations()
    return [_to_response(i) for i in integrations]


@router.post("", response_model=WhatsAppIntegrationResponseSchema, status_code=status.HTTP_201_CREATED)
async def register_integration(
    payload: WhatsAppIntegrationCreateSchema,
    current_user: Annotated[
        UserDocument, Depends(require_permissions(Permission.WHATSAPP_INTEGRATION_MANAGE))
    ],
    service: WhatsAppIntegrationService = Depends(get_whatsapp_integration_service),
) -> WhatsAppIntegrationResponseSchema:
    try:
        integration = await service.register_integration(
            phone_number_id=payload.phone_number_id,
            waba_id=payload.waba_id,
            business_id=payload.business_id,
            display_phone_number=payload.display_phone_number,
            verified_name=payload.verified_name,
            connection_mode=payload.connection_mode,
            access_token=payload.access_token,
            api_version=payload.api_version,
            is_default=payload.is_default,
            connected_by_user_id=str(current_user.id),
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return _to_response(integration)


@router.post("/{integration_id}/set-default", response_model=WhatsAppIntegrationResponseSchema)
async def set_default_integration(
    integration_id: str,
    _: Annotated[
        UserDocument, Depends(require_permissions(Permission.WHATSAPP_INTEGRATION_MANAGE))
    ],
    service: WhatsAppIntegrationService = Depends(get_whatsapp_integration_service),
) -> WhatsAppIntegrationResponseSchema:
    try:
        integration = await service.set_default(integration_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return _to_response(integration)


@router.post("/{integration_id}/disconnect", response_model=WhatsAppIntegrationResponseSchema)
async def disconnect_integration(
    integration_id: str,
    _: Annotated[
        UserDocument, Depends(require_permissions(Permission.WHATSAPP_INTEGRATION_MANAGE))
    ],
    service: WhatsAppIntegrationService = Depends(get_whatsapp_integration_service),
) -> WhatsAppIntegrationResponseSchema:
    try:
        integration = await service.disconnect(integration_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return _to_response(integration)
