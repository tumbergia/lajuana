from datetime import UTC, datetime, timedelta
from uuid import uuid4

from app.conversations.documents import MessageBufferDocument
from app.core.logging import logger

DEBOUNCE_SECONDS = 10
MAX_BUFFER_SECONDS = 30
MAX_MESSAGES_PER_BUFFER = 15


class MessageBufferService:
    MAX_STALE_SECONDS = 120
    # Si un buffer lleva más de esto en estado "processing", se considera
    # crashed y se re-marca como "scheduled" para reprocesarlo. Debe ser
    # MAYOR que el timeout del orchestrator (75s) para no recuperarlo
    # mientras un turno legítimo sigue corriendo.
    PROCESSING_TIMEOUT_SECONDS = 180

    async def add_message(
        self,
        *,
        conversation_id: str,
        normalized_phone: str,
        channel: str,
        message_id: str,
        body: str,
    ) -> MessageBufferDocument:
        now = datetime.now(UTC)

        existing = await MessageBufferDocument.find_one(
            {
                "conversation_id": conversation_id,
                "status": {"$in": ["open", "scheduled"]},
            }
        )

        if existing:
            first_at = existing.first_message_at
            if first_at and first_at.tzinfo is None:
                first_at = first_at.replace(tzinfo=UTC)
            elapsed = (now - (first_at or now)).total_seconds()

            # If buffer is too old, close it as stale and create a new one
            if elapsed >= self.MAX_STALE_SECONDS:
                collection = MessageBufferDocument.get_motor_collection()
                await collection.find_one_and_update(
                    {"buffer_id": existing.buffer_id},
                    {"$set": {"status": "stale"}},
                )
                logger.info(
                    "[conversation_id=%s] Buffer stale after %.0fs, creating new buffer",
                    conversation_id,
                    elapsed,
                )
                existing = None

        if existing:
            existing.message_ids.append(message_id)
            existing.last_message_at = now
            existing.version += 1
            existing.combined_preview = (
                (existing.combined_preview + f"\n{body}") if existing.combined_preview else body
            )

            elapsed = (now - (first_at or now)).total_seconds()

            if (
                elapsed >= MAX_BUFFER_SECONDS
                or len(existing.message_ids) >= MAX_MESSAGES_PER_BUFFER
            ):
                existing.scheduled_for = now
                existing.status = "scheduled"
            else:
                existing.scheduled_for = now + timedelta(seconds=DEBOUNCE_SECONDS)
                existing.status = "scheduled"

            await existing.save()
            return existing

        buffer_doc = MessageBufferDocument(
            buffer_id=str(uuid4()),
            conversation_id=conversation_id,
            normalized_phone=normalized_phone,
            channel=channel,
            message_ids=[message_id],
            combined_preview=body,
            status="scheduled",
            first_message_at=now,
            last_message_at=now,
            scheduled_for=now + timedelta(seconds=DEBOUNCE_SECONDS),
        )
        await buffer_doc.insert()

        logger.info(
            "[conversation_id=%s] New buffer | debounce=%ds | message=%.80s",
            conversation_id,
            DEBOUNCE_SECONDS,
            body,
        )

        return buffer_doc

    async def find_due_buffers(self, *, limit: int = 25) -> list[MessageBufferDocument]:
        now = datetime.now(UTC)
        # Auto-recupera buffers "processing" que llevan más de
        # `processing_timeout_seconds` sin avanzar (e.g. el worker crasheó
        # a la mitad de un turno). Los marcamos de nuevo como "scheduled"
        # para que el scheduler los reprocese.
        stuck_processing = await MessageBufferDocument.find(
            {
                "status": "processing",
                "processing_started_at": {
                    "$lt": now - timedelta(seconds=self.PROCESSING_TIMEOUT_SECONDS),
                },
            }
        ).to_list()
        for stuck in stuck_processing:
            logger.warning(
                "[buffer_id=%s] Recovering stuck buffer (processing since %s)",
                stuck.buffer_id,
                stuck.processing_started_at,
            )
            await self._recover_stuck_buffer(stuck)
        return (
            await MessageBufferDocument.find(
                {
                    "status": "scheduled",
                    "scheduled_for": {"$lte": now},
                }
            )
            .sort("scheduled_for")
            .limit(limit)
            .to_list()
        )

    async def _recover_stuck_buffer(self, buffer: MessageBufferDocument) -> None:
        """Recupera un buffer que quedó en 'processing' por un crash.

        Estrategia: lo re-marca como 'scheduled' con `scheduled_for=now` para
        que el scheduler lo reprocese en el siguiente tick. NO borramos los
        message_ids: el worker es idempotente (los eventos son
        deduplicados por wa_message_id en la ingestion).
        """
        now = datetime.now(UTC)
        collection = MessageBufferDocument.get_motor_collection()
        await collection.find_one_and_update(
            {"buffer_id": buffer.buffer_id, "status": "processing"},
            {
                "$set": {
                    "status": "scheduled",
                    "scheduled_for": now,
                }
            },
        )

    async def mark_processing(self, *, buffer: MessageBufferDocument) -> bool:
        now = datetime.now(UTC)
        collection = MessageBufferDocument.get_motor_collection()
        result = await collection.find_one_and_update(
            {"buffer_id": buffer.buffer_id, "status": "scheduled"},
            {
                "$set": {
                    "status": "processing",
                    "processing_started_at": now,
                    "version": buffer.version + 1,
                }
            },  # noqa: E501
        )
        return result is not None

    async def mark_processed(self, *, buffer: MessageBufferDocument) -> None:
        now = datetime.now(UTC)
        collection = MessageBufferDocument.get_motor_collection()
        await collection.find_one_and_update(
            {"buffer_id": buffer.buffer_id},
            {"$set": {"status": "processed", "processed_at": now}},
        )

    async def mark_failed(self, *, buffer: MessageBufferDocument, error: str) -> None:
        collection = MessageBufferDocument.get_motor_collection()
        await collection.find_one_and_update(
            {"buffer_id": buffer.buffer_id},
            {"$set": {"status": "failed", "error": error}},
        )

    async def reschedule(self, *, buffer: MessageBufferDocument, delay_seconds: int = 2) -> None:
        now = datetime.now(UTC)
        collection = MessageBufferDocument.get_motor_collection()
        await collection.find_one_and_update(
            {"buffer_id": buffer.buffer_id, "status": {"$in": ["scheduled", "processing"]}},
            {
                "$set": {
                    "status": "scheduled",
                    "scheduled_for": now + timedelta(seconds=delay_seconds),
                }
            },  # noqa: E501
        )
