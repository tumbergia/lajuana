from datetime import UTC, datetime
from uuid import uuid4
import asyncio

from app.ai.assistant.orchestrator import AssistantOrchestrator
from app.ai.language.detector import SUPPORTED_RESPONSE_LANGUAGES
from app.ai.language.messages import t
from app.ai.providers.stt_provider import TranscriptionResult
from app.channels.whatsapp.normalizer import build_conversation_id
from app.channels.whatsapp.outbound_service import WhatsAppOutboundService
from app.channels.whatsapp.parser import ParsedMessage, parse_whatsapp_payload
from app.conversations.documents import WhatsAppInboundEventDocument
from app.conversations.services.conversation_resolver import ConversationResolver
from app.conversations.services.message_buffer_service import MessageBufferService
from app.core.config import settings
from app.core.logging import logger
from app.documents.conversation_session_document import ConversationSessionDocument
from app.documents.conversation_turn_document import ConversationTurnDocument
from app.schemas.ask import AskRequest
from app.services.audio_transcription_service import download_and_transcribe

_SUPPORTED_DOCUMENT_MIMES = {"application/pdf"}


def _is_local_takeover() -> bool:
    return (settings.app_env or "").lower() in {"local", "dev", "development"}


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

    async def _get_conversation_language(self, conversation_id: str) -> str:
        try:
            session = await ConversationSessionDocument.find_one(
                {"conversation_key": conversation_id, "status": "active"},
            )
            if session and session.language:
                return session.language
        except Exception:
            pass
        return "es"

    async def _reject_and_log(
        self,
        *,
        parsed: ParsedMessage,
        conversation_id: str,
        message_key: str,
        log_type: str,
    ) -> None:
        if not self._outbound_service:
            return
        lang = await self._get_conversation_language(conversation_id)
        text = t(message_key, lang)
        turn = ConversationTurnDocument(
            trace_id=str(uuid4()),
            channel="whatsapp",
            from_phone=parsed.normalized_phone,
            user_message="",
            conversation_id=conversation_id,
            status="responded",
            response_text=text,
            responded_at=datetime.now(UTC),
        )
        await turn.insert()
        await self._outbound_service.send(
            turn=turn,
            to_phone=parsed.normalized_phone,
            text=text,
        )
        logger.info(
            "[conversation_id=%s] Rejected %s | wa_message_id=%s",
            conversation_id,
            log_type,
            parsed.wa_message_id,
        )

    async def _reject_unsupported_audio_language(
        self,
        *,
        parsed: ParsedMessage,
        conversation_id: str,
        detected_language: str,
        transcription: str,
    ) -> None:
        """Responde con `unsupported_language_message` cuando el STT detecta
        un idioma fuera del catálogo soportado. Ver ADR-0013.
        """
        if not self._outbound_service:
            return
        lang = await self._get_conversation_language(conversation_id)
        supported_list = ", ".join(
            t(f"language_name_{code}", lang)
            for code in ("es", "en", "fr", "de", "it", "ru", "zh", "ja")
        )
        text = t("unsupported_language_message", lang, supported=supported_list)
        turn = ConversationTurnDocument(
            trace_id=str(uuid4()),
            channel="whatsapp",
            from_phone=parsed.normalized_phone,
            user_message=transcription,
            conversation_id=conversation_id,
            status="responded",
            response_text=text,
            responded_at=datetime.now(UTC),
        )
        await turn.insert()
        await self._outbound_service.send(
            turn=turn,
            to_phone=parsed.normalized_phone,
            text=text,
        )
        logger.info(
            "[conversation_id=%s] Rejected unsupported audio language | "
            "wa_message_id=%s detected=%s",
            conversation_id,
            parsed.wa_message_id,
            detected_language,
        )

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
            transcription_result: TranscriptionResult | None = None
            transcription_language: str | None = None
            if parsed.message_type == "audio":
                try:
                    transcription_result = await download_and_transcribe(parsed.media_id)
                    body = transcription_result.text
                    transcription_language = transcription_result.language
                    logger.info(
                        "[ingestion] Audio transcribed | wa_message_id=%s "
                        "lang=%s (p=%.2f) transcription=%.200s",
                        parsed.wa_message_id,
                        transcription_language or "?",
                        transcription_result.language_probability or 0.0,
                        transcription_result.text,
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

            if transcription_result is not None:
                await collection.update_one(
                    {"wa_message_id": parsed.wa_message_id},
                    {
                        "$set": {
                            "transcription": transcription_result.text,
                            "transcription_language": transcription_language,
                        }
                    },
                )

            # ── Unsupported message types (sticker, video, location, etc.) ──
            if parsed.message_type == "unsupported":
                await self._reject_and_log(
                    parsed=parsed,
                    conversation_id=conversation_id,
                    message_key="unsupported_file_type",
                    log_type=f"unsupported type (raw_type={parsed.raw_payload.get('type', 'unknown')})",
                )
                ingested_count += 1
                continue

            # ── Non-PDF documents (Word, Excel, etc.) ──
            if parsed.message_type == "document":
                doc_info = (parsed.raw_payload or {}).get("document") or {}
                doc_mime = (doc_info.get("mime_type") or "").lower()
                if doc_mime and doc_mime not in _SUPPORTED_DOCUMENT_MIMES:
                    await self._reject_and_log(
                        parsed=parsed,
                        conversation_id=conversation_id,
                        message_key="unsupported_document_type",
                        log_type=f"unsupported document mime={doc_mime}",
                    )
                    ingested_count += 1
                    continue

            # ── Audio en idioma NO soportado: responder unsupported y NO
            #     pasar al orchestrator. El STT detectó (e.g.) coreano o
            #     portugués; el bot no puede atender en esos idiomas (ADR-0013).
            if (
                parsed.message_type == "audio"
                and transcription_language
                and transcription_language not in SUPPORTED_RESPONSE_LANGUAGES
            ):
                await self._reject_unsupported_audio_language(
                    parsed=parsed,
                    conversation_id=conversation_id,
                    detected_language=transcription_language,
                    transcription=body,
                )
                ingested_count += 1
                continue

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
                            audio_language=transcription_language,
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
                buffer_doc = await self._buffer_service.add_message(
                    conversation_id=conversation_id,
                    normalized_phone=parsed.normalized_phone,
                    channel="whatsapp",
                    message_id=parsed.wa_message_id,
                    body=body,
                )
                if _is_local_takeover():
                    # Espera el debounce (y extensiones si llegan más mensajes)
                    # antes de procesar; el status "buffering" evita que el
                    # worker remoto robe el buffer en Atlas.
                    asyncio.create_task(
                        self._process_buffer_when_due(buffer_doc.buffer_id),
                        name=f"local-takeover-{buffer_doc.buffer_id[:8]}",
                    )

            ingested_count += 1

        logger.info("[ingestion] Ingested %d message(s)", ingested_count)
        return ingested_count

    async def _process_buffer_when_due(self, buffer_id: str) -> None:
        """Espera scheduled_for (debounce) y luego procesa el buffer local."""
        try:
            from app.channels.whatsapp.outbound_service import WhatsAppOutboundService
            from app.conversations.documents import MessageBufferDocument
            from app.conversations.services.conversation_lock_service import (
                ConversationLockService,
            )
            from app.conversations.services.conversation_turn_worker import (
                ConversationTurnWorker,
            )

            # Hasta ~buffer_debounce + margen; relee por si se extendió.
            for _ in range(60):
                buffer_doc = await MessageBufferDocument.find_one(
                    {
                        "buffer_id": buffer_id,
                        "status": {"$in": ["scheduled", "buffering", "processing"]},
                    }
                )
                if not buffer_doc:
                    logger.info(
                        "[local-takeover] Buffer %s already claimed/processed",
                        buffer_id,
                    )
                    return

                now = datetime.now(UTC)
                due = buffer_doc.scheduled_for
                if due is not None and due.tzinfo is None:
                    due = due.replace(tzinfo=UTC)
                if due is None or due <= now:
                    break

                wait_s = min(2.0, max(0.2, (due - now).total_seconds()))
                await asyncio.sleep(wait_s)
            else:
                buffer_doc = await MessageBufferDocument.find_one(
                    {"buffer_id": buffer_id}
                )
                if not buffer_doc or buffer_doc.status not in {
                    "scheduled",
                    "buffering",
                    "processing",
                }:
                    return

            worker = ConversationTurnWorker(
                lock_service=ConversationLockService(),
                buffer_service=self._buffer_service,
                outbound_service=self._outbound_service or WhatsAppOutboundService(),
            )
            ok = await worker._process_single_buffer(buffer_doc)
            logger.info(
                "[local-takeover] buffer=%s processed=%s",
                buffer_id,
                ok,
            )
        except Exception:
            logger.exception(
                "[local-takeover] Failed processing buffer=%s",
                buffer_id,
            )

    async def _process_buffer_immediately(self, buffer_id: str) -> None:
        """Compat: procesa sin esperar (tests / callers legacy)."""
        await self._process_buffer_when_due(buffer_id)
