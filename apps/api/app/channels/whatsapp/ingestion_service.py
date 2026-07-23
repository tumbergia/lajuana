from datetime import UTC, datetime
from uuid import uuid4
import asyncio

from app.ai.assistant.orchestrator import AssistantOrchestrator
from app.ai.language.messages import t
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
            # Audio: NO transcribir ni responder aquí. Se bufferiza como el
            # texto; el STT corre al vencer el debounce (varios audios → un turno).
            if parsed.message_type == "audio":
                body = ""
            elif parsed.media_id and parsed.message_type != "text":
                body = parsed.caption or f"[{parsed.message_type} recibido]"

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

            buffer_doc = await self._buffer_service.add_message(
                conversation_id=conversation_id,
                normalized_phone=parsed.normalized_phone,
                channel="whatsapp",
                message_id=parsed.wa_message_id,
                body=body or ("[audio]" if parsed.message_type == "audio" else ""),
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
