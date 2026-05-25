from datetime import UTC, datetime

from app.channels.whatsapp.normalizer import build_conversation_id
from app.core.logging import logger
from app.documents.conversation_session_document import ConversationSessionDocument


class ConversationResolver:
    async def resolve(
        self,
        *,
        channel: str,
        normalized_phone: str,
    ) -> ConversationSessionDocument:
        conversation_id = build_conversation_id(channel, normalized_phone)

        existing = await ConversationSessionDocument.find_one(
            {"conversation_id": conversation_id},
        )

        if existing:
            existing.updated_at = datetime.now(UTC)
            await existing.save()
            return existing

        session = ConversationSessionDocument(
            conversation_id=conversation_id,
            channel=channel,
            normalized_phone=normalized_phone,
            conversation_key=conversation_id,
        )
        await session.insert()
        logger.info(
            "[conversation_id=%s] New session created",
            conversation_id,
        )
        return session
