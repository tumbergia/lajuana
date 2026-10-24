"""Pausas + continuación por módulo del asistente admin (sin Gemini).

Cubre listados NL del router y flujos incompletos → follow-up → (confirmar).
"""

from __future__ import annotations

import asyncio
from types import SimpleNamespace
from typing import Any

import pytest

from app.ai.assistant.intent_router import detect_and_build_plan
from app.ai.assistant.orchestrator import (
    AssistantOrchestrator,
    _extract_slot_updates,
)
from app.schemas.ask import AskRequest
from app.schemas.assistant_plan import AssistantAction, AssistantPlan, ToolArgs


OID = "507f1f77bcf86cd799439011"
OID_PAY = "507f1f77bcf86cd799439012"

NL_LIST_MODULES: list[tuple[str, str]] = [
    ("listar usuarios", "admin_list_users"),
    ("listame las experiencias", "admin_list_experiences_admin"),
    ("listar proveedores", "admin_list_providers"),
    ("muestrame los equinos disponibles", "admin_list_equines"),
    ("listame las reservas pendientes", "admin_list_reservations"),
    ("ver las sillas", "admin_list_saddles"),
    ("dame los contactos de emergencia", "admin_get_emergency_contacts"),
    ("abre el tablero de asignación", "admin_get_assignment_board"),
    ("reporte de ventas", "admin_get_sales_summary"),
    ("muéstrame el embudo de reservas", "admin_get_reservation_funnel"),
    ("de qué redes viene más gente", "admin_get_channel_performance"),
    ("reporte de ocupación", "admin_get_occupancy_report"),
    ("carga equina", "admin_get_equine_workload_report"),
    ("aprobar el pago", "admin_approve_payment"),
    ("rechaza el comprobante", "admin_reject_payment_proof"),
    ("desactiva el usuario", "admin_deactivate_user"),
    ("desactiva el proveedor", "admin_deactivate_provider"),
    ("desactiva el equino", "admin_deactivate_equine"),
    ("desactiva la silla", "admin_deactivate_saddle"),
    ("desactiva la experiencia", "admin_deactivate_experience"),
    ("registra un evento de equino", "admin_create_equine_event"),
    ("eventos del equino", "admin_list_equine_events"),
]

SLOT_CASES: list[tuple[str, list[str], dict[str, Any]]] = [
    ("el correo es ana@lajuana.co", ["email"], {"email": "ana@lajuana.co"}),
    ("nivel intermedio", ["level"], {"level": "intermediate"}),
    ("dura 4 horas", ["duration_hours"], {"duration_hours": 4}),
    ("2 días", ["duration_hours"], {"duration_hours": 48}),
    ("alojamiento", ["type"], {"type": "lodging"}),
    ("Ana Pérez", ["full_name", "email"], {"full_name": "Ana Pérez"}),
    ("Los Chorros", ["name"], {"name": "Chorros"}),
    ("un recorrido por cascadas", ["description"], {"description": "un recorrido por cascadas"}),
    ("el código es PR-20260601-ABC", ["code"], {"code": "PR-20260601-ABC"}),
    (OID, ["reservation_id"], {"reservation_id": OID}),
    (f"el id es {OID_PAY}", ["payment_proof_id"], {"payment_proof_id": OID_PAY}),
    ("S-99", ["code"], {"code": "S-99"}),
    ("Trueno", ["name", "equine_id"], {"name": "Trueno"}),
    ("Vacunación anual", ["title"], {"title": "Vacunación anual"}),
]


class FakeDoc:
    def __init__(self, **kwargs: Any) -> None:
        for key, value in kwargs.items():
            setattr(self, key, value)

    async def insert(self) -> FakeDoc:
        self.id = "fake-id"
        return self

    async def save(self) -> None:
        pass


async def _empty_turn_list() -> list:
    return []


class FindableFakeDoc(FakeDoc):
    channel = True
    conversation_id = True
    created_at = True
    status = True

    @classmethod
    def find(cls, *args: Any, **kwargs: Any) -> SimpleNamespace:
        return SimpleNamespace(
            sort=lambda _: SimpleNamespace(limit=lambda _: SimpleNamespace(to_list=_empty_turn_list))
        )


class MockPlanner:
    def __init__(self, plan: AssistantPlan | None = None) -> None:
        self._plan = plan

    async def plan(self, **kwargs: Any) -> AssistantPlan:
        if self._plan is not None:
            return self._plan
        return AssistantPlan(
            action=AssistantAction.FINAL_RESPONSE,
            confidence=0.2,
            user_goal="No debería planificar.",
            audit_summary="Planner no esperado.",
            response="No entendí.",
        )


