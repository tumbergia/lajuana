from __future__ import annotations

import asyncio
from types import SimpleNamespace
from typing import Any

import pytest

from app.ai.assistant.orchestrator import AssistantOrchestrator
from app.schemas.ask import AskRequest
from app.schemas.assistant_plan import AssistantAction, AssistantPlan, RiskLevel


class FakeDoc:
    def __init__(self, **kwargs: Any) -> None:
        for k, v in kwargs.items():
            setattr(self, k, v)

    async def insert(self) -> None:
        self.id = "fake-id"

    async def save(self) -> None:
        pass


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

    async def plan(self, **kwargs: Any) -> AssistantPlan:
        return self._plan


def _apply_mocks(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.ai.assistant.orchestrator.ConversationTurnDocument", FakeDoc)
    monkeypatch.setattr("app.ai.assistant.orchestrator.ToolCallLogDocument", FakeDoc)

    async def fake_load_session(self: Any, **_: Any) -> Any:
        async def noop_save() -> None:
            pass

        return SimpleNamespace(
            id="ses-001",
            channel="test",
            conversation_key="demo-key",
            status="active",
            slot_values={},
            turn_count=0,
            pending_fields=[],
            last_intent=None,
            last_trace_id=None,
            updated_at=None,
            save=noop_save,
        )

    monkeypatch.setattr(
        AssistantOrchestrator,
        "_load_or_create_session",
        fake_load_session,
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

    plan = _make_plan(
        action=AssistantAction.TOOL_CALL,
        tool_name="check_experience_availability",
        arguments={
            "experience_query": "los chorros",
            "requested_date": "2026-06-20",
            "participant_count": 4,
        },
    )
    orch = AssistantOrchestrator(planner=MockPlanner(plan))

    async def run() -> Any:
        return await orch.ask(
            AskRequest(
                message="4 personas el 20 de junio de 2026",
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


def test_conversation_turn_is_completed(monkeypatch: pytest.MonkeyPatch) -> None:
    _apply_mocks(monkeypatch)
    _apply_registry_mock(monkeypatch)

    saved_status: list[str] = []

    class TrackingTurnDoc(FakeDoc):
        async def save(self) -> None:
            saved_status.append(getattr(self, "status", "unknown"))

    monkeypatch.setattr("app.ai.assistant.orchestrator.ConversationTurnDocument", TrackingTurnDoc)

    plan = _make_plan(
        action=AssistantAction.TOOL_CALL,
        tool_name="list_experiences",
        arguments={"limit": 20},
    )
    orch = AssistantOrchestrator(planner=MockPlanner(plan))

    async def run() -> Any:
        return await orch.ask(
            AskRequest(message="qu\u00e9 ofrecen", channel="test", conversation_id="demo-006")
        )

    asyncio.run(run())
    assert "completed" in saved_status
