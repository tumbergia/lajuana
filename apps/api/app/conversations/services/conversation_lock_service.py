from datetime import UTC, datetime, timedelta
import os
import re
import socket

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


def _worker_lock_id() -> str:
    return f"local:{socket.gethostname()}:{os.getpid()}"


def _is_local_takeover() -> bool:
    """En local, priorizamos este proceso frente a workers remotos legacy."""
    return (settings.app_env or "").lower() in {"local", "dev", "development"}


class ConversationLockService:
    async def acquire(self, *, conversation_id: str) -> bool:
        now = datetime.now(UTC)
        lock_until = now + timedelta(seconds=_get_lock_seconds())
        stale_threshold = now - timedelta(seconds=_get_stale_lock_seconds())
        worker_id = _worker_lock_id()

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

        # Local takeover: libera locks del worker remoto legacy y de otros
        # procesos locales muertos (mismo host, distinto PID tras --reload).
        if _is_local_takeover():
            stolen = await collection.update_one(
                {
                    "conversation_key": conversation_id,
                    "locked_by": "whatsapp_worker",
                },
                {"$set": {"locked_until": None, "locked_by": None}},
            )
            if stolen.modified_count:
                logger.warning(
                    "[conversation_id=%s] Local takeover: cleared legacy whatsapp_worker lock",
                    conversation_id,
                )
            host = socket.gethostname()
            stale_local = await collection.update_one(
                {
                    "conversation_key": conversation_id,
                    "$and": [
                        {"locked_by": {"$regex": f"^local:{re.escape(host)}:"}},
                        {"locked_by": {"$ne": worker_id}},
                    ],
                },
                {"$set": {"locked_until": None, "locked_by": None}},
            )
            if stale_local.modified_count:
                logger.warning(
                    "[conversation_id=%s] Local takeover: cleared stale local lock (other PID)",
                    conversation_id,
                )

        # Debug: inspeccionar el documento actual antes del acquire
        try:
            debug_doc = await collection.find_one({"conversation_key": conversation_id})
            if debug_doc:
                logger.info(
                    "[lock_debug] conversation_key=%s locked_until=%s locked_by=%s want=%s",
                    conversation_id,
                    debug_doc.get("locked_until"),
                    debug_doc.get("locked_by"),
                    worker_id,
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
            {"$set": {"locked_until": lock_until, "locked_by": worker_id}},
        )
        if result:
            logger.info(
                "[conversation_id=%s] Lock acquired by %s (locked_until=%s)",
                conversation_id,
                worker_id,
                lock_until,
            )
            return True

        logger.info(
            "[conversation_id=%s] Lock not acquired | now=%s | stale_threshold=%s | want=%s",
            conversation_id,
            now,
            stale_threshold,
            worker_id,
        )
        return False

    async def release(self, *, conversation_id: str) -> None:
        collection = ConversationSessionDocument.get_motor_collection()
        await collection.find_one_and_update(
            {"conversation_key": conversation_id},
            {"$set": {"locked_until": None, "locked_by": None}},
        )
