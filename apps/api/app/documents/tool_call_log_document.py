from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from beanie import Document
from pydantic import Field


class ToolCallLogDocument(Document):
    trace_id: str = Field(default_factory=lambda: str(uuid4()))
    conversation_turn_id: str | None = None
    tool_name: str
    tool_version: str = "2026-05-11"
    input: dict[str, Any] = Field(default_factory=dict)
    output: dict[str, Any] = Field(default_factory=dict)
    status: str = "success"
    error_code: str | None = None
    latency_ms: int | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    class Settings:
        name = "tool_call_logs"
        indexes = [
            "trace_id",
            "conversation_turn_id",
            "tool_name",
            "status",
            "created_at",
        ]
