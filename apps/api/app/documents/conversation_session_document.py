from datetime import UTC, datetime
from typing import Any

from beanie import Document
from pydantic import Field


class ConversationSessionDocument(Document):
    channel: str
    conversation_key: str = Field(description="conversation_id")
    from_phone: str | None = None
    conversation_id: str | None = None
    normalized_phone: str = ""
    status: str = "active"
    state: str = "idle"
    last_intent: str | None = None
    pending_fields: list[str] = Field(default_factory=list)
    slot_values: dict[str, Any] = Field(default_factory=dict)
    last_trace_id: str | None = None
    turn_count: int = 0
    locked_until: datetime | None = None
    locked_by: str | None = None
    last_turn_id: str | None = None
    last_inbound_at: datetime | None = None
    language: str = "es"
    language_override: str | None = None
    language_streak: int = 0
    language_streak_lang: str | None = None
    pending_media_proof: dict[str, Any] | None = None
    version: int = 0
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
