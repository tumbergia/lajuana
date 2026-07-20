from datetime import datetime
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


class WhatsAppIntegrationCreateSchema(BaseModel):
    phone_number_id: str
    waba_id: str | None = None
    business_id: str | None = None
    display_phone_number: str | None = None
    verified_name: str | None = None
    connection_mode: str = "coexistence"
    access_token: str | None = None
    api_version: str | None = None
    is_default: bool = False


class WhatsAppIntegrationResponseSchema(BaseModel):
    id: str
    business_id: str | None
    waba_id: str | None
    phone_number_id: str
    display_phone_number: str | None
    verified_name: str | None
    connection_mode: str
    status: str
    is_default: bool
    is_enabled: bool
    coexistence_enabled: bool
    webhook_subscribed: bool
    last_validated_at: datetime | None
    last_error_message: str | None
    created_at: datetime
    updated_at: datetime
