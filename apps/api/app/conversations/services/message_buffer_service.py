from datetime import UTC, datetime, timedelta
from uuid import uuid4

from app.conversations.documents import MessageBufferDocument
from app.core.config import settings
from app.core.logging import logger

DEBOUNCE_SECONDS = 10
MAX_BUFFER_SECONDS = 30
MAX_MESSAGES_PER_BUFFER = 15

# Local: status invisible al find_due remoto (solo mira "scheduled").
# Así retenemos el buffer durante el debounce, acumulamos mensajes, y
# ganamos al worker remoto que comparte Atlas.
_LOCAL_BUFFERING = "buffering"


def _is_local_env() -> bool:
    return (settings.app_env or "").lower() in {"local", "dev", "development"}


def _debounce_seconds() -> int:
    """Espera para agrupar mensajes seguidos (siempre activo, incl. local)."""
    configured = int(getattr(settings, "buffer_debounce_seconds", None) or DEBOUNCE_SECONDS)
    return max(2, configured)


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
        debounce = _debounce_seconds()
        active_statuses = ["open", "scheduled", _LOCAL_BUFFERING]
        initial_status = _LOCAL_BUFFERING if _is_local_env() else "scheduled"
        collection = MessageBufferDocument.get_motor_collection()

        # Atómico: evita dos "New buffer" concurrentes (race de webhooks).
        for _attempt in range(4):
            existing = await MessageBufferDocument.find_one(
                {
                    "conversation_id": conversation_id,
                    "status": {"$in": active_statuses},
                }
            )

            if existing:
                first_at = existing.first_message_at
                if first_at and first_at.tzinfo is None:
                    first_at = first_at.replace(tzinfo=UTC)
                elapsed = (now - (first_at or now)).total_seconds()

                if elapsed >= self.MAX_STALE_SECONDS:
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
                else:
                    new_scheduled = (
                        now
                        if (
                            elapsed >= MAX_BUFFER_SECONDS
                            or len(existing.message_ids) + 1 >= MAX_MESSAGES_PER_BUFFER
                        )
                        else now + timedelta(seconds=debounce)
                    )
                    preview = (
                        f"{existing.combined_preview}\n{body}"
                        if existing.combined_preview
                        else body
                    )
                    updated = await collection.find_one_and_update(
                        {
                            "buffer_id": existing.buffer_id,
                            "status": {"$in": active_statuses},
                            "version": existing.version,
                        },
                        {
                            "$push": {"message_ids": message_id},
                            "$set": {
                                "last_message_at": now,
                                "scheduled_for": new_scheduled,
                                "combined_preview": preview,
                                "status": (
                                    _LOCAL_BUFFERING
                                    if existing.status == _LOCAL_BUFFERING
                                    else "scheduled"
                                ),
                            },
                            "$inc": {"version": 1},
                        },
                        return_document=True,
                    )
                    if updated:
                        logger.info(
                            "[conversation_id=%s] Buffer extended | debounce=%ds | messages=%d",
                            conversation_id,
                            debounce,
                            len(updated.get("message_ids") or []),
                        )
                        return MessageBufferDocument.model_validate(updated)
                    # Conflicto de versión → reintentar
                    continue

            buffer_id = str(uuid4())
            try:
                buffer_doc = MessageBufferDocument(
                    buffer_id=buffer_id,
                    conversation_id=conversation_id,
                    normalized_phone=normalized_phone,
                    channel=channel,
                    message_ids=[message_id],
                    combined_preview=body,
                    status=initial_status,
                    first_message_at=now,
                    last_message_at=now,
                    scheduled_for=now + timedelta(seconds=debounce),
                    version=1,
                )
                await buffer_doc.insert()
                logger.info(
                    "[conversation_id=%s] New buffer | debounce=%ds | status=%s | message=%.80s",
                    conversation_id,
                    debounce,
                    initial_status,
                    body,
                )
                return buffer_doc
            except Exception:
                # Otro request insertó primero → reintentar append
                logger.info(
                    "[conversation_id=%s] Buffer insert race; retrying append",
                    conversation_id,
                )
                continue

        # Último recurso: append sin version check
        existing = await MessageBufferDocument.find_one(
            {
                "conversation_id": conversation_id,
                "status": {"$in": active_statuses},
            }
        )
        if existing:
            existing.message_ids.append(message_id)
            existing.last_message_at = now
            existing.combined_preview = (
                f"{existing.combined_preview}\n{body}"
                if existing.combined_preview
                else body
            )
            existing.scheduled_for = now + timedelta(seconds=debounce)
            existing.version += 1
            await existing.save()
            return existing
        raise RuntimeError(f"Could not buffer message for {conversation_id}")

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

        statuses = ["scheduled", _LOCAL_BUFFERING] if _is_local_env() else ["scheduled"]
        return (
            await MessageBufferDocument.find(
                {
                    "status": {"$in": statuses},
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

    async def merge_pending_buffers(
        self, *, primary: MessageBufferDocument
    ) -> list[MessageBufferDocument]:
        """Une el buffer primario con todos los demás buffers pendientes
        del mismo `conversation_id` en una sola unidad de procesamiento.

        Caso de uso: el bot tarda 6+ minutos en responder. Mientras tanto
        el usuario envía varios mensajes (sí/no, nombre+correo, comprobante,
        código de reserva). Sin este merge, el scheduler procesa cada
        buffer como un turno independiente, perdiendo contexto (e.g. el
        comprobante no se asocia a la reserva creada en otro turno).

        Estrategia:
          1. Buscar todos los buffers "scheduled" del mismo conversation_id
             (excluyendo el primario).
          2. Mover sus message_ids al primario.
          3. Marcar los secundarios como "absorbed" (estado terminal que el
             scheduler no recoge).
          4. Devolver [primary, *secundarios] para que el caller marque
             todos como "processed" al final del turno.

        El primario sigue siendo el que conserva `scheduled_for` (la fecha
        de su creación) y `combined_preview` ya se actualizó en cada
        add_message, así que el orden cronológico se preserva.
        """
        pending_others = (
            await MessageBufferDocument.find(
                {
                    "conversation_id": primary.conversation_id,
                    "status": {"$in": ["scheduled", _LOCAL_BUFFERING]},
                    "buffer_id": {"$ne": primary.buffer_id},
                }
            )
            .sort("first_message_at")
            .to_list()
        )

        if not pending_others:
            return [primary]

        # Une los message_ids en el primario sin duplicados
        seen = set(primary.message_ids)
        for other in pending_others:
            for mid in other.message_ids:
                if mid not in seen:
                    primary.message_ids.append(mid)
                    seen.add(mid)

        primary.version += 1
        primary.last_message_at = max(
            primary.last_message_at or primary.first_message_at,
            *(o.last_message_at for o in pending_others),
        )
        await primary.save()

        # Marca los secundarios como "absorbed" (estado terminal invisible
        # para find_due_buffers). El caller los marca como "processed" al
        # final del turno.
        now = datetime.now(UTC)
        collection = MessageBufferDocument.get_motor_collection()
        for other in pending_others:
            await collection.find_one_and_update(
                {
                    "buffer_id": other.buffer_id,
                    "status": {"$in": ["scheduled", _LOCAL_BUFFERING]},
                },
                {
                    "$set": {
                        "status": "absorbed",
                        "absorbed_at": now,
                        "absorbed_by_buffer_id": primary.buffer_id,
                    }
                },
            )

        logger.info(
            "[conversation_id=%s] Merged %d pending buffer(s) into buffer_id=%s (total %d messages)",
            primary.conversation_id,
            len(pending_others),
            primary.buffer_id,
            len(primary.message_ids),
        )
        return [primary, *pending_others]

    async def mark_processing(self, *, buffer: MessageBufferDocument) -> bool:
        now = datetime.now(UTC)
        collection = MessageBufferDocument.get_motor_collection()
        result = await collection.find_one_and_update(
            {
                "buffer_id": buffer.buffer_id,
                "status": {"$in": ["scheduled", "processing", _LOCAL_BUFFERING]},
            },
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
