from datetime import UTC, datetime

import httpx

from app.channels.whatsapp.integration_service import WhatsAppIntegrationService
from app.channels.whatsapp.normalizer import strip_whatsapp_markup
from app.conversations.documents import OutboundMessageDocument
from app.core.config import settings
from app.core.logging import logger
from app.documents.conversation_turn_document import ConversationTurnDocument


class WhatsAppOutboundService:
    def __init__(self, integration_service: WhatsAppIntegrationService | None = None) -> None:
        # Si no se inyecta un integration_service, el envío usa directamente
        # settings.* como antes (comportamiento legacy, usado en tests y en
        # llamadas que aún no pasan por el flujo multi-número).
        self._integration_service = integration_service

    async def send(
        self,
        *,
        turn: ConversationTurnDocument,
        to_phone: str,
        text: str,
        integration_id: str | None = None,
    ) -> OutboundMessageDocument:
        # WhatsApp renderiza * _ ~ y `, que el LLM puede emitir y rompe la lectura
        # con saltos de línea raros. Saneamos antes de enviar para garantizar texto plano.
        clean_text = strip_whatsapp_markup(text)

        resolved_integration_id: str | None = None
        phone_number_id = settings.whatsapp_phone_number_id
        access_token = settings.whatsapp_access_token
        api_version = settings.whatsapp_api_version

        if self._integration_service is not None:
            integration = (
                await self._integration_service.resolve_by_id(integration_id)
                if integration_id
                else await self._integration_service.resolve_default()
            )
            if integration is not None:
                credentials = self._integration_service.get_send_credentials(integration)
                resolved_integration_id = credentials.integration_id
                phone_number_id = credentials.phone_number_id
                access_token = credentials.access_token
                api_version = credentials.api_version

        outbound = OutboundMessageDocument(
            conversation_id=turn.conversation_id or "",
            turn_id=str(turn.id),
            to_phone=to_phone,
            body=clean_text,
            integration_id=resolved_integration_id,
            status="queued",
        )
        await outbound.insert()

        if not settings.whatsapp_send_enabled:
            return outbound

        if not access_token or not phone_number_id:
            outbound.status = "failed"
            outbound.error = "missing_credentials"
            await outbound.save()
            return outbound

        clean_phone = to_phone.lstrip("+")
        url = f"https://graph.facebook.com/{api_version}/{phone_number_id}/messages"

        payload = {
            "messaging_product": "whatsapp",
            "to": clean_phone,
            "type": "text",
            "text": {"body": clean_text},
        }

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=15) as client:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                data = response.json()
                provider_id = (
                    (data.get("messages") or [{}])[0].get("id") if data.get("messages") else None
                )
                outbound.provider_message_id = provider_id
                outbound.status = "sent"
                outbound.sent_at = datetime.now(UTC)
                await outbound.save()
                logger.info(
                    "[outbound] Sent | to=%s | outbound_id=%s",
                    to_phone,
                    outbound.outbound_id,
                )
        except Exception as exc:
            outbound.status = "failed"
            outbound.error = str(exc)
            await outbound.save()
            logger.error("[outbound] Send failed | to=%s | error=%s", to_phone, exc)
            if self._integration_service is not None and isinstance(exc, httpx.HTTPStatusError):
                if exc.response.status_code in (401, 403):
                    await self._integration_service.mark_degraded(
                        resolved_integration_id, str(exc)
                    )

        return outbound
