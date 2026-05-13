from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from beanie import Document
from pydantic import Field


class ConversationTurnDocument(Document):
    trace_id: str = Field(default_factory=lambda: str(uuid4()))
    channel: str = Field(default="whatsapp")
    external_message_id: str | None = None
    from_phone: str | None = None
    to_phone: str | None = None
    direction: str = Field(default="inbound")
    raw_payload: dict[str, Any] = Field(default_factory=dict)
    normalized_text: str | None = None
    detected_intent: str | None = None
    reservation_id: str | None = None
    conversation_id: str | None = None
    user_message: str | None = None
    input_message_ids: list[str] = Field(default_factory=list)
    planner_output: dict[str, Any] = Field(default_factory=dict)
    tool_output: dict[str, Any] = Field(default_factory=dict)
    response_text: str | None = None
    status: str = Field(default="received")
    error_code: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    responded_at: datetime | None = None

    class Settings:
        name = "conversation_turns"
        indexes = [
            "trace_id",
            "conversation_id",
            "channel",
            "external_message_id",
            "from_phone",
            "created_at",
            "detected_intent",
            [("conversation_id", 1), ("status", 1)],
        ]
