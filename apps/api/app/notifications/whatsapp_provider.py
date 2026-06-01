from __future__ import annotations

from uuid import uuid4

from app.channels.whatsapp.normalizer import build_conversation_id
from app.channels.whatsapp.outbound_service import WhatsAppOutboundService
from app.common.enums import NotificationChannel
from app.core.logging import logger
from app.documents.conversation_turn_document import ConversationTurnDocument
from app.documents.notification_outbox_document import NotificationOutboxDocument
from app.notifications.provider import NotificationProvider, SendResult


class WhatsAppNotificationProvider(NotificationProvider):
    channel = NotificationChannel.WHATSAPP

    def __init__(self, outbound_service: WhatsAppOutboundService) -> None:
        self._outbound = outbound_service

    async def send(self, entry: NotificationOutboxDocument) -> SendResult:
        to_phone = entry.recipient_identifier
        body = entry.rendered_body
        if not body:
            return SendResult(success=False, error_detail="No rendered body")

        conversation_id = build_conversation_id("whatsapp", to_phone)
        turn = ConversationTurnDocument(
            trace_id=str(uuid4()),
            channel="whatsapp",
            from_phone=to_phone,
            user_message="(notification outbox)",
            conversation_id=conversation_id,
        )
        await turn.insert()

        try:
            result = await self._outbound.send(
                turn=turn,
                to_phone=to_phone,
                text=body,
            )
            return SendResult(
                success=result.status == "sent",
                provider_message_id=result.provider_message_id,
            )
        except Exception as exc:
            logger.error(
                "[outbox=%s] WhatsApp send failed | event=%s | error=%s",
                entry.id,
                entry.event_type,
                exc,
            )
            return SendResult(
                success=False,
                error_detail=str(exc),
            )

    async def validate_config(self) -> bool:
        from app.core.config import settings
        return bool(settings.whatsapp_access_token and settings.whatsapp_phone_number_id)
