from app.ai.assistant.orchestrator import _extract_slot_updates


def test_extracts_email_from_followup() -> None:
    updates = _extract_slot_updates("el correo es ana@lajuana.co", ["email", "full_name"])
    assert updates["email"] == "ana@lajuana.co"


def test_extracts_level_and_duration() -> None:
    updates = _extract_slot_updates(
        "nivel intermedio y dura 4 horas",
        ["level", "duration_hours", "description"],
    )
    assert updates["level"] == "intermediate"
    assert updates["duration_hours"] == 4


def test_extracts_plain_name() -> None:
    updates = _extract_slot_updates("Ana Pérez", ["full_name", "email"])
    assert updates["full_name"] == "Ana Pérez"
