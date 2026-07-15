from datetime import UTC, datetime, timedelta

from app.core.config import settings
from app.core.logging import logger
from app.documents.conversation_session_document import ConversationSessionDocument

# Backward-compat: tests y código externo siguen importando LOCK_SECONDS.
# Se calcula dinámicamente desde settings.
LOCK_SECONDS = 90  # valor por defecto legacy; ver settings.buffer_lock_seconds


def _get_lock_seconds() -> int:
    return getattr(settings, "buffer_lock_seconds", LOCK_SECONDS)


def _get_stale_lock_seconds() -> int:
    return getattr(settings, "buffer_stale_lock_seconds", 300)


class ConversationLockService:
    async def acquire(self, *, conversation_id: str) -> bool:
        now = datetime.now(UTC)
        lock_until = now + timedelta(seconds=_get_lock_seconds())
        stale_threshold = now - timedelta(seconds=_get_stale_lock_seconds())

        collection = ConversationSessionDocument.get_motor_collection()
        # Auto-limpia locks muertos (más viejos que buffer_stale_lock_seconds)
        # para evitar que un crash anterior bloquee la conversación indefinidamente.
        await collection.update_many(
            {
                "conversation_key": conversation_id,
                "locked_until": {"$lt": stale_threshold, "$ne": None},
            },
            {"$set": {"locked_until": None, "locked_by": None}},
        )

        # Debug: inspeccionar el documento actual antes del acquire
        try:
            debug_doc = await collection.find_one({"conversation_key": conversation_id})
            if debug_doc:
                logger.info(
                    "[lock_debug] conversation_key=%s locked_until=%s locked_by=%s",
                    conversation_id,
                    debug_doc.get("locked_until"),
                    debug_doc.get("locked_by"),
                )
            else:
                logger.warning(
                    "[lock_debug] NO session document found for conversation_key=%s",
                    conversation_id,
                )
        except Exception as e:
            logger.error("[lock_debug] Error inspecting session: %s", e)

        result = await collection.find_one_and_update(
            {
                "conversation_key": conversation_id,
                "$or": [
                    {"locked_until": None},
                    {"locked_until": {"$lt": now}},
                ],
            },
            {"$set": {"locked_until": lock_until, "locked_by": "whatsapp_worker"}},
        )
        if result:
            logger.info("[conversation_id=%s] Lock acquired (locked_until=%s)", conversation_id, lock_until)
            return True

        logger.info("[conversation_id=%s] Lock not acquired | now=%s | stale_threshold=%s", conversation_id, now, stale_threshold)
        return False

    async def release(self, *, conversation_id: str) -> None:
        collection = ConversationSessionDocument.get_motor_collection()
        await collection.find_one_and_update(
            {"conversation_key": conversation_id},
            {"$set": {"locked_until": None, "locked_by": None}},
        )
