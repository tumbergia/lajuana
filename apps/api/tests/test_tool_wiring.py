"""Contratos entre las tools registradas y lo que el asistente puede enviarles.

Gemini recibe el schema de ToolArgs sin additionalProperties, así que solo puede
emitir campos declarados ahí. Estos tests garantizan que cada tool sea invocable
de punta a punta: sus parámetros existen en ToolArgs, sus obligatorios se piden
antes de ejecutar y toda escritura pasa por confirmación.
"""

from __future__ import annotations

import asyncio
import inspect
from typing import Any

import pytest

import app.ai.mcp  # noqa: F401  (registra las tools)
from app.ai.assistant import orchestrator as orch_module
from app.ai.assistant.orchestrator import (
    REQUIRED_FIELDS_BY_TOOL,
    WRITE_TOOLS_REQUIRING_CONFIRMATION,
    AssistantOrchestrator,
    _extract_slot_updates,
)
from app.ai.assistant.policy import _WRITE_TOOL_RE, ToolPolicyEngine
from app.ai.mcp import _TOOLS
from app.ai.mcp.registry import _ARG_ALIASES, registry
from app.schemas.ask import AskRequest
from app.schemas.assistant_plan import AssistantAction, AssistantPlan, ToolArgs
from tests.test_admin_modules_pause import MockPlanner, _build_session, _wire

_INFRA_PARAMS = {"trace_id", "conversation_turn_id"}
_ALIAS_SOURCES = {target: source for source, target in _ARG_ALIASES.items()}
OID = "507f1f77bcf86cd799439011"


def _tool_params(fn: Any) -> list[inspect.Parameter]:
    return [
        p
        for p in inspect.signature(fn).parameters.values()
        if p.kind not in (p.VAR_KEYWORD, p.VAR_POSITIONAL) and p.name not in _INFRA_PARAMS
    ]


@pytest.mark.parametrize("tool_name", sorted(_TOOLS))
def test_every_tool_param_is_reachable_from_tool_args(tool_name: str) -> None:
    fields = set(ToolArgs.model_fields)
    unreachable = [
        p.name
        for p in _tool_params(_TOOLS[tool_name])
        if p.name not in fields and _ALIAS_SOURCES.get(p.name) not in fields
    ]
    assert not unreachable, f"{tool_name}: parámetros que el LLM no puede enviar: {unreachable}"


@pytest.mark.parametrize("tool_name", sorted(_TOOLS))
def test_every_tool_accepts_extra_kwargs(tool_name: str) -> None:
    # El orquestador envía todos los campos no nulos de ToolArgs a cualquier tool.
    params = inspect.signature(_TOOLS[tool_name]).parameters.values()
    assert any(p.kind == p.VAR_KEYWORD for p in params), tool_name


def test_every_admin_write_tool_requires_confirmation() -> None:
    writes = {name for name in _TOOLS if name.startswith("admin_") and _WRITE_TOOL_RE.search(name)}
    assert writes - WRITE_TOOLS_REQUIRING_CONFIRMATION == set()


def test_tool_lists_only_reference_registered_tools() -> None:
    registered = set(registry.names())
    assert WRITE_TOOLS_REQUIRING_CONFIRMATION - registered == set()
    assert set(REQUIRED_FIELDS_BY_TOOL) - registered == set()
    policy = ToolPolicyEngine
    assert (policy.CLIENT_TOOLS | policy.GUIDE_TOOLS | policy.ADMIN_TOOLS) == registered
    assert (
        registered - (policy.READ_TOOLS | policy.LIMITED_WRITE_TOOLS | policy.WRITE_TOOLS) == set()
    )


@pytest.mark.parametrize(
    "unknown",
    [
        "admin_update_schedule",
        "admin_deactivate_schedule",
        "admin_create_schedule",
        "admin_upate_user",
    ],
)
def test_autocorrect_never_lands_on_a_write_tool(unknown: str) -> None:
    engine = ToolPolicyEngine()
    allowed = engine._get_allowed_tools_for_role("admin")
    corrected = engine._autocorrect_tool_name(unknown, allowed)
    assert corrected == unknown or not _WRITE_TOOL_RE.search(corrected)


def test_autocorrect_still_fixes_read_typos() -> None:
    engine = ToolPolicyEngine()
    allowed = engine._get_allowed_tools_for_role("admin")
    assert engine._autocorrect_tool_name("admin_list_equins", allowed) == "admin_list_equines"


