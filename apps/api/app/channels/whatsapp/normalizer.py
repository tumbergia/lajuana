import re


def normalize_phone(phone: str) -> str:
    digits = re.sub(r"\D+", "", phone or "")
    if not digits:
        raise ValueError("empty_phone")
    return f"+{digits}"


def build_conversation_id(channel: str, normalized_phone: str) -> str:
    return f"{channel}:{normalized_phone}"
