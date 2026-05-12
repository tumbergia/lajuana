from typing import Any

from app.schemas.whatsapp import WhatsAppWebhookMessage


def normalize_whatsapp_payload(payload: dict[str, Any]) -> list[WhatsAppWebhookMessage]:
    messages: list[WhatsAppWebhookMessage] = []

    entries = payload.get("entry") or []
    for entry in entries:
        changes = entry.get("changes") or []
        for change in changes:
            value = change.get("value") or {}
            raw_messages = value.get("messages") or []

            for raw_message in raw_messages:
                message_type = raw_message.get("type")
                text: str | None = None

                if message_type == "text":
                    text = ((raw_message.get("text") or {}).get("body") or "").strip()

                if not text:
                    continue

                messages.append(
                    WhatsAppWebhookMessage(
                        external_message_id=raw_message.get("id"),
                        from_phone=raw_message.get("from"),
                        text=text,
                        raw_payload=raw_message,
                    )
                )

    return messages
