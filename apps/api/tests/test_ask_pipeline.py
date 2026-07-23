from __future__ import annotations

import asyncio
from types import SimpleNamespace
from typing import Any

import pytest

from app.ai.assistant.orchestrator import AssistantOrchestrator
from app.schemas.ask import AskRequest
from app.schemas.assistant_plan import AssistantAction, AssistantPlan, RiskLevel, ToolResultResponse


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
            sort=lambda _: SimpleNamespace(
                limit=lambda _: SimpleNamespace(to_list=_empty_turn_list)
            )  # noqa: E501
        )


def _make_plan(**overrides: Any) -> AssistantPlan:
    data = {
        "action": AssistantAction.FINAL_RESPONSE,
        "confidence": 0.95,
        "tool_name": None,
        "arguments": {},
        "risk_level": RiskLevel.LOW,
        "user_goal": "Test.",
        "audit_summary": "Test.",
    }
    data.update(overrides)
    return AssistantPlan(**data)


class MockPlanner:
    def __init__(self, plan: AssistantPlan) -> None:
        self._plan = plan
        self.calls = 0

    async def plan(self, **kwargs: Any) -> AssistantPlan:
        self.calls += 1
        return self._plan


def _build_session(**overrides: Any) -> Any:
    async def noop_save() -> None:
        pass

    data = {
        "id": "ses-001",
        "channel": "test",
        "conversation_key": "demo-key",
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


def _apply_mocks(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.ai.assistant.orchestrator.ConversationTurnDocument", FindableFakeDoc)
    monkeypatch.setattr("app.ai.assistant.orchestrator.ToolCallLogDocument", FakeDoc)

    async def fake_load_session(self: Any, **_: Any) -> Any:
        return _build_session()

    monkeypatch.setattr(
        AssistantOrchestrator,
        "_load_or_create_session",
        fake_load_session,
    )

    async def fake_generate_structured(**kwargs: Any) -> ToolResultResponse:
        return ToolResultResponse(response="Ok.", audit_summary="Test.")

    monkeypatch.setattr(
        "app.ai.assistant.response_composer.get_llm_provider",
        lambda: SimpleNamespace(generate_structured=fake_generate_structured),
    )


def _apply_registry_mock(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_call(name: str, **kwargs: Any) -> dict[str, Any]:
        if name == "list_experiences":
            return {"experiences": [], "total": 0}
        if name == "check_experience_availability":
            return {
                "available": True,
                "experience_id": "exp-001",
                "experience_name": "Los Chorros",
                "requested_date": "2026-06-20",
                "participant_count": 4,
                "capacity_available": 4,
            }
        return {}

    monkeypatch.setattr("app.ai.assistant.orchestrator.registry.call", fake_call)


def test_ask_catalog_inquiry_calls_list_experiences(monkeypatch: pytest.MonkeyPatch) -> None:
    _apply_mocks(monkeypatch)
    _apply_registry_mock(monkeypatch)

    plan = _make_plan(
        action=AssistantAction.TOOL_CALL,
        tool_name="list_experiences",
        arguments={"limit": 20},
    )
    orch = AssistantOrchestrator(planner=MockPlanner(plan))

    async def run() -> Any:
        return await orch.ask(
            AskRequest(message="qu\u00e9 ofrecen", channel="test", conversation_id="demo-001")
        )

    result = asyncio.run(run())
    assert result.action == AssistantAction.TOOL_CALL
    assert result.tool_name == "list_experiences"
    assert "experiences" in result.tool_output


def test_ask_missing_fields_updates_session(monkeypatch: pytest.MonkeyPatch) -> None:
    _apply_mocks(monkeypatch)

    plan = _make_plan(
        action=AssistantAction.ASK_CLARIFYING_QUESTION,
        tool_name=None,
        arguments={"experience_query": "los chorros"},
        missing_fields=["requested_date", "participant_count"],
        response="\u00bfPara qu\u00e9 fecha y cu\u00e1ntas personas?",
    )
    orch = AssistantOrchestrator(planner=MockPlanner(plan))

    async def run() -> Any:
        return await orch.ask(
            AskRequest(
                message="quiero reservar los chorros", channel="test", conversation_id="demo-002"
            )
        )

    result = asyncio.run(run())
    assert result.action == AssistantAction.ASK_CLARIFYING_QUESTION
    assert "requested_date" in result.planner_output.get("missing_fields", [])
    assert "participant_count" in result.planner_output.get("missing_fields", [])


def test_ask_next_turn_merges_slots_and_calls_availability(monkeypatch: pytest.MonkeyPatch) -> None:
    _apply_mocks(monkeypatch)
    _apply_registry_mock(monkeypatch)
    monkeypatch.setattr("app.ai.assistant.orchestrator.detect_and_build_plan", lambda **_: None)

    plan = _make_plan(
        action=AssistantAction.TOOL_CALL,
        tool_name="check_experience_availability",
        arguments={
            "experience_query": "los chorros",
            "requested_date": "2026-08-20",
            "participant_count": 4,
        },
    )
    orch = AssistantOrchestrator(planner=MockPlanner(plan))

    async def run() -> Any:
        return await orch.ask(
            AskRequest(
                message="4 personas el 20 de agosto de 2026",
                channel="test",
                conversation_id="demo-003",
            )
        )

    result = asyncio.run(run())
    assert result.action == AssistantAction.TOOL_CALL
    assert result.tool_name == "check_experience_availability"


def test_policy_blocks_critical_tool(monkeypatch: pytest.MonkeyPatch) -> None:
    _apply_mocks(monkeypatch)

    plan = _make_plan(
        action=AssistantAction.TOOL_CALL,
        tool_name="confirm_reservation",
        arguments={"reservation_id": "abc"},
        user_goal="Confirmar reserva.",
        audit_summary="Confirmar.",
    )
    orch = AssistantOrchestrator(planner=MockPlanner(plan))

    async def run() -> Any:
        return await orch.ask(
            AskRequest(message="confirma mi reserva", channel="test", conversation_id="demo-004")
        )

    result = asyncio.run(run())
    assert result.action == AssistantAction.ASK_CLARIFYING_QUESTION


def test_policy_allows_generate_participant_form_link(monkeypatch: pytest.MonkeyPatch) -> None:
    """Policy must allow generate_participant_form_link (added to LIMITED_WRITE_TOOLS)."""
    _apply_mocks(monkeypatch)

    plan = _make_plan(
        action=AssistantAction.TOOL_CALL,
        tool_name="generate_participant_form_link",
        arguments={"reservation_id": "660000000000000000000001"},
    )
    orch = AssistantOrchestrator(planner=MockPlanner(plan))

    async def run() -> Any:
        return await orch.ask(
            AskRequest(
                message="genera link formulario",
                channel="test",
                conversation_id="demo-006",
            )
        )

    result = asyncio.run(run())
    assert result.action == AssistantAction.TOOL_CALL
    assert result.tool_name == "generate_participant_form_link"


def test_policy_allows_get_participant_form_status(monkeypatch: pytest.MonkeyPatch) -> None:
    """Policy must allow get_participant_form_status (added to LIMITED_WRITE_TOOLS)."""
    _apply_mocks(monkeypatch)
    monkeypatch.setattr("app.ai.assistant.orchestrator.detect_and_build_plan", lambda **_: None)

    plan = _make_plan(
        action=AssistantAction.TOOL_CALL,
        tool_name="get_participant_form_status",
        arguments={"reservation_id": "660000000000000000000001"},
    )
    orch = AssistantOrchestrator(planner=MockPlanner(plan))

    async def run() -> Any:
        return await orch.ask(
            AskRequest(
                message="estado formulario",
                channel="test",
                conversation_id="demo-007",
            )
        )

    result = asyncio.run(run())
    assert result.action == AssistantAction.TOOL_CALL
    assert result.tool_name == "get_participant_form_status"


def test_ask_generate_participant_form_link_returns_form_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Chatbot calling generate_participant_form_link tool returns form_url in output."""
    _apply_mocks(monkeypatch)

    async def fake_registry_call(name: str, **kwargs: Any) -> dict[str, Any]:
        if name == "generate_participant_form_link":
            return {
                "generated": True,
                "form_url": "http://test/form?t=fake-token",
                "reservation_id": "660000000000000000000001",
                "participant_limit": 2,
                "participants_registered": 0,
                "participants_remaining": 2,
            }
        return {}

    monkeypatch.setattr("app.ai.assistant.orchestrator.registry.call", fake_registry_call)

    plan = _make_plan(
        action=AssistantAction.TOOL_CALL,
        tool_name="generate_participant_form_link",
        arguments={"reservation_id": "660000000000000000000001"},
    )
    orch = AssistantOrchestrator(planner=MockPlanner(plan))

    async def run() -> Any:
        return await orch.ask(
            AskRequest(
                message="genera link formulario",
                channel="test",
                conversation_id="demo-008",
            )
        )

    result = asyncio.run(run())
    assert result.action == AssistantAction.TOOL_CALL
    assert result.tool_name == "generate_participant_form_link"
    assert "form_url" in result.tool_output
    assert "fake-token" in result.tool_output["form_url"]


def test_ask_get_participant_form_status_returns_status(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Chatbot calling get_participant_form_status tool returns form status."""
    _apply_mocks(monkeypatch)
    monkeypatch.setattr("app.ai.assistant.orchestrator.detect_and_build_plan", lambda **_: None)

    async def fake_registry_call(name: str, **kwargs: Any) -> dict[str, Any]:
        if name == "get_participant_form_status":
            return {
                "found": True,
                "participant_limit": 2,
                "participants_registered": 1,
                "participants_remaining": 1,
                "form_status": "partial",
            }
        return {}

    monkeypatch.setattr("app.ai.assistant.orchestrator.registry.call", fake_registry_call)

    plan = _make_plan(
        action=AssistantAction.TOOL_CALL,
        tool_name="get_participant_form_status",
        arguments={"reservation_id": "660000000000000000000001"},
    )
    orch = AssistantOrchestrator(planner=MockPlanner(plan))

    async def run() -> Any:
        return await orch.ask(
            AskRequest(
                message="estado formulario",
                channel="test",
                conversation_id="demo-009",
            )
        )

    result = asyncio.run(run())
    assert result.action == AssistantAction.TOOL_CALL
    assert result.tool_name == "get_participant_form_status"
    assert result.tool_output.get("found") is True
    assert result.tool_output.get("participants_registered") == 1


def test_tool_call_log_is_created(monkeypatch: pytest.MonkeyPatch) -> None:
    _apply_mocks(monkeypatch)
    _apply_registry_mock(monkeypatch)

    insert_called: list[bool] = []

    class TrackingLogDoc(FakeDoc):
        async def insert(self) -> None:
            insert_called.append(True)
            assert self.tool_name == "list_experiences"
            self.id = "log-001"

    monkeypatch.setattr("app.ai.assistant.orchestrator.ToolCallLogDocument", TrackingLogDoc)

    plan = _make_plan(
        action=AssistantAction.TOOL_CALL,
        tool_name="list_experiences",
        arguments={"limit": 20},
    )
    orch = AssistantOrchestrator(planner=MockPlanner(plan))

    async def run() -> Any:
        return await orch.ask(
            AskRequest(message="qu\u00e9 ofrecen", channel="test", conversation_id="demo-005")
        )

    asyncio.run(run())
    assert len(insert_called) == 1


def test_destructive_tool_requires_explicit_confirmation(monkeypatch: pytest.MonkeyPatch) -> None:
    _apply_mocks(monkeypatch)
    monkeypatch.setattr("app.ai.assistant.orchestrator.detect_and_build_plan", lambda **_: None)

    planner = MockPlanner(
        _make_plan(
            action=AssistantAction.TOOL_CALL,
            tool_name="admin_cancel_reservation",
            arguments={"reservation_code": "RES-001"},
        )
    )
    orch = AssistantOrchestrator(planner=planner)
    orch._policy = SimpleNamespace(validate=lambda *args, **kwargs: SimpleNamespace(allowed=True))

    async def run() -> Any:
        return await orch.ask(
            AskRequest(
                message="cancela la reserva RES-001", channel="test", conversation_id="demo-010"
            )
        )

    result = asyncio.run(run())
    assert planner.calls == 1
    assert result.action == AssistantAction.ASK_CLARIFYING_QUESTION
    assert result.tool_name == "admin_cancel_reservation"
    assert "está lista" in result.response
    assert "solo necesita tu confirmación" in result.response
    assert "Responde 'sí'" in result.response


def test_confirmation_reply_executes_pending_tool_without_replanning(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = _build_session()

    monkeypatch.setattr("app.ai.assistant.orchestrator.ConversationTurnDocument", FindableFakeDoc)
    monkeypatch.setattr("app.ai.assistant.orchestrator.ToolCallLogDocument", FakeDoc)
    monkeypatch.setattr("app.ai.assistant.orchestrator.detect_and_build_plan", lambda **_: None)

    async def fake_load_session(self: Any, **_: Any) -> Any:
        return session

    monkeypatch.setattr(AssistantOrchestrator, "_load_or_create_session", fake_load_session)

    registry_calls: list[tuple[str, dict[str, Any]]] = []

    async def fake_registry_call(name: str, **kwargs: Any) -> dict[str, Any]:
        registry_calls.append((name, kwargs))
        return {"message": "Reserva cancelada en backend.", "reservation_code": "RES-001"}

    monkeypatch.setattr("app.ai.assistant.orchestrator.registry.call", fake_registry_call)

    planner = MockPlanner(
        _make_plan(
            action=AssistantAction.TOOL_CALL,
            tool_name="admin_cancel_reservation",
            arguments={"reservation_code": "RES-001"},
        )
    )
    orch = AssistantOrchestrator(planner=planner)
    orch._policy = SimpleNamespace(validate=lambda *args, **kwargs: SimpleNamespace(allowed=True))

    async def run_flow() -> tuple[Any, Any]:
        first = await orch.ask(
            AskRequest(
                message="cancela la reserva RES-001", channel="test", conversation_id="demo-011"
            )
        )
        second = await orch.ask(
            AskRequest(message="sí, hazlo", channel="test", conversation_id="demo-011")
        )
        return first, second

    first_result, second_result = asyncio.run(run_flow())

    assert first_result.action == AssistantAction.ASK_CLARIFYING_QUESTION
    assert planner.calls == 1
    assert len(registry_calls) == 1
    assert registry_calls[0][0] == "admin_cancel_reservation"
    assert second_result.action == AssistantAction.TOOL_CALL
    assert second_result.tool_name == "admin_cancel_reservation"
    assert second_result.response == "Reserva cancelada en backend."
    assert second_result.planner_output == {}
    assert session.slot_values.get("_pending_tool_name") is None


def test_confirmation_reply_uses_blocking_reason_message(monkeypatch: pytest.MonkeyPatch) -> None:
    session = _build_session()

    monkeypatch.setattr("app.ai.assistant.orchestrator.ConversationTurnDocument", FindableFakeDoc)
    monkeypatch.setattr("app.ai.assistant.orchestrator.ToolCallLogDocument", FakeDoc)
    monkeypatch.setattr("app.ai.assistant.orchestrator.detect_and_build_plan", lambda **_: None)

    async def fake_load_session(self: Any, **_: Any) -> Any:
        return session

    monkeypatch.setattr(AssistantOrchestrator, "_load_or_create_session", fake_load_session)

    async def fake_registry_call(name: str, **kwargs: Any) -> dict[str, Any]:
        assert name == "admin_deactivate_user"
        return {
            "deactivated": False,
            "blocking_reasons": [
                {
                    "code": "user.self_delete_forbidden",
                    "message": "No puedes desactivar tu propia cuenta.",
                }
            ],
        }

    monkeypatch.setattr("app.ai.assistant.orchestrator.registry.call", fake_registry_call)

    planner = MockPlanner(
        _make_plan(
            action=AssistantAction.TOOL_CALL,
            tool_name="admin_deactivate_user",
            arguments={"user_id": "660000000000000000000001"},
        )
    )
    orch = AssistantOrchestrator(planner=planner)
    orch._policy = SimpleNamespace(validate=lambda *args, **kwargs: SimpleNamespace(allowed=True))

    async def run_flow() -> tuple[Any, Any]:
        first = await orch.ask(
            AskRequest(
                message="borra user_id 660000000000000000000001",
                channel="admin_api",
                conversation_id="demo-011b",
            )
        )
        second = await orch.ask(
            AskRequest(message="sí", channel="admin_api", conversation_id="demo-011b")
        )
        return first, second

    first_result, second_result = asyncio.run(run_flow())

    assert first_result.action == AssistantAction.ASK_CLARIFYING_QUESTION
    assert second_result.response == "No puedes desactivar tu propia cuenta."


def test_admin_user_reference_is_resolved_before_confirmation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _apply_mocks(monkeypatch)

    async def fake_resolve_user_reference(self: Any, reference: str) -> dict[str, Any]:
        assert reference == "eduardo"
        return {
            "status": "resolved",
            "reference": reference,
            "user_id": "660000000000000000000055",
            "label": "Eduardo Perez <eduardo@example.com>",
        }

    monkeypatch.setattr(
        "app.ai.assistant.orchestrator.UserService.resolve_user_reference",
        fake_resolve_user_reference,
    )

    planner = MockPlanner(_make_plan())
    orch = AssistantOrchestrator(planner=planner)
    orch._policy = SimpleNamespace(validate=lambda *args, **kwargs: SimpleNamespace(allowed=True))

    async def run() -> Any:
        return await orch.ask(
            AskRequest(
                message="borra el usuario eduardo",
                channel="admin_api",
                conversation_id="demo-010a",
            )
        )

    result = asyncio.run(run())
    assert planner.calls == 0
    assert result.action == AssistantAction.ASK_CLARIFYING_QUESTION
    assert result.tool_name == "admin_deactivate_user"
    assert result.planner_output["arguments"]["user_id"] == "660000000000000000000055"
    assert result.response.startswith("La acción desactivar usuario está lista")


def test_admin_user_reference_ambiguous_asks_clarifying_question(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _apply_mocks(monkeypatch)

    async def fake_resolve_user_reference(self: Any, reference: str) -> dict[str, Any]:
        return {
            "status": "ambiguous",
            "reference": reference,
            "matches": [
                {
                    "user_id": "660000000000000000000055",
                    "email": "eduardo@example.com",
                    "full_name": "Eduardo Perez",
                    "is_active": True,
                },
                {
                    "user_id": "660000000000000000000056",
                    "email": "eduardo.gomez@example.com",
                    "full_name": "Eduardo Gomez",
                    "is_active": True,
                },
            ],
        }

    monkeypatch.setattr(
        "app.ai.assistant.orchestrator.UserService.resolve_user_reference",
        fake_resolve_user_reference,
    )

    planner = MockPlanner(_make_plan())
    orch = AssistantOrchestrator(planner=planner)
    orch._policy = SimpleNamespace(validate=lambda *args, **kwargs: SimpleNamespace(allowed=True))

    async def run() -> Any:
        return await orch.ask(
            AskRequest(
                message="borra el usuario eduardo",
                channel="admin_api",
                conversation_id="demo-010b",
            )
        )

    result = asyncio.run(run())
    assert result.action == AssistantAction.ASK_CLARIFYING_QUESTION
    assert result.tool_name == "admin_deactivate_user"
    assert "Encontré varios usuarios" in result.response
    assert "Eduardo Perez <eduardo@example.com>" in result.response


@pytest.mark.parametrize(
    ("message", "tool_name", "patch_target", "resolver_name", "entity_id"),
    [
        (
            "desactiva el proveedor patio central",
            "admin_deactivate_provider",
            "app.ai.assistant.orchestrator.ProviderService.resolve_provider_reference",
            "provider_id",
            "660000000000000000000201",
        ),
        (
            "borra la silla asg-22",
            "admin_deactivate_saddle",
            "app.ai.assistant.orchestrator.SaddleService.resolve_saddle_reference",
            "saddle_id",
            "660000000000000000000202",
        ),
        (
            "desactiva el equino relampago",
            "admin_deactivate_equine",
            "app.ai.assistant.orchestrator.EquineService.resolve_equine_reference",
            "equine_id",
            "660000000000000000000203",
        ),
        (
            "desactiva experiencia medio dia",
            "admin_deactivate_experience",
            "app.ai.assistant.orchestrator.ExperienceService.resolve_experience_reference",
            "experience_id",
            "660000000000000000000204",
        ),
    ],
)
def test_admin_entity_reference_is_resolved_before_confirmation(
    monkeypatch: pytest.MonkeyPatch,
    message: str,
    tool_name: str,
    patch_target: str,
    resolver_name: str,
    entity_id: str,
) -> None:
    _apply_mocks(monkeypatch)

    async def fake_resolver(self: Any, reference: str) -> dict[str, Any]:
        assert reference
        return {
            "status": "resolved",
            "reference": reference,
            resolver_name: entity_id,
            "label": reference.title(),
        }

    monkeypatch.setattr(patch_target, fake_resolver)

    planner = MockPlanner(_make_plan())
    orch = AssistantOrchestrator(planner=planner)
    orch._policy = SimpleNamespace(validate=lambda *args, **kwargs: SimpleNamespace(allowed=True))

    async def run() -> Any:
        return await orch.ask(
            AskRequest(message=message, channel="admin_api", conversation_id=f"demo-{tool_name}")
        )

    result = asyncio.run(run())
    assert planner.calls == 0
    assert result.action == AssistantAction.ASK_CLARIFYING_QUESTION
    assert result.tool_name == tool_name
    assert result.planner_output["arguments"][resolver_name] == entity_id
    assert result.response.startswith("La acción")


def test_admin_provider_reference_ambiguous_asks_clarifying_question(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _apply_mocks(monkeypatch)

    async def fake_resolve_provider_reference(self: Any, reference: str) -> dict[str, Any]:
        return {
            "status": "ambiguous",
            "reference": reference,
            "matches": [
                {
                    "provider_id": "660000000000000000000055",
                    "name": "Patio Central",
                    "slug": "patio-central",
                    "label": "Patio Central (patio-central)",
                },
                {
                    "provider_id": "660000000000000000000056",
                    "name": "Patio Centro",
                    "slug": "patio-centro",
                    "label": "Patio Centro (patio-centro)",
                },
            ],
        }

    monkeypatch.setattr(
        "app.ai.assistant.orchestrator.ProviderService.resolve_provider_reference",
        fake_resolve_provider_reference,
    )

    planner = MockPlanner(_make_plan())
    orch = AssistantOrchestrator(planner=planner)
    orch._policy = SimpleNamespace(validate=lambda *args, **kwargs: SimpleNamespace(allowed=True))

    async def run() -> Any:
        return await orch.ask(
            AskRequest(
                message="desactiva el proveedor patio central",
                channel="admin_api",
                conversation_id="demo-010c",
            )
        )

    result = asyncio.run(run())
    assert result.action == AssistantAction.ASK_CLARIFYING_QUESTION
    assert result.tool_name == "admin_deactivate_provider"
    assert "Patio Central (patio-central)" in result.response
    assert "provider_id exacto" in result.response


def test_admin_reservation_id_is_normalized_before_policy(monkeypatch: pytest.MonkeyPatch) -> None:
    _apply_mocks(monkeypatch)
    monkeypatch.setattr("app.ai.assistant.orchestrator.detect_and_build_plan", lambda **_: None)

    reservation_id = "6a14f60f51dc79122be5cc97"
    planner = MockPlanner(
        _make_plan(
            action=AssistantAction.TOOL_CALL,
            tool_name="admin_cancel_reservation",
            arguments={"reservation_code": reservation_id},
        )
    )
    orch = AssistantOrchestrator(planner=planner)
    orch._policy = SimpleNamespace(validate=lambda *args, **kwargs: SimpleNamespace(allowed=True))

    async def run() -> Any:
        return await orch.ask(
            AskRequest(
                message=f"Cancelar la reserva con reservation_id {reservation_id}",
                channel="admin_api",
                conversation_id="demo-012",
            )
        )

    result = asyncio.run(run())
    assert result.action == AssistantAction.ASK_CLARIFYING_QUESTION
    assert result.tool_name == "admin_cancel_reservation"
    assert result.planner_output["arguments"]["reservation_id"] == reservation_id


def test_admin_get_reservation_detail_accepts_code(monkeypatch: pytest.MonkeyPatch) -> None:
    _apply_mocks(monkeypatch)
    monkeypatch.setattr("app.ai.assistant.orchestrator.detect_and_build_plan", lambda **_: None)

    async def fake_registry_call(name: str, **kwargs: Any) -> dict[str, Any]:
        assert name == "admin_get_reservation_detail"
        assert kwargs["code"] == "RES-PAGO-001"
        return {"found": True, "reservation_id": "res-1", "code": "RES-PAGO-001"}

    monkeypatch.setattr("app.ai.assistant.orchestrator.registry.call", fake_registry_call)

    planner = MockPlanner(
        _make_plan(
            action=AssistantAction.TOOL_CALL,
            tool_name="admin_get_reservation_detail",
            arguments={"code": "RES-PAGO-001"},
        )
    )
    orch = AssistantOrchestrator(planner=planner)

    async def run() -> Any:
        return await orch.ask(
            AskRequest(
                message="Ver detalle de la reserva RES-PAGO-001",
                channel="admin_api",
                conversation_id="demo-013",
            )
        )

    result = asyncio.run(run())
    assert result.action == AssistantAction.TOOL_CALL
    assert result.tool_name == "admin_get_reservation_detail"
