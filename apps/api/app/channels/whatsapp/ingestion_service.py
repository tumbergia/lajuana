from datetime import UTC, datetime

from app.channels.whatsapp.normalizer import build_conversation_id
from app.channels.whatsapp.parser import parse_whatsapp_payload
from app.conversations.documents import WhatsAppInboundEventDocument
from app.conversations.services.conversation_resolver import ConversationResolver
from app.conversations.services.message_buffer_service import MessageBufferService
from app.core.logging import logger


class WhatsAppIngestionService:
    def __init__(self) -> None:
        self._resolver = ConversationResolver()
        self._buffer_service = MessageBufferService()

    async def ingest(self, payload: dict) -> int:
        parsed_messages = parse_whatsapp_payload(payload)

        if not parsed_messages:
            return 0

        ingested_count = 0

        for parsed in parsed_messages:
            conversation_id = build_conversation_id("whatsapp", parsed.normalized_phone)

            await self._resolver.resolve(
                channel="whatsapp",
                normalized_phone=parsed.normalized_phone,
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
