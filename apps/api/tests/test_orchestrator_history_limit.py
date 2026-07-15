"""Tests for the history limit per channel in AssistantOrchestrator.

The orchestrator should inject fewer turns of history on the whatsapp channel
(to save prompt tokens) and keep the larger context for admin/guide channels.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest

from app.ai.assistant.orchestrator import AssistantOrchestrator
from app.schemas.ask import AskRequest
from app.schemas.assistant_plan import AssistantAction, AssistantPlan, RiskLevel


async def _empty_turn_list() -> list:
    return []


def _make_capture_findable(captured: dict[str, int]) -> Any:
    """Return a stand-in for ConversationTurnDocument that records the limit used."""

    class FakeDoc:
        def __init__(self, **kwargs: Any) -> None:
            for k, v in kwargs.items():
                setattr(self, k, v)

        async def insert(self) -> None:
            self.id = "turn-001"

        async def save(self) -> None:
            pass

        @classmethod
        def find(cls, *_args: Any, **_kwargs: Any) -> SimpleNamespace:
            chain = SimpleNamespace()

            def _sort(_field: str) -> SimpleNamespace:
                sort_chain = SimpleNamespace()

                def _limit(n: int) -> SimpleNamespace:
                    captured["limit"] = n
                    limit_chain = SimpleNamespace()
                    limit_chain.to_list = _empty_turn_list
                    return limit_chain

                sort_chain.limit = _limit
                return sort_chain

            chain.sort = _sort
            return chain

    return FakeDoc


def _apply_session_mock(monkeypatch: pytest.MonkeyPatch) -> None:
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
            language="es",
            language_override=None,
            language_streak=0,
            language_streak_lang=None,
            pending_media_proof=None,
            save=noop_save,
        )

    monkeypatch.setattr(
        AssistantOrchestrator,
        "_load_or_create_session",
        fake_load_session,
    )


def _build_planner_for_final_response() -> Any:
    plan = AssistantPlan(
        action=AssistantAction.FINAL_RESPONSE,
        confidence=0.9,
        tool_name=None,
        user_goal="test",
        audit_summary="test",
        risk_level=RiskLevel.LOW,
    )

    class _MockPlanner:
        async def plan(self, **kwargs: Any) -> AssistantPlan:
            return plan

    return _MockPlanner()


@pytest.mark.asyncio
async def test_whatsapp_channel_uses_history_limit_4(monkeypatch: pytest.MonkeyPatch) -> None:
    """WhatsApp: limit must be 4 to save prompt tokens."""
    captured: dict[str, int] = {}
    monkeypatch.setattr(
        "app.ai.assistant.orchestrator.ConversationTurnDocument",
        _make_capture_findable(captured),
    )
    _apply_session_mock(monkeypatch)

    orchestrator = AssistantOrchestrator(planner=_build_planner_for_final_response())
    request = AskRequest(
        message="hola",
        channel="whatsapp",
        from_phone="+573001112233",
        conversation_id="whatsapp:+573001112233",
    )
    await orchestrator.ask(request)

    assert captured.get("limit") == 4, f"Expected limit=4 for whatsapp, got {captured}"


@pytest.mark.asyncio
async def test_admin_api_channel_uses_history_limit_8(monkeypatch: pytest.MonkeyPatch) -> None:
    """Admin panel: keep the larger history (8) for operator context."""
    captured: dict[str, int] = {}
    monkeypatch.setattr(
        "app.ai.assistant.orchestrator.ConversationTurnDocument",
        _make_capture_findable(captured),
    )
    _apply_session_mock(monkeypatch)

    orchestrator = AssistantOrchestrator(planner=_build_planner_for_final_response())
    request = AskRequest(
        message="hola",
        channel="admin_api",
        from_phone=None,
        conversation_id="admin:user-1",
    )
    await orchestrator.ask(request)

    assert captured.get("limit") == 8, f"Expected limit=8 for admin_api, got {captured}"


@pytest.mark.asyncio
async def test_mobile_api_channel_uses_history_limit_8(monkeypatch: pytest.MonkeyPatch) -> None:
    """Guides: keep the larger history (8) for field context."""
    captured: dict[str, int] = {}
    monkeypatch.setattr(
        "app.ai.assistant.orchestrator.ConversationTurnDocument",
        _make_capture_findable(captured),
    )
    _apply_session_mock(monkeypatch)

    orchestrator = AssistantOrchestrator(planner=_build_planner_for_final_response())
    request = AskRequest(
        message="crea bitacora",
        channel="mobile_api",
        from_phone="+573001112233",
        conversation_id="mobile:+573001112233",
    )
    await orchestrator.ask(request)

    assert captured.get("limit") == 8, f"Expected limit=8 for mobile_api, got {captured}"


@pytest.mark.asyncio
async def test_test_channel_uses_history_limit_8(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test channel (/ask endpoint): keep 8 turns of history."""
    captured: dict[str, int] = {}
    monkeypatch.setattr(
        "app.ai.assistant.orchestrator.ConversationTurnDocument",
        _make_capture_findable(captured),
    )
    _apply_session_mock(monkeypatch)

    orchestrator = AssistantOrchestrator(planner=_build_planner_for_final_response())
    request = AskRequest(
        message="hola",
        channel="test",
        conversation_id="test-1",
    )
    await orchestrator.ask(request)

    assert captured.get("limit") == 8, f"Expected limit=8 for test, got {captured}"
