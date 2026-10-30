from typing import Any

from app.channels.whatsapp.normalizer import normalize_phone


class ParsedMessage:
    def __init__(
        self,
        *,
        wa_message_id: str,
        from_phone: str,
        normalized_phone: str,
        message_type: str,
        body: str | None = None,
        media_id: str | None = None,
        caption: str | None = None,
        provider_timestamp: str | None = None,
        raw_payload: dict[str, Any] | None = None,
    ) -> None:
        self.wa_message_id = wa_message_id
        self.from_phone = from_phone
        self.normalized_phone = normalized_phone
        self.message_type = message_type
        self.body = body
        self.media_id = media_id
        self.caption = caption
        self.provider_timestamp = provider_timestamp
        self.raw_payload = raw_payload or {}


def parse_whatsapp_payload(payload: dict[str, Any]) -> list[ParsedMessage]:
    messages: list[ParsedMessage] = []
    entries = payload.get("entry") or []

    if not entries:
        return messages

    for entry in entries:
        changes = entry.get("changes") or []
        for change in changes:
            value = change.get("value") or {}
            raw_messages = value.get("messages") or []
            for raw in raw_messages:
                parsed = _parse_single_message(raw)
                if parsed:
                    messages.append(parsed)

    return messages


def _parse_single_message(raw: dict[str, Any]) -> ParsedMessage | None:
    msg_type = raw.get("type")
    wa_message_id = raw.get("id")
    from_phone = raw.get("from")

    if not wa_message_id or not from_phone:
        return None

    try:
        normalized = normalize_phone(from_phone)
    except ValueError:
        return None

    if msg_type == "text":
        body = ((raw.get("text") or {}).get("body") or "").strip()
        if not body:
            return None
        return ParsedMessage(
            wa_message_id=wa_message_id,
            from_phone=from_phone,
            normalized_phone=normalized,
            message_type=msg_type,
            body=body,
            raw_payload=raw,
        )

    if msg_type == "button":
        button_text = ((raw.get("button") or {}).get("text") or "").strip()
        if not button_text:
            return None
        return ParsedMessage(
            wa_message_id=wa_message_id,
            from_phone=from_phone,
            normalized_phone=normalized,
            message_type=msg_type,
            body=button_text,
            raw_payload=raw,
        )

    if msg_type == "interactive":
        interactive = raw.get("interactive") or {}
        type_ = interactive.get("type")
        body = None
        if type_ == "button_reply":
            body = ((interactive.get("button_reply") or {}).get("title") or "").strip()
        elif type_ == "list_reply":
            body = ((interactive.get("list_reply") or {}).get("title") or "").strip()
        if body:
            return ParsedMessage(
                wa_message_id=wa_message_id,
                from_phone=from_phone,
                normalized_phone=normalized,
                message_type=msg_type,
                body=body,
                raw_payload=raw,
            )

    if msg_type in ("audio", "image", "document"):
        media = raw.get(msg_type) or {}
        media_id = media.get("id") or media.get("media_id")
        caption = (media.get("caption") or "").strip() or None
        if not media_id:
            return None
        return ParsedMessage(
            wa_message_id=wa_message_id,
            from_phone=from_phone,
            normalized_phone=normalized,
            message_type=msg_type,
            media_id=media_id,
            caption=caption,
            raw_payload=raw,
        )

    return ParsedMessage(
        wa_message_id=wa_message_id,
        from_phone=from_phone,
        normalized_phone=normalized,
        message_type="unsupported",
        provider_timestamp=raw.get("timestamp"),
        raw_payload=raw,
    )
