from datetime import UTC, datetime
from uuid import uuid4

from app.ai.assistant.orchestrator import AssistantOrchestrator
from app.channels.whatsapp.normalizer import build_conversation_id
from app.channels.whatsapp.parser import parse_whatsapp_payload
from app.channels.whatsapp.outbound_service import WhatsAppOutboundService
from app.conversations.documents import WhatsAppInboundEventDocument
from app.conversations.services.conversation_resolver import ConversationResolver
from app.conversations.services.message_buffer_service import MessageBufferService
from app.core.logging import logger
from app.documents.conversation_turn_document import ConversationTurnDocument
from app.schemas.ask import AskRequest
from app.services.audio_transcription_service import download_and_transcribe


class WhatsAppIngestionService:
    def __init__(
        self,
        resolver: ConversationResolver,
        buffer_service: MessageBufferService,
        outbound_service: WhatsAppOutboundService | None = None,
    ) -> None:
        self._resolver = resolver
        self._buffer_service = buffer_service
        self._orchestrator = AssistantOrchestrator()
        self._outbound_service = outbound_service

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
            transcription = None
            if parsed.message_type == "audio":
                try:
                    transcription = await download_and_transcribe(parsed.media_id)
                    body = transcription
                    logger.info(
                        "[ingestion] Audio transcribed | wa_message_id=%s transcription=%.200s",
                        parsed.wa_message_id,
                        transcription,
                    )
                except Exception as exc:
                    logger.error(
                        "[ingestion] Audio transcription failed | wa_message_id=%s error=%s",
                        parsed.wa_message_id,
                        exc,
                        exc_info=True,
                    )
                    body = "[Audio no pudo ser transcrito]"
            elif parsed.media_id and parsed.message_type != "text":
                body = parsed.caption or f"[{parsed.message_type} recibido]"

            if transcription:
                await collection.update_one(
                    {"wa_message_id": parsed.wa_message_id},
                    {"$set": {"transcription": transcription}},
                )

            # Audio: process immediately, skip buffer to avoid double-response
            if parsed.message_type == "audio" and body and self._outbound_service:
                try:
                    trace_id = str(uuid4())
                    turn = ConversationTurnDocument(
                        trace_id=trace_id,
                        channel="whatsapp",
                        from_phone=parsed.normalized_phone,
                        user_message=body,
                        conversation_id=conversation_id,
                        status="processing",
                        input_message_ids=[parsed.wa_message_id],
                    )
                    await turn.insert()

                    response = await self._orchestrator.ask(
                        AskRequest(
                            message=body,
                            channel="whatsapp",
                            from_phone=parsed.normalized_phone,
                            conversation_id=conversation_id,
                            trace_id=trace_id,
                            conversation_turn_id=str(turn.id),
                        )
                    )

                    turn.status = "responded"
                    turn.response_text = response.response
                    turn.responded_at = datetime.now(UTC)
                    await turn.save()

                    await self._outbound_service.send(
                        turn=turn,
                        to_phone=parsed.normalized_phone,
                        text=response.response,
                    )

                    logger.info(
                        "[conversation_id=%s] Audio processed directly | turn=%s",
                        conversation_id,
                        turn.id,
                    )
                except Exception as exc:
                    logger.error(
                        "[conversation_id=%s] Direct audio processing failed | error=%s",
                        conversation_id,
                        exc,
                        exc_info=True,
                    )
            else:
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
