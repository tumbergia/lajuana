from datetime import UTC, datetime
from typing import Protocol
from uuid import uuid4

from app.ai.assistant.orchestrator import AssistantOrchestrator
from app.channels.whatsapp.outbound_service import WhatsAppOutboundService
from app.conversations.documents import (
    MessageBufferDocument,
    WhatsAppInboundEventDocument,
)
from app.conversations.services.conversation_lock_service import (
    ConversationLockService,
)
from app.conversations.services.message_buffer_service import MessageBufferService
from app.core.logging import logger
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
    def __init__(self) -> None:
        self._orchestrator = AssistantOrchestrator()
        self._lock_service = ConversationLockService()
        self._buffer_service = MessageBufferService()
        self._outbound_service = WhatsAppOutboundService()

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
            events = []
            for msg_id in reloaded.message_ids:
                event = await WhatsAppInboundEventDocument.find_one(
                    WhatsAppInboundEventDocument.wa_message_id == msg_id
                )
                if event:
                    events.append(event)

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
                conversation_id, exc,
            )
            await self._buffer_service.mark_failed(buffer=reloaded, error=str(exc))
            return False
        finally:
            await self._lock_service.release(conversation_id=conversation_id)