def _plan(tool_name: str, **args: Any) -> AssistantPlan:
    return AssistantPlan(
        action=AssistantAction.TOOL_CALL,
        confidence=0.95,
        tool_name=tool_name,
        arguments=ToolArgs(**args),
        user_goal="test",
        audit_summary="test",
    )


@pytest.mark.parametrize(
    "tool_name,args,missing",
    [
        ("admin_update_equine_availability", {"equine_id": OID}, "is_available,reason"),
        ("guide_report_incident", {"reservation_id": OID}, "severity,description"),
        ("admin_update_saddle", {}, "saddle_id"),
        ("admin_delete_assignment", {}, "assignment_id"),
    ],
)
def test_policy_blocks_missing_signature_args(
    tool_name: str, args: dict[str, Any], missing: str
) -> None:
    decision = ToolPolicyEngine().validate(_plan(tool_name, **args), channel="admin_api")
    assert decision.allowed is False
    assert decision.reason == f"missing_required_arguments:{missing}"


def test_update_rules_without_values_is_blocked() -> None:
    # ToolArgs declara los campos de reglas, así que model_dump() los trae como None.
    decision = ToolPolicyEngine().validate(
        _plan("admin_update_reservation_rules"), channel="admin_api"
    )
    assert decision.allowed is False
    plan = _plan("admin_update_reservation_rules", min_days_in_advance=2)
    assert ToolPolicyEngine().validate(plan, channel="admin_api").allowed is True


def test_policy_allows_false_boolean_as_present() -> None:
    plan = _plan(
        "admin_update_equine_availability", equine_id=OID, is_available=False, reason="cojea"
    )
    assert ToolPolicyEngine().validate(plan, channel="admin_api").allowed is True


def test_registry_maps_notes_to_note() -> None:
    received: dict[str, Any] = {}

    async def fake_tool(payment_proof_id: str, note: str | None = None, **_: Any) -> dict:
        received.update(payment_proof_id=payment_proof_id, note=note)
        return {"ok": True}

    registry._tools["__test_note_tool"] = fake_tool
    try:
        asyncio.run(registry.call("__test_note_tool", payment_proof_id="p1", notes="ok banco"))
    finally:
        registry._tools.pop("__test_note_tool")
    assert received == {"payment_proof_id": "p1", "note": "ok banco"}


@pytest.mark.parametrize(
    "message,expected",
    [
        ("déjalo no disponible", False),
        ("ponlo disponible", True),
    ],
)
def test_slot_extracts_availability(message: str, expected: bool) -> None:
    assert _extract_slot_updates(message, ["is_available"]) == {"is_available": expected}


def test_slot_extracts_severity() -> None:
    assert _extract_slot_updates("gravedad alta", ["severity"])["severity"] == "high"


def test_equine_availability_end_to_end(monkeypatch: pytest.MonkeyPatch) -> None:
    """Planner → policy → confirmación → registry real → la tool recibe is_available=False."""
    session = _build_session()
    _wire(monkeypatch, session)
    received: dict[str, Any] = {}

    async def fake_availability(
        equine_id: str,
        is_available: bool,
        reason: str,
        trace_id: str | None = None,
        conversation_turn_id: str | None = None,
        **_: Any,
    ) -> dict[str, Any]:
        received.update(equine_id=equine_id, is_available=is_available, reason=reason)
        return {"ok": True, "message": "Disponibilidad actualizada."}

    monkeypatch.setitem(registry._tools, "admin_update_equine_availability", fake_availability)
    plan = _plan(
        "admin_update_equine_availability", equine_id=OID, is_available=False, reason="cojea"
    )
    orch = AssistantOrchestrator(planner=MockPlanner(plan))

    async def run() -> tuple[Any, Any]:
        request = AskRequest(
            message="pon a Lucero como no disponible porque cojea",
            channel="admin_api",
            conversation_id="wiring-1",
        )
        first = await orch.ask(request)
        second = await orch.ask(request.model_copy(update={"message": "sí"}))
        return first, second

    monkeypatch.setattr(orch_module, "detect_and_build_plan", lambda **_: None)
    first, second = asyncio.run(run())
    assert first.needs_confirmation is True
    assert second.action == AssistantAction.TOOL_CALL
    assert second.tool_output.get("error") is None, second.tool_output
    assert received == {"equine_id": OID, "is_available": False, "reason": "cojea"}
