from app.schemas.conversation_session import merge_slots


def test_merge_slots_does_not_override_with_empty_dict() -> None:
    result = merge_slots(
        session_slots={"quote_snapshot": {"subtotal": 720000}},
        plan_args={"quote_snapshot": {}},
        required_fields=["quote_snapshot"],
    )

    assert result.still_missing == []
    assert result.merged["quote_snapshot"]["subtotal"] == 720000


def test_merge_slots_fills_conversation_id_from_session() -> None:
    result = merge_slots(
        session_slots={"conversation_id": "flow-prereserva-004"},
        plan_args={"conversation_id": None},
        required_fields=["conversation_id"],
    )

    assert result.still_missing == []
    assert result.merged["conversation_id"] == "flow-prereserva-004"
