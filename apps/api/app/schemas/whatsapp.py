from typing import Any

from pydantic import BaseModel, Field


class WhatsAppWebhookMessage(BaseModel):
    external_message_id: str | None = None
    from_phone: str | None = None
    text: str | None = None
    raw_payload: dict[str, Any] = Field(default_factory=dict)


class WhatsAppWebhookResult(BaseModel):
    received: bool = True
    processed_messages: int = 0
