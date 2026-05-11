from datetime import UTC, datetime
from typing import Any

from beanie import Indexed
from pydantic import Field
from pymongo import IndexModel

from app.common.collections import Collections
from app.documents.base import AuditDocument


class ChatCheckpointDocument(AuditDocument):
    conversation_id: Indexed(str)  # type: ignore[valid-type]
    user_id: Indexed(str)  # type: ignore[valid-type]
    messages: list[dict[str, Any]] = Field(default_factory=list)
    role: str = "unassigned"
    extracted_data: dict[str, Any] = Field(default_factory=dict)
    rag_context: str = ""
    booking_intent: bool = False
    state_snapshot: dict[str, Any] = Field(default_factory=dict)
    checkpoint_updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    class Settings:
        name = Collections.CHAT_CHECKPOINTS
        indexes = [IndexModel([("conversation_id", 1), ("user_id", 1)], unique=True)]
