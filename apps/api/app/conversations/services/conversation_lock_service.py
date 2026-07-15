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
                "conversation_id": conversation_id,
                "locked_until": {"$lt": stale_threshold, "$ne": None},
            },
            {"$set": {"locked_until": None, "locked_by": None}},
        )

        result = await collection.find_one_and_update(
            {
                "conversation_id": conversation_id,
                "$or": [
                    {"locked_until": None},
                    {"locked_until": {"$lt": now}},
                ],
            },
            {"$set": {"locked_until": lock_until, "locked_by": "whatsapp_worker"}},
        )
        if result:
            logger.info("[conversation_id=%s] Lock acquired", conversation_id)
            return True

        logger.info("[conversation_id=%s] Lock not acquired", conversation_id)
        return False

    async def release(self, *, conversation_id: str) -> None:
        collection = ConversationSessionDocument.get_motor_collection()
        await collection.find_one_and_update(
            {"conversation_id": conversation_id},
            {"$set": {"locked_until": None, "locked_by": None}},
        )
