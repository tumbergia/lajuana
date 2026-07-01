from __future__ import annotations

from app.ai.assistant.intent_router import detect_and_build_plan
from app.schemas.assistant_plan import AssistantAction


def test_admin_channel_lists_reservations_this_week() -> None:
    plan = detect_and_build_plan(
        user_message="Hola dame que reservas hay esta semana",
        channel="admin_api",
    )
    assert plan is not None
    assert plan.tool_name == "admin_list_reservations"
    assert plan.arguments.date_from is not None  # type: ignore[attr-defined]
    assert plan.arguments.date_to is not None  # type: ignore[attr-defined]


def test_admin_channel_does_not_use_client_experience_list() -> None:
    plan = detect_and_build_plan(
        user_message="listame las experiencias",
        channel="admin_api",
    )
    assert plan is None


def test_admin_channel_lists_reservations() -> None:
    plan = detect_and_build_plan(
        user_message="listame las reservas pendientes",
        channel="admin_api",
    )
    assert plan is not None
    assert plan.tool_name == "admin_list_reservations"
    assert plan.action == AssistantAction.TOOL_CALL


def test_admin_channel_lists_equines() -> None:
    plan = detect_and_build_plan(
        user_message="muestrame los equinos disponibles",
        channel="admin_api",
    )
    assert plan is not None
    assert plan.tool_name == "admin_list_equines"


def test_admin_channel_assignment_board() -> None:
    plan = detect_and_build_plan(
        user_message="abre el tablero de asignación",
        channel="admin_api",
    )
    assert plan is not None
    assert plan.tool_name == "admin_get_assignment_board"


def test_admin_channel_emergency_contacts() -> None:
    plan = detect_and_build_plan(
        user_message="dame los contactos de emergencia",
        channel="admin_api",
    )
    assert plan is not None
    assert plan.tool_name == "admin_get_emergency_contacts"


def test_admin_keyword_without_channel() -> None:
    plan = detect_and_build_plan(user_message="listar proveedores activos")
    assert plan is not None
    assert plan.tool_name == "admin_list_providers"


def test_client_channel_does_not_force_admin_list() -> None:
    plan = detect_and_build_plan(
        user_message="listame las experiencias",
        channel="whatsapp",
    )
    assert plan is not None
    assert plan.tool_name == "list_experiences"
