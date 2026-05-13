from app.ai.assistant.policy import ToolPolicyEngine
from app.schemas.assistant_plan import AssistantAction, AssistantPlan, RiskLevel


def test_allows_quote_with_experience_query_and_count() -> None:
    plan = AssistantPlan(
        action=AssistantAction.TOOL_CALL,
        confidence=0.95,
        tool_name="quote_experience",
        arguments={
            "experience_query": "medio día",
            "participant_count": 4,
        },
        risk_level=RiskLevel.LOW,
        user_goal="Cotizar experiencia.",
        audit_summary="El usuario entregó datos suficientes para cotizar.",
    )

    decision = ToolPolicyEngine().validate(plan)

    assert decision.allowed is True


def test_allows_quote_with_experience_id_and_count() -> None:
    plan = AssistantPlan(
        action=AssistantAction.TOOL_CALL,
        confidence=0.95,
        tool_name="quote_experience",
        arguments={
            "experience_id": "exp_123",
            "participant_count": 4,
        },
        risk_level=RiskLevel.LOW,
        user_goal="Cotizar experiencia.",
        audit_summary="El usuario entregó id y cantidad de participantes.",
    )

    decision = ToolPolicyEngine().validate(plan)

    assert decision.allowed is True


def test_allows_quote_with_both_experience_fields() -> None:
    plan = AssistantPlan(
        action=AssistantAction.TOOL_CALL,
        confidence=0.95,
        tool_name="quote_experience",
        arguments={
            "experience_id": "exp_123",
            "experience_query": "medio día",
            "participant_count": 4,
        },
        risk_level=RiskLevel.LOW,
        user_goal="Cotizar experiencia.",
        audit_summary="El usuario entregó id y query de experiencia.",
    )

    decision = ToolPolicyEngine().validate(plan)

    assert decision.allowed is True


def test_blocks_quote_without_experience() -> None:
    plan = AssistantPlan(
        action=AssistantAction.TOOL_CALL,
        confidence=0.95,
        tool_name="quote_experience",
        arguments={
            "participant_count": 4,
        },
        risk_level=RiskLevel.LOW,
        user_goal="Cotizar experiencia.",
        audit_summary="Falta identificador de experiencia.",
    )

    decision = ToolPolicyEngine().validate(plan)

    assert decision.allowed is False
    assert decision.reason == "missing_required_arguments:experience_id_or_experience_query"


def test_blocks_quote_without_count() -> None:
    plan = AssistantPlan(
        action=AssistantAction.TOOL_CALL,
        confidence=0.95,
        tool_name="quote_experience",
        arguments={
            "experience_query": "medio día",
        },
        risk_level=RiskLevel.LOW,
        user_goal="Cotizar experiencia.",
        audit_summary="Falta cantidad de participantes.",
    )

    decision = ToolPolicyEngine().validate(plan)

    assert decision.allowed is False
    assert decision.reason == "missing_required_arguments:participant_count"


def test_blocks_quote_with_neither_experience_nor_count() -> None:
    plan = AssistantPlan(
        action=AssistantAction.TOOL_CALL,
        confidence=0.95,
        tool_name="quote_experience",
        arguments={},
        risk_level=RiskLevel.LOW,
        user_goal="Cotizar experiencia.",
        audit_summary="Faltan todos los argumentos requeridos.",
    )

    decision = ToolPolicyEngine().validate(plan)

    assert decision.allowed is False
