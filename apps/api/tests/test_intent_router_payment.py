from __future__ import annotations

from app.ai.assistant.intent_router import detect_and_build_plan
from app.schemas.assistant_plan import AssistantAction


def test_payment_info_routes_to_get_payment_instructions() -> None:
    for msg in [
        "dime los detalles del pago",
        "como pago?",
        "cuales son los medios de pago",
        "donde consigo los datos de pago",
        "necesito el numero de cuenta bancolombia",
    ]:
        plan = detect_and_build_plan(user_message=msg)
        assert plan is not None, msg
        assert plan.tool_name == "get_payment_instructions"
        assert plan.action == AssistantAction.TOOL_CALL


def test_payment_info_request_does_not_set_bold_when_unmentioned() -> None:
    # Sin mencionar Bold, payment info es una tool call normal sin flag.
    plan = detect_and_build_plan(user_message="dime los medios de pago")
    assert plan is not None
    assert plan.tool_name == "get_payment_instructions"
    assert plan.arguments.bold_requested is False


def test_bold_link_request_routes_to_configured_payment_tool() -> None:
    for msg in [
        "quiero el link de pago bold",
        "pagar por bold por favor",
        "link bold",
        "pago bold",
        "quiero un link de pago",
    ]:
        plan = detect_and_build_plan(user_message=msg)
        assert plan is not None, msg
        assert plan.action == AssistantAction.TOOL_CALL
        assert plan.tool_name == "get_payment_instructions"
        assert plan.arguments.bold_requested is True


def test_informal_bold_request_routes_without_llm() -> None:
    plan = detect_and_build_plan(user_message="qro pagr con bld", channel="test")

    assert plan is not None
    assert plan.action == AssistantAction.TOOL_CALL
    assert plan.tool_name == "get_payment_instructions"
    assert plan.arguments.bold_requested is True


def test_neutral_payment_phrase_not_routed_when_unrelated() -> None:
    # Frase genérica que no debe confundirse con consulta de pago.
    plan = detect_and_build_plan(user_message="el pago se hace el viernes")
    assert plan is None or plan.tool_name != "get_payment_instructions"


def test_informal_public_configuration_queries_use_live_config_tool() -> None:
    for message in [
        "dnd qda la juana? mandme la ubikcion",
        "q edades pueden ir a la experiencia?",
        "cuanto tmpo tngo pa pagar la preresrva?",
        "con cuántos días de anticipación debo rsrvar?",
        "necesito enviar comprobante de pago?",
    ]:
        plan = detect_and_build_plan(user_message=message, channel="test")

        assert plan is not None, message
        assert plan.action == AssistantAction.TOOL_CALL
        assert plan.tool_name == "get_public_business_rules"
