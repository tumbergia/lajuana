"""Pruebas del asistente de voz admin: NL, datos incompletos y pausas/multi-turno."""

from __future__ import annotations

import asyncio
from types import SimpleNamespace
from typing import Any

import pytest

from app.ai.assistant.intent_router import detect_and_build_plan
from app.ai.assistant.orchestrator import (
    AssistantOrchestrator,
    _extract_slot_updates,
    _resume_active_admin_tool,
)
from app.ai.assistant.policy import ToolPolicyEngine
from app.schemas.ask import AskRequest
from app.schemas.assistant_plan import AssistantAction, AssistantPlan, RiskLevel, ToolArgs


# ── Catálogo de entradas de voz (como las diría un admin) ─────────────────

NL_LIST_CASES: list[tuple[str, str]] = [
    ("listar usuarios", "admin_list_users"),
    ("muéstrame los usuarios", "admin_list_users"),
    ("dime qué usuarios hay", "admin_list_users"),
    ("listame las experiencias", "admin_list_experiences_admin"),
    ("ver las experiencias", "admin_list_experiences_admin"),
    ("listar proveedores", "admin_list_providers"),
    ("muestrame los equinos disponibles", "admin_list_equines"),
    ("listame las reservas pendientes", "admin_list_reservations"),
    ("dame los contactos de emergencia", "admin_get_emergency_contacts"),
    ("abre el tablero de asignación", "admin_get_assignment_board"),
    ("ver las sillas", "admin_list_saddles"),
    ("reporte de ventas", "admin_get_sales_summary"),
    ("muéstrame el embudo de reservas", "admin_get_reservation_funnel"),
    ("de qué redes viene más gente", "admin_get_channel_performance"),
    ("reporte de ocupación", "admin_get_occupancy_report"),
    ("carga equina", "admin_get_equine_workload_report"),
]

NL_CREATE_CASES: list[tuple[str, str]] = [
    ("crea un usuario", "admin_create_user"),
    ("crea un usuario llamado Ana Pérez", "admin_create_user"),
    ("registra un usuario correo ana@lajuana.co", "admin_create_user"),
    ("crear experiencia", "admin_create_experience"),
    ("crea una experiencia llamada bosque nublado", "admin_create_experience"),
    ("agrega un proveedor", "admin_create_provider"),
    ("crea un proveedor llamado Finca El Roble", "admin_create_provider"),
    ("registra un equino llamado Trueno", "admin_create_equine"),
    ("registra un equino", "admin_create_equine"),
    ("aprobar el pago", "admin_approve_payment"),
    ("rechaza el comprobante", "admin_reject_payment_proof"),
    ("desactiva el usuario", "admin_deactivate_user"),
    ("registra un evento de equino", "admin_create_equine_event"),
]

SLOT_PAUSE_CASES: list[tuple[str, list[str], dict[str, Any]]] = [
    ("el correo es ana@lajuana.co", ["email", "full_name"], {"email": "ana@lajuana.co"}),
    ("ehhh ana@lajuana.co", ["email"], {"email": "ana@lajuana.co"}),
    ("pues el nombre es Los Chorros", ["name", "level"], {"name": "Los Chorros"}),
    ("nivel intermedio", ["level", "duration_hours"], {"level": "intermediate"}),
    ("básico", ["level"], {"level": "basic"}),
    ("dura 4 horas", ["duration_hours", "description"], {"duration_hours": 4}),
    ("2 días", ["duration_hours"], {"duration_hours": 48}),
    ("alojamiento", ["type", "name"], {"type": "lodging"}),
    ("Ana Pérez", ["full_name", "email"], {"full_name": "Ana Pérez"}),
    ("el código es PR-20260601-ABC", ["code"], {"code": "PR-20260601-ABC"}),
    ("507f1f77bcf86cd799439011", ["reservation_id"], {"reservation_id": "507f1f77bcf86cd799439011"}),
]


class FakeDoc:
    def __init__(self, **kwargs: Any) -> None:
        for k, v in kwargs.items():
            setattr(self, k, v)

    async def insert(self) -> None:
        self.id = "fake-id"

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
        self.calls = 0
        self.last_kwargs: dict[str, Any] = {}

    async def plan(self, **kwargs: Any) -> AssistantPlan:
        self.calls += 1
        self.last_kwargs = kwargs
        if self._plan is None:
            return AssistantPlan(
                action=AssistantAction.FINAL_RESPONSE,
                confidence=0.4,
                user_goal="No debería planificar en este flujo.",
                audit_summary="Planner no esperado.",
                response="No entendí.",
            )
        return self._plan