def _build_session(**overrides: Any) -> Any:
    async def noop_save() -> None:
        pass

    data = {
        "id": "ses-modules",
        "channel": "admin_api",
        "conversation_key": "mod-1",
        "status": "active",
        "slot_values": {},
        "turn_count": 0,
        "pending_fields": [],
        "last_intent": None,
        "last_trace_id": None,
        "updated_at": None,
        "language": "es",
        "language_override": None,
        "language_streak": 0,
        "language_streak_lang": None,
        "pending_media_proof": None,
        "save": noop_save,
    }
    data.update(overrides)
    return SimpleNamespace(**data)


def _wire(monkeypatch: pytest.MonkeyPatch, session: Any) -> None:
    monkeypatch.setattr("app.ai.assistant.orchestrator.ConversationTurnDocument", FindableFakeDoc)
    monkeypatch.setattr("app.ai.assistant.orchestrator.ToolCallLogDocument", FakeDoc)

    async def fake_load(self: Any, **_: Any) -> Any:
        return session

    monkeypatch.setattr(AssistantOrchestrator, "_load_or_create_session", fake_load)


def _stub_registry(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    calls: list[str] = []

    async def fake_call(tool_name: str, /, **kwargs: Any) -> dict[str, Any]:
        calls.append(tool_name)
        return {"ok": True, "created": True, "message": f"{tool_name} ejecutado."}

    monkeypatch.setattr("app.ai.assistant.orchestrator.registry.call", fake_call)

    async def fake_compose(**kwargs: Any) -> str:
        output = kwargs.get("tool_output") or {}
        return str(output.get("message") or "Listo.")

    monkeypatch.setattr("app.ai.assistant.orchestrator.compose_tool_response", fake_compose)
    return calls


def _ask(orch: AssistantOrchestrator, message: str, cid: str) -> Any:
    return orch.ask(AskRequest(message=message, channel="admin_api", conversation_id=cid))


@pytest.mark.parametrize("utterance,tool", NL_LIST_MODULES)
def test_router_covers_admin_modules(utterance: str, tool: str) -> None:
    plan = detect_and_build_plan(user_message=utterance, channel="admin_api")
    assert plan is not None, utterance
    assert plan.tool_name == tool


@pytest.mark.parametrize("utterance,missing,expected", SLOT_CASES)
def test_slot_updates_cover_module_fields(
    utterance: str, missing: list[str], expected: dict[str, Any]
) -> None:
    updates = _extract_slot_updates(utterance, missing)
    for key, value in expected.items():
        assert updates.get(key) == value, updates


def test_experience_incomplete_then_continue_then_confirm(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = _build_session()
    _wire(monkeypatch, session)
    calls = _stub_registry(monkeypatch)
    orch = AssistantOrchestrator(planner=MockPlanner())
    cid = "mod-exp"

    async def run() -> tuple[Any, Any, Any]:
        first = await _ask(orch, "crear experiencia llamada Cascada Escondida", cid)
        second = await _ask(
            orch,
            "es un recorrido por bosque, nivel intermedio, dura 4 horas",
            cid,
        )
        third = await _ask(orch, "sí", cid)
        return first, second, third

    first, second, third = asyncio.run(run())
    assert first.needs_confirmation is False
    assert first.tool_name == "admin_create_experience"
    assert first.action == AssistantAction.ASK_CLARIFYING_QUESTION
    assert second.needs_confirmation is True
    assert third.action == AssistantAction.TOOL_CALL
    assert calls == ["admin_create_experience"]


def test_provider_name_then_type_then_confirm(monkeypatch: pytest.MonkeyPatch) -> None:
    session = _build_session()
    _wire(monkeypatch, session)
    calls = _stub_registry(monkeypatch)
    orch = AssistantOrchestrator(planner=MockPlanner())
    cid = "mod-prov"

    async def run() -> tuple[Any, Any, Any]:
        first = await _ask(orch, "crea un proveedor llamado Finca El Roble", cid)
        second = await _ask(orch, "alojamiento", cid)
        third = await _ask(orch, "sí", cid)
        return first, second, third

    first, second, third = asyncio.run(run())
    assert first.tool_name == "admin_create_provider"
    assert first.needs_confirmation is False
    assert second.needs_confirmation is True
    assert third.action == AssistantAction.TOOL_CALL
    assert calls == ["admin_create_provider"]


def test_equine_without_name_then_continue(monkeypatch: pytest.MonkeyPatch) -> None:
    session = _build_session()
    _wire(monkeypatch, session)
    calls = _stub_registry(monkeypatch)
    orch = AssistantOrchestrator(planner=MockPlanner())
    cid = "mod-eq"

    async def run() -> tuple[Any, Any, Any]:
        first = await _ask(orch, "registra un equino", cid)
        second = await _ask(orch, "Trueno", cid)
        third = await _ask(orch, "sí", cid)
        return first, second, third

    first, second, third = asyncio.run(run())
    assert first.tool_name == "admin_create_equine"
    assert first.needs_confirmation is False
    assert "nombre" in first.response.lower()
    assert second.needs_confirmation is True
    assert third.action == AssistantAction.TOOL_CALL
    assert calls == ["admin_create_equine"]


def test_assignment_board_asks_reservation_then_continues(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = _build_session()
    _wire(monkeypatch, session)
    calls = _stub_registry(monkeypatch)
    orch = AssistantOrchestrator(planner=MockPlanner())
    cid = "mod-board"

    async def run() -> tuple[Any, Any]:
        first = await _ask(orch, "abre el tablero de asignación", cid)
        second = await _ask(orch, OID, cid)
        return first, second

    first, second = asyncio.run(run())
    assert first.tool_name == "admin_get_assignment_board"
    assert first.needs_confirmation is False
    assert first.action == AssistantAction.ASK_CLARIFYING_QUESTION
    assert second.tool_name == "admin_get_assignment_board"
    assert second.action == AssistantAction.TOOL_CALL
    assert calls == ["admin_get_assignment_board"]


def test_approve_payment_asks_id_then_continue_then_confirm(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = _build_session()
    _wire(monkeypatch, session)
    calls = _stub_registry(monkeypatch)
    orch = AssistantOrchestrator(planner=MockPlanner())
    cid = "mod-pay"

    async def run() -> tuple[Any, Any, Any]:
        first = await _ask(orch, "aprobar el pago", cid)
        second = await _ask(orch, OID_PAY, cid)
        third = await _ask(orch, "sí", cid)
        return first, second, third

    first, second, third = asyncio.run(run())
    assert first.tool_name == "admin_approve_payment"
    assert first.needs_confirmation is False
    assert second.needs_confirmation is True
    assert third.action == AssistantAction.TOOL_CALL
    assert calls == ["admin_approve_payment"]


def test_reject_payment_asks_id_then_continue_then_confirm(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = _build_session()
    _wire(monkeypatch, session)
    calls = _stub_registry(monkeypatch)
    orch = AssistantOrchestrator(planner=MockPlanner())
    cid = "mod-rej"

    async def run() -> tuple[Any, Any, Any]:
        first = await _ask(orch, "rechaza el comprobante", cid)
        second = await _ask(orch, OID_PAY, cid)
        third = await _ask(orch, "sí", cid)
        return first, second, third

    first, second, third = asyncio.run(run())
    assert first.tool_name == "admin_reject_payment_proof"
    assert second.needs_confirmation is True
    assert third.action == AssistantAction.TOOL_CALL
    assert calls == ["admin_reject_payment_proof"]


def test_deactivate_user_asks_id_then_continue_then_confirm(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = _build_session()
    _wire(monkeypatch, session)
    calls = _stub_registry(monkeypatch)
    orch = AssistantOrchestrator(planner=MockPlanner())
    cid = "mod-du"

    async def run() -> tuple[Any, Any, Any]:
        first = await _ask(orch, "desactiva el usuario", cid)
        second = await _ask(orch, OID, cid)
        third = await _ask(orch, "sí", cid)
        return first, second, third

    first, second, third = asyncio.run(run())
    assert first.tool_name == "admin_deactivate_user"
    assert first.needs_confirmation is False
    assert second.needs_confirmation is True
    assert third.action == AssistantAction.TOOL_CALL
    assert calls == ["admin_deactivate_user"]


def test_equine_event_asks_id_then_continues(monkeypatch: pytest.MonkeyPatch) -> None:
    session = _build_session()
    _wire(monkeypatch, session)
    calls = _stub_registry(monkeypatch)
    orch = AssistantOrchestrator(planner=MockPlanner())
    cid = "mod-ee"

    async def run() -> tuple[Any, Any]:
        first = await _ask(orch, "registra un evento de equino", cid)
        second = await _ask(orch, OID, cid)
        return first, second

    first, second = asyncio.run(run())
    assert first.tool_name == "admin_create_equine_event"
    assert first.action == AssistantAction.ASK_CLARIFYING_QUESTION
    assert second.tool_name == "admin_create_equine_event"
    assert second.action == AssistantAction.TOOL_CALL
    assert calls == ["admin_create_equine_event"]


def test_list_equine_events_asks_id_then_continues(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = _build_session()
    _wire(monkeypatch, session)
    calls = _stub_registry(monkeypatch)
    orch = AssistantOrchestrator(planner=MockPlanner())
    cid = "mod-lee"

    async def run() -> tuple[Any, Any]:
        first = await _ask(orch, "eventos del equino", cid)
        second = await _ask(orch, OID, cid)
        return first, second

    first, second = asyncio.run(run())
    assert first.tool_name == "admin_list_equine_events"
    assert first.action == AssistantAction.ASK_CLARIFYING_QUESTION
    assert second.action == AssistantAction.TOOL_CALL
    assert calls == ["admin_list_equine_events"]


def test_reservation_detail_missing_code_then_continue(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = _build_session(
        slot_values={"_active_tool_name": "admin_get_reservation_detail"},
        pending_fields=["code"],
    )
    _wire(monkeypatch, session)
    calls = _stub_registry(monkeypatch)
    orch = AssistantOrchestrator(planner=MockPlanner())

    result = asyncio.run(_ask(orch, "el código es PR-20260601-ABC", "mod-res"))
    assert result.tool_name == "admin_get_reservation_detail"
    assert result.action == AssistantAction.TOOL_CALL
    assert calls == ["admin_get_reservation_detail"]


def test_confirm_reservation_missing_id_then_continue_then_confirm(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = _build_session(
        slot_values={"_active_tool_name": "admin_confirm_reservation"},
        pending_fields=["reservation_id"],
    )
    _wire(monkeypatch, session)
    calls = _stub_registry(monkeypatch)
    orch = AssistantOrchestrator(planner=MockPlanner())
    cid = "mod-conf"

    async def run() -> tuple[Any, Any]:
        first = await _ask(orch, OID, cid)
        second = await _ask(orch, "sí", cid)
        return first, second

    first, second = asyncio.run(run())
    assert first.needs_confirmation is True
    assert first.tool_name == "admin_confirm_reservation"
    assert second.action == AssistantAction.TOOL_CALL
    assert calls == ["admin_confirm_reservation"]


def test_cancel_reservation_missing_id_then_continue_then_confirm(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = _build_session(
        slot_values={"_active_tool_name": "admin_cancel_reservation"},
        pending_fields=["reservation_id"],
    )
    _wire(monkeypatch, session)
    calls = _stub_registry(monkeypatch)
    orch = AssistantOrchestrator(planner=MockPlanner())
    cid = "mod-can"

    async def run() -> tuple[Any, Any]:
        first = await _ask(orch, OID, cid)
        second = await _ask(orch, "sí", cid)
        return first, second

    first, second = asyncio.run(run())
    assert first.needs_confirmation is True
    assert second.action == AssistantAction.TOOL_CALL
    assert calls == ["admin_cancel_reservation"]


def test_get_equine_missing_id_then_continue(monkeypatch: pytest.MonkeyPatch) -> None:
    session = _build_session(
        slot_values={"_active_tool_name": "admin_get_equine"},
        pending_fields=["equine_id"],
    )
    _wire(monkeypatch, session)
    calls = _stub_registry(monkeypatch)
    orch = AssistantOrchestrator(planner=MockPlanner())

    result = asyncio.run(_ask(orch, OID, "mod-ge"))
    assert result.tool_name == "admin_get_equine"
    assert result.action == AssistantAction.TOOL_CALL
    assert calls == ["admin_get_equine"]


def test_saddle_create_incomplete_then_continue(monkeypatch: pytest.MonkeyPatch) -> None:
    session = _build_session()
    _wire(monkeypatch, session)
    calls = _stub_registry(monkeypatch)
    orch = AssistantOrchestrator(
        planner=MockPlanner(
            AssistantPlan(
                action=AssistantAction.TOOL_CALL,
                confidence=0.9,
                tool_name="admin_create_saddle",
                arguments=ToolArgs(),
                user_goal="Crear silla.",
                audit_summary="Plan silla incompleto.",
            )
        )
    )
    cid = "mod-sad"

    async def run() -> tuple[Any, Any]:
        first = await _ask(orch, "mete una montura nueva al inventario", cid)
        second = await _ask(orch, "el código es SL-99", cid)
        return first, second

    first, second = asyncio.run(run())
    assert first.tool_name == "admin_create_saddle"
    assert first.action == AssistantAction.ASK_CLARIFYING_QUESTION
    assert first.needs_confirmation is False
    assert second.tool_name == "admin_create_saddle"
    assert second.action == AssistantAction.TOOL_CALL
    assert calls == ["admin_create_saddle"]


def test_saddles_available_asks_reservation_then_continues(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = _build_session()
    _wire(monkeypatch, session)
    calls = _stub_registry(monkeypatch)
    orch = AssistantOrchestrator(planner=MockPlanner())
    cid = "mod-sav"

    async def run() -> tuple[Any, Any]:
        first = await _ask(orch, "sillas disponibles de la reserva", cid)
        second = await _ask(orch, OID, cid)
        return first, second

    first, second = asyncio.run(run())
    assert first.tool_name == "admin_list_available_saddles_for_reservation"
    assert first.action == AssistantAction.ASK_CLARIFYING_QUESTION
    assert second.action == AssistantAction.TOOL_CALL
    assert calls == ["admin_list_available_saddles_for_reservation"]
