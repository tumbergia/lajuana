from app.schemas.conversation_session import merge_slots


def test_merge_empty_session() -> None:
    result = merge_slots(
        session_slots={},
        plan_args={"experience_query": "los chorros"},
        required_fields=["requested_date", "participant_count"],
    )
    assert result.merged["experience_query"] == "los chorros"
    assert "requested_date" not in result.merged
    assert result.still_missing == ["requested_date", "participant_count"]
    assert result.filled_from_session == []


def test_merge_fills_from_session() -> None:
    result = merge_slots(
        session_slots={
            "experience_query": "los chorros",
            "requested_date": "2026-06-20",
        },
        plan_args={"participant_count": 4},
        required_fields=["requested_date", "participant_count", "experience_query"],
    )
    assert result.merged["experience_query"] == "los chorros"
    assert result.merged["requested_date"] == "2026-06-20"
    assert result.merged["participant_count"] == 4
    assert result.still_missing == []
    assert "requested_date" in result.filled_from_session
    assert "experience_query" in result.filled_from_session


def test_merge_plan_overrides_session() -> None:
    result = merge_slots(
        session_slots={
            "experience_query": "los chorros",
            "participant_count": 2,
        },
        plan_args={
            "experience_query": "recorrido de medio día",
            "participant_count": 4,
            "requested_date": "2026-06-20",
        },
        required_fields=["requested_date", "participant_count", "experience_query"],
    )
    assert result.merged["experience_query"] == "recorrido de medio día"
    assert result.merged["participant_count"] == 4
    assert result.merged["requested_date"] == "2026-06-20"
    assert result.still_missing == []
    assert result.filled_from_session == []


def test_merge_partial_override() -> None:
    result = merge_slots(
        session_slots={
            "experience_query": "los chorros",
            "participant_count": 2,
        },
        plan_args={"participant_count": 4},
        required_fields=["experience_query", "participant_count"],
    )
    assert result.merged["experience_query"] == "los chorros"
    assert result.merged["participant_count"] == 4
    assert result.filled_from_session == ["experience_query"]


def test_merge_session_overrides_plan_nulls() -> None:
    result = merge_slots(
        session_slots={
            "experience_query": "los chorros",
            "requested_date": "2026-06-20",
            "participant_count": 4,
        },
        plan_args={
            "experience_query": None,
            "participant_count": 4,
        },
        required_fields=["requested_date", "participant_count", "experience_query"],
    )
    assert result.merged["experience_query"] == "los chorros"
    assert result.merged["requested_date"] == "2026-06-20"
    assert result.merged["participant_count"] == 4
    assert result.filled_from_session == ["requested_date", "experience_query"]
    assert result.still_missing == []


def test_merge_partial_required_fields() -> None:
    result = merge_slots(
        session_slots={},
        plan_args={"experience_query": "los chorros"},
        required_fields=["requested_date", "participant_count"],
    )
    assert result.merged == {"experience_query": "los chorros"}
    assert result.still_missing == ["requested_date", "participant_count"]
    assert result.filled_from_session == []
