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
        integration_id: str | None = None,
        phone_number_id: str | None = None,
        is_default_integration: bool = True,
    ) -> ConversationSessionDocument:
        conversation_id = build_conversation_id(
            channel,
            normalized_phone,
            phone_number_id=phone_number_id,
            is_default=is_default_integration,
        )

        existing = await ConversationSessionDocument.find_one(
            {"conversation_id": conversation_id},
        )

        if existing:
            existing.updated_at = datetime.now(UTC)
            if integration_id:
                existing.integration_id = integration_id
                existing.phone_number_id = phone_number_id
            await existing.save()
            return existing

        session = ConversationSessionDocument(
            conversation_id=conversation_id,
            channel=channel,
            normalized_phone=normalized_phone,
            conversation_key=conversation_id,
            integration_id=integration_id,
            phone_number_id=phone_number_id,
        )
        await session.insert()
        logger.info(
            "[conversation_id=%s] New session created",
            conversation_id,
        )
        return session
