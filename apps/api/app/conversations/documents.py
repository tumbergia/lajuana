from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from beanie import Document
from pydantic import Field


class WhatsAppInboundEventDocument(Document):
    wa_message_id: str
    from_phone: str
    normalized_phone: str
    conversation_id: str
    message_type: str
    body: str | None = None
    media_id: str | None = None
    caption: str | None = None
    transcription: str | None = None
    transcription_language: str | None = None
    provider_timestamp: datetime | None = None
    received_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    status: str = "received"
    raw_payload: dict[str, Any] = Field(default_factory=dict)

    class Settings:
        name = "whatsapp_inbound_events"
        indexes = [
            "wa_message_id",
            "conversation_id",
            "normalized_phone",
            "status",
            "received_at",
        ]


class MessageBufferDocument(Document):
    buffer_id: str = Field(default_factory=lambda: str(uuid4()))
    conversation_id: str
    normalized_phone: str
    channel: str = "whatsapp"
    message_ids: list[str] = Field(default_factory=list)
    combined_preview: str = ""
    status: str = "open"
    version: int = 1
    first_message_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    last_message_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    scheduled_for: datetime | None = None
    processing_started_at: datetime | None = None
    processed_at: datetime | None = None
    absorbed_at: datetime | None = None
    absorbed_by_buffer_id: str | None = None
    error: str | None = None

    class Settings:
        name = "message_buffers"
        indexes = [
            "buffer_id",
            "conversation_id",
            "status",
            "scheduled_for",
        ]


class OutboundMessageDocument(Document):
    outbound_id: str = Field(default_factory=lambda: str(uuid4()))
    conversation_id: str
    turn_id: str
    to_phone: str
    body: str
    provider_message_id: str | None = None
    status: str = "queued"
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    sent_at: datetime | None = None
    error: str | None = None

    class Settings:
        name = "outbound_messages"
        indexes = [
            "outbound_id",
            "conversation_id",
            "turn_id",
            "status",
        ]
