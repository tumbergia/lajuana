from app.ai.assistant.policy import ToolPolicyEngine
from app.schemas.assistant_plan import AssistantAction, AssistantPlan, RiskLevel, ToolArgs


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
    assert decision.reason == "tool_not_allowed_for_channel"


def test_critical_tool_blocked_even_from_admin_api() -> None:
    plan = AssistantPlan(
        action=AssistantAction.TOOL_CALL,
        confidence=0.95,
        tool_name="confirm_reservation",
        arguments={"reservation_id": "abc"},
        risk_level=RiskLevel.LOW,
        user_goal="Confirmar reserva.",
        audit_summary="El usuario quiere confirmar una reserva.",
    )
    decision = ToolPolicyEngine().validate(plan, channel="admin_api")

    assert decision.allowed is False
    assert decision.reason == "tool_not_allowed_for_channel"


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


def test_create_reservation_draft_allowed() -> None:
    plan = AssistantPlan(
        action=AssistantAction.TOOL_CALL,
        tool_name="create_reservation_draft",
        arguments=ToolArgs(),
        confidence=0.9,
        user_goal="create a reservation draft",
        audit_summary="test",
    )
    decision = ToolPolicyEngine().validate(plan)
    assert decision.allowed


def test_get_reservation_public_summary_allowed() -> None:
    plan = AssistantPlan(
        action=AssistantAction.TOOL_CALL,
        tool_name="get_reservation_public_summary",
        arguments=ToolArgs(),
        confidence=0.9,
        user_goal="check reservation public summary",
        audit_summary="test",
    )
    decision = ToolPolicyEngine().validate(plan)
    assert decision.allowed


def test_get_reservation_status_by_phone_allowed() -> None:
    plan = AssistantPlan(
        action=AssistantAction.TOOL_CALL,
        tool_name="get_reservation_status_by_phone",
        arguments=ToolArgs(),
        confidence=0.9,
        user_goal="check reservation status by phone",
        audit_summary="test",
    )
    decision = ToolPolicyEngine().validate(plan)
    assert decision.allowed


def test_get_reservation_status_by_phone_blocked_on_admin_api() -> None:
    plan = AssistantPlan(
        action=AssistantAction.TOOL_CALL,
        tool_name="get_reservation_status_by_phone",
        arguments=ToolArgs(),
        confidence=0.9,
        user_goal="check reservation status by phone",
        audit_summary="test",
    )
    decision = ToolPolicyEngine().validate(plan, channel="admin_api")
    assert decision.allowed is False
    assert decision.reason == "admin_use_operational_tools"


def test_attach_payment_proof_to_reservation_allowed() -> None:
    plan = AssistantPlan(
        action=AssistantAction.TOOL_CALL,
        tool_name="attach_payment_proof_to_reservation",
        arguments=ToolArgs(),
        confidence=0.9,
        user_goal="attach payment proof",
        audit_summary="test",
    )
    decision = ToolPolicyEngine().validate(plan)
    assert decision.allowed


def test_blocks_admin_tool_from_whatsapp() -> None:
    plan = AssistantPlan(
        action=AssistantAction.TOOL_CALL,
        confidence=0.95,
        tool_name="admin_get_sales_summary",
        arguments={},
        risk_level=RiskLevel.LOW,
        user_goal="get sales summary",
        audit_summary="test",
    )
    decision = ToolPolicyEngine().validate(plan, channel="whatsapp")
    assert decision.allowed is False
    assert decision.reason == "tool_not_allowed_for_channel"


def test_allows_admin_tool_from_admin_api() -> None:
    plan = AssistantPlan(
        action=AssistantAction.TOOL_CALL,
        confidence=0.95,
        tool_name="admin_get_sales_summary",
        arguments={},
        risk_level=RiskLevel.LOW,
        user_goal="get sales summary",
        audit_summary="test",
    )
    decision = ToolPolicyEngine().validate(plan, channel="admin_api")
    assert decision.allowed is True


def test_allows_client_tool_from_whatsapp() -> None:
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
        user_goal="check availability",
        audit_summary="test",
    )
    decision = ToolPolicyEngine().validate(plan, channel="whatsapp")
    assert decision.allowed is True


def test_blocks_guide_tool_from_whatsapp() -> None:
    plan = AssistantPlan(
        action=AssistantAction.TOOL_CALL,
        confidence=0.95,
        tool_name="guide_create_service_log",
        arguments={"reservation_id": "abc123", "event_type": "arrival"},
        risk_level=RiskLevel.LOW,
        user_goal="create service log",
        audit_summary="test",
    )
    decision = ToolPolicyEngine().validate(plan, channel="whatsapp")
    assert decision.allowed is False
    assert decision.reason == "tool_not_allowed_for_channel"


def test_allows_guide_tool_from_mobile_api() -> None:
    plan = AssistantPlan(
        action=AssistantAction.TOOL_CALL,
        confidence=0.95,
        tool_name="guide_create_service_log",
        arguments={"reservation_id": "abc123", "event_type": "arrival"},
        risk_level=RiskLevel.LOW,
        user_goal="create service log",
        audit_summary="test",
    )
    decision = ToolPolicyEngine().validate(plan, channel="mobile_api")
    assert decision.allowed is True


def test_admin_api_can_access_all_client_tools() -> None:
    for tool in {"check_experience_availability", "quote_experience", "list_experiences"}:
        plan = AssistantPlan(
            action=AssistantAction.TOOL_CALL,
            confidence=0.95,
            tool_name=tool,
            arguments={
                "experience_query": "test",
                "requested_date": "2026-06-20",
                "participant_count": 4,
            },
            risk_level=RiskLevel.LOW,
            user_goal="test",
            audit_summary="test",
        )
        decision = ToolPolicyEngine().validate(plan, channel="admin_api")
        assert decision.allowed is True, f"{tool} should be allowed from admin_api"


def test_unknown_tool_blocked_regardless_of_channel() -> None:
    plan = AssistantPlan(
        action=AssistantAction.TOOL_CALL,
        confidence=0.95,
        tool_name="nonexistent_tool",
        arguments={},
        risk_level=RiskLevel.LOW,
        user_goal="test",
        audit_summary="test",
    )
    decision = ToolPolicyEngine().validate(plan, channel="admin_api")
    assert decision.allowed is False
    assert decision.reason == "tool_not_allowed_for_channel"
