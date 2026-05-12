from app.ai.assistant.policy import ToolPolicyEngine
from app.schemas.assistant_plan import AssistantAction, AssistantPlan, RiskLevel


def test_allows_read_availability_tool_with_required_args() -> None:
    plan = AssistantPlan(
        action=AssistantAction.TOOL_CALL,
        confidence=0.95,
        tool_name="check_experience_availability",
        arguments={
            "experience_query": "medio día",
            "requested_date": "2026-06-20",
            "participant_count": 4,
        },
        risk_level=RiskLevel.LOW,
        user_goal="Consultar disponibilidad.",
        audit_summary="El usuario entregó datos suficientes para consultar disponibilidad.",
    )

    decision = ToolPolicyEngine().validate(plan)

    assert decision.allowed is True


def test_blocks_critical_tool() -> None:
    plan = AssistantPlan(
        action=AssistantAction.TOOL_CALL,
        confidence=0.95,
        tool_name="confirm_reservation",
        arguments={"reservation_id": "abc"},
        risk_level=RiskLevel.LOW,
        user_goal="Confirmar reserva.",
        audit_summary="El usuario quiere confirmar una reserva.",
    )

    decision = ToolPolicyEngine().validate(plan)

    assert decision.allowed is False
    assert decision.reason == "critical_tool_denied"


def test_blocks_availability_without_date() -> None:
    plan = AssistantPlan(
        action=AssistantAction.TOOL_CALL,
        confidence=0.95,
        tool_name="check_experience_availability",
        arguments={
            "experience_query": "medio día",
            "participant_count": 4,
        },
        risk_level=RiskLevel.LOW,
        user_goal="Consultar disponibilidad.",
        audit_summary="Falta fecha.",
    )

    decision = ToolPolicyEngine().validate(plan)

    assert decision.allowed is False
    assert decision.reason == "missing_required_arguments:requested_date"


def test_blocks_low_confidence() -> None:
    plan = AssistantPlan(
        action=AssistantAction.TOOL_CALL,
        confidence=0.3,
        tool_name="check_experience_availability",
        arguments={
            "experience_query": "medio día",
            "requested_date": "2026-06-20",
            "participant_count": 4,
        },
        risk_level=RiskLevel.LOW,
        user_goal="Consultar disponibilidad.",
        audit_summary="Confianza baja.",
    )

    decision = ToolPolicyEngine().validate(plan)

    assert decision.allowed is False
    assert decision.reason == "low_confidence"


def test_blocks_high_risk_tool() -> None:
    plan = AssistantPlan(
        action=AssistantAction.TOOL_CALL,
        confidence=0.95,
        tool_name="check_experience_availability",
        arguments={
            "experience_query": "medio día",
            "requested_date": "2026-06-20",
            "participant_count": 4,
        },
        risk_level=RiskLevel.HIGH,
        user_goal="Consultar disponibilidad.",
        audit_summary="Alto riesgo.",
    )

    decision = ToolPolicyEngine().validate(plan)

    assert decision.allowed is False
    assert decision.reason == "high_risk_requires_human"


def test_allows_non_tool_action() -> None:
    plan = AssistantPlan(
        action=AssistantAction.FINAL_RESPONSE,
        confidence=0.7,
        user_goal="Saludar.",
        audit_summary="El usuario saluda, no necesita tool.",
    )

    decision = ToolPolicyEngine().validate(plan)

    assert decision.allowed is True
