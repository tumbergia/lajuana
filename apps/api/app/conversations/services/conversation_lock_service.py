from datetime import UTC, datetime, timedelta

from app.core.logging import logger
from app.documents.conversation_session_document import ConversationSessionDocument

LOCK_SECONDS = 60


class ConversationLockService:
    async def acquire(self, *, conversation_id: str) -> bool:
        now = datetime.now(UTC)
        lock_until = now + timedelta(seconds=LOCK_SECONDS)

        collection = ConversationSessionDocument.get_motor_collection()
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
