import re
from datetime import UTC, datetime
from typing import Any, Protocol
from uuid import uuid4

from app.ai.assistant.assistant_gate import AssistantGate
from app.ai.assistant.orchestrator import AssistantOrchestrator
from app.ai.language.detector import detect_explicit_language_request, detect_language
from app.ai.language.messages import t
from app.ai.mcp.registry import registry
from app.channels.whatsapp.outbound_service import WhatsAppOutboundService
from app.common.enums import ReservationStatus
from app.conversations.documents import (
    MessageBufferDocument,
    WhatsAppInboundEventDocument,
)
from app.conversations.services.conversation_lock_service import (
    ConversationLockService,
)
from app.conversations.services.message_buffer_service import MessageBufferService
from app.core.logging import logger
from app.documents import ReservationDocument
from app.documents.conversation_session_document import ConversationSessionDocument
from app.documents.conversation_turn_document import ConversationTurnDocument
from app.schemas.ask import AskRequest


class _EventLike(Protocol):
    body: str | None
    media_id: str | None
    message_type: str


def combine_messages(events: list[_EventLike]) -> str:
    parts = []
    for event in events:
        if event.body:
            parts.append(event.body.strip())
        elif event.media_id and event.message_type == "audio":
            parts.append("[Audio recibido pendiente de transcripción]")
        elif event.media_id:
            parts.append(f"[{event.message_type} recibido]")
    return "\n".join(parts)


