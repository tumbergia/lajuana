"""Tests for intent_router catalog listing → list_experiences.

El camino productivo es list_experiences con response literal (todas las
experiencias). get_all_experiences no está cableado como tool MCP.
"""

from __future__ import annotations

from app.ai.assistant.intent_router import detect_and_build_plan
from app.schemas.assistant_plan import AssistantAction


def _assert_list_experiences(plan) -> None:
    assert plan is not None
    assert plan.tool_name == "list_experiences"
    assert plan.action == AssistantAction.TOOL_CALL


def test_intent_router_routes_todas_las_experiencias_to_list() -> None:
    plan = detect_and_build_plan(
        user_message="dame informacion de todas las experiencias",
        channel="whatsapp",
    )
    _assert_list_experiences(plan)


def test_intent_router_routes_listame_todas_to_list() -> None:
    plan = detect_and_build_plan(
        user_message="listame todas las experiencias",
        channel="whatsapp",
    )
    _assert_list_experiences(plan)


def test_intent_router_routes_que_experiencias_to_list() -> None:
    plan = detect_and_build_plan(
        user_message="que experiencias tienes",
        channel="whatsapp",
    )
    _assert_list_experiences(plan)


def test_intent_router_routes_lista_completa_to_list() -> None:
    plan = detect_and_build_plan(
        user_message="lista completa de experiencias",
        channel="whatsapp",
    )
    _assert_list_experiences(plan)


def test_intent_router_routes_simple_list_to_list() -> None:
    plan = detect_and_build_plan(
        user_message="que experiencias ofrecen",
        channel="whatsapp",
    )
    _assert_list_experiences(plan)


def test_intent_router_routes_hola_que_experiencias_to_list() -> None:
    plan = detect_and_build_plan(
        user_message="hola que experiencias tienes",
        channel="whatsapp",
    )
    _assert_list_experiences(plan)


def test_intent_router_routes_dame_las_experiencias_to_list() -> None:
    plan = detect_and_build_plan(
        user_message="dame las experiencias",
        channel="whatsapp",
    )
    _assert_list_experiences(plan)


def test_intent_router_routes_que_hay_to_list() -> None:
    plan = detect_and_build_plan(
        user_message="que hay para hacer",
        channel="whatsapp",
    )
    _assert_list_experiences(plan)


def test_intent_router_routes_que_opciones_to_list() -> None:
    plan = detect_and_build_plan(
        user_message="que opciones hay",
        channel="whatsapp",
    )
    _assert_list_experiences(plan)
