from app.schemas.assistant_plan import AssistantAction, AssistantPlan, ToolResultResponse


def test_audit_summary_longer_than_500_is_clipped() -> None:
    plan = AssistantPlan(
        action=AssistantAction.ASK_CLARIFYING_QUESTION,
        confidence=0.95,
        user_goal="Reservar la experiencia Fábrica de Cementos.",
        response="¿Para cuántas personas?",
        audit_summary="x" * 600,
    )
    assert len(plan.audit_summary) == 500
    assert plan.audit_summary.endswith("…")


def test_tool_result_response_clips_long_fields() -> None:
    result = ToolResultResponse(
        response="y" * 1300,
        audit_summary="z" * 550,
    )
    assert len(result.response) == 1200
    assert len(result.audit_summary) == 500
