"""Tests for intent_router matching of get_all_experiences.

Valida que el bot SIEMPRE use get_all_experiences (no list_experiences) cuando
el usuario pregunta por el catálogo en general, para que liste TODAS las
experiencias con TODOS sus campos.
"""

from __future__ import annotations

from app.ai.assistant.intent_router import detect_and_build_plan
from app.schemas.assistant_plan import AssistantAction


def test_intent_router_routes_todas_las_experiencias_to_get_all() -> None:
    """'dame informacion de todas las experiencias' must trigger get_all_experiences."""
    plan = detect_and_build_plan(
        user_message="dame informacion de todas las experiencias",
        channel="whatsapp",
    )
    assert plan is not None
    assert plan.tool_name == "get_all_experiences"
    assert plan.action == AssistantAction.TOOL_CALL


def test_intent_router_routes_toda_la_info_to_get_all() -> None:
    """'dame toda la info' must trigger get_all_experiences."""
    plan = detect_and_build_plan(
        user_message="dame toda la info de las experiencias",
        channel="whatsapp",
    )
    assert plan is not None
    assert plan.tool_name == "get_all_experiences"


def test_intent_router_routes_lista_completa_to_get_all() -> None:
    plan = detect_and_build_plan(
        user_message="lista completa de experiencias",
        channel="whatsapp",
    )
    assert plan is not None
    assert plan.tool_name == "get_all_experiences"


def test_intent_router_routes_simple_list_to_get_all() -> None:
    """Caso del usuario: 'que experiencias tienes' debe ir a get_all_experiences,
    NO a list_experiences. La razón: list_experiences solo devuelve resumen y
    el LLM lo filtraba, mostrando solo 3. Con get_all_experiences el bot
    tiene toda la info y puede listar TODAS."""
    plan = detect_and_build_plan(
        user_message="que experiencias tienes",
        channel="whatsapp",
    )
    assert plan is not None
    assert plan.tool_name == "get_all_experiences", (
        f"Se esperaba get_all_experiences, se obtuvo {plan.tool_name}"
    )


def test_intent_router_routes_hola_que_experiencias_to_get_all() -> None:
    """El caso exacto que reportó el usuario: 'hola que experiencias tienes'."""
    plan = detect_and_build_plan(
        user_message="hola que experiencias tienes",
        channel="whatsapp",
    )
    assert plan is not None
    assert plan.tool_name == "get_all_experiences"


def test_intent_router_routes_dame_las_experiencias_to_get_all() -> None:
    plan = detect_and_build_plan(
        user_message="dame las experiencias",
        channel="whatsapp",
    )
    assert plan is not None
    assert plan.tool_name == "get_all_experiences"


def test_intent_router_routes_que_hay_to_get_all() -> None:
    plan = detect_and_build_plan(
        user_message="que planes tienen",
        channel="whatsapp",
    )
    assert plan is not None
    assert plan.tool_name == "get_all_experiences"


def test_intent_router_routes_que_opciones_to_get_all() -> None:
    plan = detect_and_build_plan(
        user_message="que opciones hay",
        channel="whatsapp",
    )
    assert plan is not None
    assert plan.tool_name == "get_all_experiences"