class ConversationTurnWorker:
    def __init__(
        self,
        lock_service: ConversationLockService,
        buffer_service: MessageBufferService,
        outbound_service: WhatsAppOutboundService,
    ) -> None:
        self._orchestrator = AssistantOrchestrator()
        self._assistant_gate = AssistantGate()
        self._lock_service = lock_service
        self._buffer_service = buffer_service
        self._outbound_service = outbound_service

    async def _find_active_candidates(self, from_phone: str) -> list[ReservationDocument]:
        allowed = [
            ReservationStatus.PRE_RESERVED.value,
            ReservationStatus.PENDING_PAYMENT.value,
            ReservationStatus.PAYMENT_RECEIVED.value,
            ReservationStatus.QUOTED.value,
        ]
        return await ReservationDocument.find(
            {
                "holder_phone": from_phone,
                "status": {"$in": allowed},
            }
        ).to_list()

    async def _resolve_session_language(
        self,
        *,
        conversation_id: str,
        combined_text: str,
        normalized_phone: str,
    ) -> str:
        """Devuelve el idioma efectivo a usar en el flujo de comprobantes.

        Prioridad:
          1. Petición explícita en el texto del comprobante (raro pero posible).
          2. Idioma de la sesión activa asociada a la conversación.
          3. Detección por texto (fallback), con español por defecto.

        La carga de la sesión es defensiva: si no hay sesión activa o el
        almacenamiento no está disponible (ej. tests), se cae al fallback
        sin propagar errores.
        """
        explicit = detect_explicit_language_request(combined_text)
        if explicit:
            return explicit

        try:
            session = await ConversationSessionDocument.find_one(
                {"conversation_key": conversation_id, "status": "active"},
            )
        except Exception:
            session = None

        if session and getattr(session, "language", None):
            return session.language

        return detect_language(combined_text)

    async def _try_process_media_proof(
        self,
        *,
        events: list[WhatsAppInboundEventDocument],
        trace_id: str,
        conversation_id: str,
        normalized_phone: str,
        turn: ConversationTurnDocument,
    ) -> bool:
        combined_text = combine_messages(events)
        lang = await self._resolve_session_language(
            conversation_id=conversation_id,
            combined_text=combined_text,
            normalized_phone=normalized_phone,
        )

        media_events = [e for e in events if e.media_id and e.message_type in {"image", "document"}]
        if not media_events:
            return False

        candidates = await self._find_active_candidates(normalized_phone)
        if len(candidates) == 0:
            turn.status = "responded"
            turn.response_text = t("media_no_reservation", lang)
            turn.responded_at = datetime.now(UTC)
            await turn.save()
            await self._outbound_service.send(
                turn=turn,
                to_phone=normalized_phone,
                text=turn.response_text,
            )
            return True

        if len(candidates) > 1:
            event = media_events[0]
            try:
                session = await ConversationSessionDocument.find_one(
                    {"conversation_key": conversation_id, "status": "active"},
                )
                if session and hasattr(session, "pending_media_proof"):
                    session.pending_media_proof = {
                        "wa_message_id": event.wa_message_id,
                        "media_id": event.media_id,
                        "message_type": event.message_type,
                        "mime_type": (
                            (event.raw_payload or {}).get(event.message_type) or {}
                        ).get("mime_type", "application/pdf"),
                        "filename": (
                            (event.raw_payload or {}).get(event.message_type) or {}
                        ).get("filename"),
                        "caption": event.caption,
                        "from_phone": normalized_phone,
                    }
                    session.updated_at = datetime.now(UTC)
                    await session.save()
            except Exception:
                logger.exception(
                    "[conversation_id=%s] Failed to save pending media",
                    conversation_id,
                )

            turn.status = "responded"
            turn.response_text = t("media_multiple_reservations", lang)
            turn.responded_at = datetime.now(UTC)
            await turn.save()
            await self._outbound_service.send(
                turn=turn,
                to_phone=normalized_phone,
                text=turn.response_text,
            )
            return True

        event = media_events[0]
        raw_media = (event.raw_payload or {}).get(event.message_type) or {}
        mime_type = raw_media.get("mime_type") or "application/pdf"
        filename = raw_media.get("filename")

        result = await registry.call(
            "attach_payment_proof_to_reservation",
            conversation_id_for_log=conversation_id,
            trace_id=trace_id,
            conversation_turn_id=str(turn.id),
            reservation_id=str(candidates[0].id),
            from_phone=normalized_phone,
            whatsapp_message_id=event.wa_message_id,
            media_id=event.media_id,
            media_mime_type=mime_type,
            filename=filename,
            caption=event.caption,
        )
        turn.status = "responded"
        turn.response_text = result.get(
            "response",
            t("media_proof_received", lang),
        )
        turn.responded_at = datetime.now(UTC)
        await turn.save()
        await self._outbound_service.send(
            turn=turn,
            to_phone=normalized_phone,
            text=turn.response_text,
        )
        return True

    async def _try_process_pending_media_with_code(
        self,
        *,
        combined_text: str,
        trace_id: str,
        conversation_id: str,
        normalized_phone: str,
        turn: ConversationTurnDocument,
    ) -> bool:
        if not combined_text or not combined_text.strip():
            return False
        code_match = re.search(r"PR-\w{6,}", combined_text.upper())
        if not code_match:
            return False
        reservation_code = code_match.group(0)

        try:
            session = await ConversationSessionDocument.find_one(
                {"conversation_key": conversation_id, "status": "active"},
            )
        except Exception:
            session = None
        if not session:
            return False
        pending: dict[str, Any] | None = getattr(session, "pending_media_proof", None)
        if not pending:
            return False

        lang = getattr(session, "language", "es") or "es"

        reservation = await ReservationDocument.find_one(
            {"code": reservation_code, "holder_phone": normalized_phone},
        )
        if reservation is None:
            return False

        result = await registry.call(
            "attach_payment_proof_to_reservation",
            conversation_id_for_log=conversation_id,
            trace_id=trace_id,
            conversation_turn_id=str(turn.id),
            reservation_id=str(reservation.id),
            from_phone=normalized_phone,
            whatsapp_message_id=pending.get("wa_message_id", ""),
            media_id=pending.get("media_id", ""),
            media_mime_type=pending.get("mime_type", "application/pdf"),
            filename=pending.get("filename"),
            caption=pending.get("caption"),
            public_reservation_code=reservation_code,
        )
        session.pending_media_proof = None
        session.updated_at = datetime.now(UTC)
        await session.save()

        turn.status = "responded"
        turn.response_text = result.get(
            "response",
            t("media_proof_received", lang),
        )
        turn.responded_at = datetime.now(UTC)
        await turn.save()
        await self._outbound_service.send(
            turn=turn,
            to_phone=normalized_phone,
            text=turn.response_text,
        )
        return True

    async def process_due_buffers(self, *, limit: int = 25) -> int:
        buffers = await self._buffer_service.find_due_buffers(limit=limit)
        processed = 0
        for buffer_doc in buffers:
            if await self._process_single_buffer(buffer_doc):
                processed += 1
        return processed

    async def _process_single_buffer(self, buffer_doc: MessageBufferDocument) -> bool:
        conversation_id = buffer_doc.conversation_id

        locked = await self._lock_service.acquire(conversation_id=conversation_id)
        if not locked:
            await self._buffer_service.reschedule(buffer=buffer_doc, delay_seconds=2)
            return False

        reloaded = await MessageBufferDocument.find_one(
            {"buffer_id": buffer_doc.buffer_id, "status": "scheduled"}
        )
        if not reloaded:
            await self._lock_service.release(conversation_id=conversation_id)
            return False

        marked = await self._buffer_service.mark_processing(buffer=reloaded)
        if not marked:
            await self._lock_service.release(conversation_id=conversation_id)
            return False

        try:
            events_docs = await WhatsAppInboundEventDocument.find(
                {"wa_message_id": {"$in": reloaded.message_ids}}
            ).to_list()
            events_dict = {str(e.wa_message_id): e for e in events_docs}
            events = [events_dict[mid] for mid in reloaded.message_ids if mid in events_dict]

            events.sort(key=lambda e: e.received_at or datetime(2020, 1, 1, tzinfo=UTC))
            combined_input = combine_messages(events)
            trace_id = str(uuid4())

            turn = ConversationTurnDocument(
                trace_id=trace_id,
                channel="whatsapp",
                from_phone=buffer_doc.normalized_phone,
                user_message=combined_input,
                conversation_id=conversation_id,
                status="processing",
                input_message_ids=reloaded.message_ids,
            )
            await turn.insert()

            if not await self._assistant_gate.is_allowed(buffer_doc.normalized_phone):
                turn.status = "skipped_disabled"
                turn.responded_at = datetime.now(UTC)
                await turn.save()
                await self._buffer_service.mark_processed(buffer=reloaded)
                logger.info(
                    "[conversation_id=%s] Assistant disabled; turn skipped | messages=%d",
                    conversation_id,
                    len(events),
                )
                return True

            if await self._try_process_pending_media_with_code(
                combined_text=combined_input,
                trace_id=trace_id,
                conversation_id=conversation_id,
                normalized_phone=buffer_doc.normalized_phone,
                turn=turn,
            ):
                await self._buffer_service.mark_processed(buffer=reloaded)
                logger.info(
                    "[conversation_id=%s] Pending media proof associated with code | messages=%d",
                    conversation_id,
                    len(events),
                )
                return True

            if await self._try_process_media_proof(
                events=events,
                trace_id=trace_id,
                conversation_id=conversation_id,
                normalized_phone=buffer_doc.normalized_phone,
                turn=turn,
            ):
                await self._buffer_service.mark_processed(buffer=reloaded)
                logger.info(
                    "[conversation_id=%s] Payment proof media processed | messages=%d",
                    conversation_id,
                    len(events),
                )
                return True

            response = await self._orchestrator.ask(
                AskRequest(
                    message=combined_input,
                    channel="whatsapp",
                    from_phone=buffer_doc.normalized_phone,
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
                to_phone=buffer_doc.normalized_phone,
                text=response.response,
            )

            await self._buffer_service.mark_processed(buffer=reloaded)
            logger.info(
                "[conversation_id=%s] Turn processed | messages=%d",
                conversation_id,
                len(events),
            )
            return True
        except Exception as exc:
            logger.error(
                "[conversation_id=%s] Turn failed | error=%s",
                conversation_id,
                exc,
            )
            await self._buffer_service.mark_failed(buffer=reloaded, error=str(exc))
            return False
        finally:
            await self._lock_service.release(conversation_id=conversation_id)
