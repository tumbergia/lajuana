from app.assistant.intent_detector import detect_intent


def test_detects_availability_intent_with_spanish_date_and_people() -> None:
    intent = detect_intent(
        "Hola, quiero reservar recorrido de medio día para 4 personas el 20 de junio de 2026"
    )

    assert intent.name == "availability_check"
    assert intent.requires_tool is True
    assert intent.tool_name == "check_experience_availability"
    assert intent.participant_count == 4
    assert intent.requested_date is not None
    assert intent.requested_date.isoformat() == "2026-06-20"


def test_detects_missing_data_for_availability() -> None:
    intent = detect_intent("Quiero reservar")

    assert intent.name == "availability_check"
    assert intent.requires_tool is False
