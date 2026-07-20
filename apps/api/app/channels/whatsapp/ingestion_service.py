from datetime import UTC, datetime

from app.channels.whatsapp.integration_service import WhatsAppIntegrationService
from app.channels.whatsapp.normalizer import build_conversation_id
from app.channels.whatsapp.parser import parse_whatsapp_payload
from app.conversations.documents import WhatsAppInboundEventDocument
from app.conversations.services.conversation_resolver import ConversationResolver
from app.conversations.services.message_buffer_service import MessageBufferService
from app.core.logging import logger


class WhatsAppIngestionService:
    def __init__(
        self,
        resolver: ConversationResolver,
        buffer_service: MessageBufferService,
        integration_service: WhatsAppIntegrationService | None = None,
    ) -> None:
        self._resolver = resolver
        self._buffer_service = buffer_service
        self._integration_service = integration_service or WhatsAppIntegrationService()

    async def ingest(self, payload: dict) -> int:
        parsed_messages = parse_whatsapp_payload(payload)

        if not parsed_messages:
            return 0

        ingested_count = 0

        for parsed in parsed_messages:
            integration = await self._integration_service.resolve_by_phone_number_id(
                parsed.phone_number_id
            )

            if not self._integration_service.is_usable(integration):
                # Número de negocio no registrado (o desactivado): se audita
                # el evento para no perder trazabilidad ni reprocesarlo en
                # reintentos de Meta, pero no se lanza el asistente.
                collection = WhatsAppInboundEventDocument.get_motor_collection()
                await collection.update_one(
                    {"wa_message_id": parsed.wa_message_id},
                    {
                        "$setOnInsert": {
                            "wa_message_id": parsed.wa_message_id,
                            "from_phone": parsed.from_phone,
                            "normalized_phone": parsed.normalized_phone,
                            "conversation_id": build_conversation_id(
                                "whatsapp", parsed.normalized_phone
                            ),
                            "message_type": parsed.message_type,
                            "body": parsed.body,
                            "media_id": parsed.media_id,
                            "caption": parsed.caption,
                            "phone_number_id": parsed.phone_number_id,
                            "integration_id": (str(integration.id) if integration else None),
                            "status": "unregistered_integration",
                            "raw_payload": parsed.raw_payload,
                            "received_at": datetime.now(UTC),
                        }
                    },
                    upsert=True,
                )
                logger.warning(
                    "[ingestion] Skipped message for unregistered/disabled integration | "
                    "phone_number_id=%s | wa_message_id=%s",
                    parsed.phone_number_id,
                    parsed.wa_message_id,
                )
                continue

            assert integration is not None  # garantizado por is_usable() arriba

            conversation_id = build_conversation_id(
                "whatsapp",
                parsed.normalized_phone,
                phone_number_id=integration.phone_number_id,
                is_default=integration.is_default,
            )

            await self._resolver.resolve(
                channel="whatsapp",
                normalized_phone=parsed.normalized_phone,
                integration_id=str(integration.id),
                phone_number_id=integration.phone_number_id,
                is_default_integration=integration.is_default,
            )

            provider_ts = None
            if parsed.provider_timestamp:
                try:
                    provider_ts = datetime.fromtimestamp(int(parsed.provider_timestamp), tz=UTC)
                except (ValueError, OSError):
                    provider_ts = None

            collection = WhatsAppInboundEventDocument.get_motor_collection()
            result = await collection.update_one(
                {"wa_message_id": parsed.wa_message_id},
                {
                    "$setOnInsert": {
                        "wa_message_id": parsed.wa_message_id,
                        "from_phone": parsed.from_phone,
                        "normalized_phone": parsed.normalized_phone,
                        "conversation_id": conversation_id,
                        "message_type": parsed.message_type,
                        "body": parsed.body,
                        "media_id": parsed.media_id,
                        "caption": parsed.caption,
                        "provider_timestamp": provider_ts,
                        "integration_id": str(integration.id),
                        "phone_number_id": integration.phone_number_id,
                        "status": "received",
                        "raw_payload": parsed.raw_payload,
                        "received_at": datetime.now(UTC),
                    }
                },
                upsert=True,
            )

            if result.upserted_id is None:
                logger.info(
                    "[ingestion] Duplicate ignored | wa_message_id=%s",
                    parsed.wa_message_id,
                )
                continue

            body = parsed.body or ""
            if parsed.message_type == "audio":
                body = "[Audio recibido pendiente de transcripción]"
            elif parsed.media_id and parsed.message_type != "text":
                body = parsed.caption or f"[{parsed.message_type} recibido]"

            await self._buffer_service.add_message(
                conversation_id=conversation_id,
                normalized_phone=parsed.normalized_phone,
                channel="whatsapp",
                message_id=parsed.wa_message_id,
                body=body,
            )

            ingested_count += 1

        logger.info("[ingestion] Ingested %d message(s)", ingested_count)
        return ingested_count
