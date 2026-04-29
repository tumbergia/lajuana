from datetime import UTC, datetime
from typing import Any

from langchain_core.messages import BaseMessage, messages_from_dict, messages_to_dict

from app.documents import ChatCheckpointDocument


class BeanieConversationCheckpointer:
    async def load(self, *, conversation_id: str, user_id: str) -> dict[str, Any] | None:
        document = await ChatCheckpointDocument.find_one(
            {
                "conversation_id": conversation_id,
                "user_id": user_id,
            }
        )
        if document is None:
            return None

        messages: list[BaseMessage] = messages_from_dict(document.messages)
        return {
            "messages": messages,
            "role": document.role,
            "extracted_data": document.extracted_data,
            "rag_context": document.rag_context,
            "booking_intent": document.booking_intent,
        }

    async def save(
        self,
        *,
        conversation_id: str,
        user_id: str,
        role: str,
        state: dict[str, Any],
    ) -> None:
        document = await ChatCheckpointDocument.find_one(
            {
                "conversation_id": conversation_id,
                "user_id": user_id,
            }
        )

        messages = state.get("messages", [])
        serialized_messages = messages_to_dict(messages)

        payload = {
            "messages": serialized_messages,
            "role": role,
            "extracted_data": state.get("extracted_data", {}),
            "rag_context": state.get("rag_context", ""),
            "booking_intent": bool(state.get("booking_intent", False)),
            "checkpoint_updated_at": datetime.now(UTC),
        }

        if document is None:
            document = ChatCheckpointDocument(
                conversation_id=conversation_id,
                user_id=user_id,
                **payload,
            )
            await document.insert()
            return

        for field, value in payload.items():
            setattr(document, field, value)
        await document.save()
