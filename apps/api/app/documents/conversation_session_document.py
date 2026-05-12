from datetime import UTC, datetime
from typing import Any

from beanie import Document
from pydantic import Field


class ConversationSessionDocument(Document):
    channel: str
    conversation_key: str = Field(description="from_phone o conversation_id")
    from_phone: str | None = None
    conversation_id: str | None = None
    status: str = "active"
    last_intent: str | None = None
    pending_fields: list[str] = Field(default_factory=list)
    slot_values: dict[str, Any] = Field(default_factory=dict)
    last_trace_id: str | None = None
    turn_count: int = 0
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    class Settings:
        name = "conversation_sessions"
        indexes = [
            "channel",
            "conversation_key",
            "from_phone",
            "conversation_id",
            "updated_at",
        ]