def _build_session(**overrides: Any) -> Any:
    async def noop_save() -> None:
        pass

    data = {
        "id": "ses-voice",
        "channel": "admin_api",
        "conversation_key": "mobile-voice-1",
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


def _make_create_plan(tool_name: str, **arguments: Any) -> AssistantPlan:
    return AssistantPlan(
        action=AssistantAction.TOOL_CALL,
        confidence=0.95,
        tool_name=tool_name,
        arguments=ToolArgs(**arguments),
        risk_level=RiskLevel.LOW,
        user_goal="Crear entidad por voz.",
        audit_summary="Plan de creación admin.",
    )


def _wire_session(monkeypatch: pytest.MonkeyPatch, session: Any) -> None:
    monkeypatch.setattr("app.ai.assistant.orchestrator.ConversationTurnDocument", FindableFakeDoc)
    monkeypatch.setattr("app.ai.assistant.orchestrator.ToolCallLogDocument", FakeDoc)

    async def fake_load_session(self: Any, **_: Any) -> Any:
        return session

    monkeypatch.setattr(AssistantOrchestrator, "_load_or_create_session", fake_load_session)


# ── Intent router: lenguaje natural ───────────────────────────────────────


@pytest.mark.parametrize("utterance,tool", NL_LIST_CASES)
def test_nl_list_intents(utterance: str, tool: str) -> None:
    plan = detect_and_build_plan(user_message=utterance, channel="admin_api")
    assert plan is not None, f"sin match para: {utterance!r}"
    assert plan.tool_name == tool
    assert plan.action == AssistantAction.TOOL_CALL


@pytest.mark.parametrize("utterance,tool", NL_CREATE_CASES)
def test_nl_create_intents(utterance: str, tool: str) -> None:
    plan = detect_and_build_plan(user_message=utterance, channel="admin_api")
    assert plan is not None, f"sin match para: {utterance!r}"
    assert plan.tool_name == tool


def test_nl_create_user_extracts_name_and_email() -> None:
    plan = detect_and_build_plan(
        user_message="crea un usuario llamado Ana Pérez correo ana@lajuana.co",
        channel="admin_api",
    )
    assert plan is not None
    assert plan.tool_name == "admin_create_user"
    assert plan.arguments.email == "ana@lajuana.co"
    assert plan.arguments.full_name
    assert "correo" not in plan.arguments.full_name.lower()


def test_nl_incomplete_create_user_has_no_email() -> None:
    plan = detect_and_build_plan(
        user_message="crea un usuario llamado Juan",
        channel="admin_api",
    )
    assert plan is not None
    assert plan.arguments.email is None
    assert plan.arguments.full_name


def test_stt_pauses_and_fillers_still_match_create() -> None:
    plan = detect_and_build_plan(
        user_message="ehh crea un usuario este llamado Ana",
        channel="admin_api",
    )
    assert plan is not None
    assert plan.tool_name == "admin_create_user"


def test_whatsapp_does_not_steal_admin_list_experiences() -> None:
    plan = detect_and_build_plan(
        user_message="listame las experiencias",
        channel="whatsapp",
    )
    assert plan is not None
    assert plan.tool_name == "list_experiences"


# ── Slots: respuestas cortas después de una pausa ─────────────────────────


@pytest.mark.parametrize("utterance,missing,expected", SLOT_PAUSE_CASES)
def test_slot_updates_after_pause(
    utterance: str, missing: list[str], expected: dict[str, Any]
) -> None:
    updates = _extract_slot_updates(utterance, missing)
    for key, value in expected.items():
        assert updates.get(key) == value, updates


def test_resume_after_pause_keeps_active_tool() -> None:
    session = _build_session(
        slot_values={"_active_tool_name": "admin_create_user", "full_name": "Ana Pérez"},
        pending_fields=["email"],
    )
    plan = _resume_active_admin_tool("el correo es ana@lajuana.co", session)
    assert plan is not None
    assert plan.tool_name == "admin_create_user"
    assert plan.arguments.email == "ana@lajuana.co"
    assert plan.arguments.full_name == "Ana Pérez"


def test_resume_ignores_unrelated_chatter() -> None:
    session = _build_session(
        slot_values={"_active_tool_name": "admin_create_user", "full_name": "Ana"},
        pending_fields=["email"],
    )
    plan = _resume_active_admin_tool("espera un momento", session)
    assert plan is None


# ── Policy: información incompleta ────────────────────────────────────────


def test_policy_asks_email_not_password_for_create_user() -> None:
    plan = _make_create_plan("admin_create_user", full_name="Ana Pérez")
    decision = ToolPolicyEngine().validate(plan, channel="admin_api")
    assert decision.allowed is False
    assert decision.reason == "missing_required_arguments:email"


def test_policy_create_user_complete_without_password() -> None:
    plan = _make_create_plan(
        "admin_create_user", full_name="Ana Pérez", email="ana@lajuana.co"
    )
    decision = ToolPolicyEngine().validate(plan, channel="admin_api")
    assert decision.allowed is True


def test_policy_create_experience_incomplete() -> None:
    plan = _make_create_plan("admin_create_experience", name="Bosque")
    decision = ToolPolicyEngine().validate(plan, channel="admin_api")
    assert decision.allowed is False
    assert decision.reason
    assert "description" in decision.reason
    assert "level" in decision.reason
    assert "duration_hours" in decision.reason


def test_policy_create_provider_needs_type() -> None:
    plan = _make_create_plan("admin_create_provider", name="Finca El Roble")
    decision = ToolPolicyEngine().validate(plan, channel="admin_api")
    assert decision.allowed is False
    assert decision.reason == "missing_required_arguments:name,type"


# ── Orquestador: pausa + completar + confirmar ────────────────────────────


def test_create_user_incomplete_then_pause_then_confirm(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = _build_session()
    _wire_session(monkeypatch, session)
    registry_calls: list[str] = []

    async def fake_registry_call(tool_name: str, /, **kwargs: Any) -> dict[str, Any]:
        registry_calls.append(tool_name)
        return {
            "created": True,
            "message": "Usuario 'ana@lajuana.co' creado exitosamente con rol guide. "
            "Contraseña temporal: abc. Pídele que la cambie al entrar.",
            "email": "ana@lajuana.co",
        }

    monkeypatch.setattr("app.ai.assistant.orchestrator.registry.call", fake_registry_call)

    orch = AssistantOrchestrator(planner=MockPlanner())

    async def run() -> tuple[Any, Any, Any]:
        first = await orch.ask(
            AskRequest(
                message="crea un usuario llamado Ana Pérez",
                channel="admin_api",
                conversation_id="mobile-voice-1",
            )
        )
        # Pausa: el admin cierra el sheet, vuelve y dicta solo el correo.
        second = await orch.ask(
            AskRequest(
                message="el correo es ana@lajuana.co",
                channel="admin_api",
                conversation_id="mobile-voice-1",
            )
        )
        third = await orch.ask(
            AskRequest(
                message="sí",
                channel="admin_api",
                conversation_id="mobile-voice-1",
            )
        )
        return first, second, third

    first, second, third = asyncio.run(run())

    assert first.action == AssistantAction.ASK_CLARIFYING_QUESTION
    assert first.needs_confirmation is False
    assert first.tool_name == "admin_create_user"
    assert "correo" in first.response.lower() or "email" in first.response.lower()

    assert second.action == AssistantAction.ASK_CLARIFYING_QUESTION
    assert second.needs_confirmation is True
    assert "ana@lajuana.co" in second.response.lower() or "ana" in second.response.lower()

    assert third.action == AssistantAction.TOOL_CALL
    assert third.tool_name == "admin_create_user"
    assert registry_calls == ["admin_create_user"]
    assert "creado" in third.response.lower()


def test_create_user_cancel_after_pause(monkeypatch: pytest.MonkeyPatch) -> None:
    session = _build_session()
    _wire_session(monkeypatch, session)
    registry_calls: list[str] = []

    async def fake_registry_call(tool_name: str, /, **kwargs: Any) -> dict[str, Any]:
        registry_calls.append(tool_name)
        return {"created": True, "message": "no debería ejecutarse"}

    monkeypatch.setattr("app.ai.assistant.orchestrator.registry.call", fake_registry_call)
    orch = AssistantOrchestrator(planner=MockPlanner())

    async def run() -> tuple[Any, Any, Any]:
        first = await orch.ask(
            AskRequest(
                message="crea un usuario llamado Ana Pérez correo ana@lajuana.co",
                channel="admin_api",
                conversation_id="mobile-voice-2",
            )
        )
        second = await orch.ask(
            AskRequest(message="no", channel="admin_api", conversation_id="mobile-voice-2")
        )
        return first, second, session.slot_values.get("_pending_tool_name")

    first, second, pending = asyncio.run(run())
    assert first.needs_confirmation is True
    assert second.action == AssistantAction.FINAL_RESPONSE
    assert pending is None
    assert not registry_calls


def test_new_intent_after_incomplete_create_does_not_keep_filling(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = _build_session()
    _wire_session(monkeypatch, session)

    async def fake_registry_call(tool_name: str, /, **kwargs: Any) -> dict[str, Any]:
        return {"users": [], "total": 0, "message": "No hay usuarios."}

    monkeypatch.setattr("app.ai.assistant.orchestrator.registry.call", fake_registry_call)

    async def fake_compose(**kwargs: Any) -> str:
        tool_output = kwargs.get("tool_output") or {}
        return str(tool_output.get("message") or "Listado listo.")

    monkeypatch.setattr("app.ai.assistant.orchestrator.compose_tool_response", fake_compose)
    orch = AssistantOrchestrator(planner=MockPlanner())

    async def run() -> tuple[Any, Any]:
        first = await orch.ask(
            AskRequest(
                message="crea un usuario llamado Ana",
                channel="admin_api",
                conversation_id="mobile-voice-3",
            )
        )
        second = await orch.ask(
            AskRequest(
                message="listar usuarios",
                channel="admin_api",
                conversation_id="mobile-voice-3",
            )
        )
        return first, second

    first, second = asyncio.run(run())
    assert first.needs_confirmation is False
    assert second.tool_name == "admin_list_users"
    assert second.action == AssistantAction.TOOL_CALL
    assert session.slot_values.get("_active_tool_name") is None
