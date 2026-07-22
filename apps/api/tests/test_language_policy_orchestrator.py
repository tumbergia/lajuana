from __future__ import annotations

import asyncio
from types import SimpleNamespace
from typing import Any

import pytest

from app.ai.assistant.orchestrator import AssistantOrchestrator
from app.schemas.ask import AskRequest
from app.schemas.assistant_plan import AssistantAction, AssistantPlan, RiskLevel


class _FakeTurn:
    def __init__(self, **kwargs: Any) -> None:
        for k, v in kwargs.items():
            setattr(self, k, v)
        self.id = "turn-id"

    async def insert(self) -> None:
        return None

    async def save(self) -> None:
        return None


async def _empty_turn_list() -> list:
    return []


class _FindableTurn(_FakeTurn):
    @classmethod
    def find(cls, *args: Any, **kwargs: Any) -> SimpleNamespace:
        return SimpleNamespace(
            sort=lambda _: SimpleNamespace(
                limit=lambda _: SimpleNamespace(to_list=_empty_turn_list)
            )
        )


class _FakeLog:
    def __init__(self, **kwargs: Any) -> None:
        pass

    async def insert(self) -> None:
        return None


def _plan(**overrides: Any) -> AssistantPlan:
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


class CapturingPlanner:
    def __init__(self, plan: AssistantPlan) -> None:
        self._plan = plan
        self.captured_language: str | None = None

    async def plan(self, **kwargs: Any) -> AssistantPlan:
        self.captured_language = kwargs.get("language")
        return self._plan


def _setup(monkeypatch: pytest.MonkeyPatch, session_lang: str = "es", override: str | None = None) -> CapturingPlanner:  # noqa: E501
    monkeypatch.setattr(
        "app.ai.assistant.orchestrator.ConversationTurnDocument", _FindableTurn
    )
    monkeypatch.setattr(
        "app.ai.assistant.orchestrator.ToolCallLogDocument", _FakeLog
    )

    async def fake_load_session(self: Any, **_: Any) -> Any:
        async def noop_save() -> None:
            return None

        return SimpleNamespace(
            id="ses",
            language=session_lang,
            language_override=override,
            language_streak=0,
            language_streak_lang=None,
            pending_media_proof=None,
            from_phone=None,
            slot_values={},
            turn_count=0,
            pending_fields=[],
            last_intent=None,
            last_trace_id=None,
            updated_at=None,
            save=noop_save,
        )

    monkeypatch.setattr(AssistantOrchestrator, "_load_or_create_session", fake_load_session)
    return CapturingPlanner(_plan())


def test_bot_keeps_spanish_when_user_writes_in_english(monkeypatch: pytest.MonkeyPatch) -> None:
    planner = _setup(monkeypatch)
    orch = AssistantOrchestrator(planner=planner)

    async def run() -> Any:
        return await orch.ask(
            AskRequest(
                message="Great! To move forward with your booking, could you please provide your full name?",
                channel="whatsapp",
                conversation_id="demo-lang-1",
            )
        )

    asyncio.run(run())
    assert planner.captured_language == "es"


def test_bot_keeps_spanish_across_several_english_turns(monkeypatch: pytest.MonkeyPatch) -> None:
    planner = _setup(monkeypatch)
    orch = AssistantOrchestrator(planner=planner)

    for msg in ["yes that works", "please", "ok proceed", "fine, do it"]:

        async def run(_msg: str = msg) -> Any:
            return await orch.ask(
                AskRequest(message=_msg, channel="whatsapp", conversation_id="demo-lang-2")
            )
        asyncio.run(run())
    assert planner.captured_language == "es"


def test_bot_switches_only_on_explicit_request(monkeypatch: pytest.MonkeyPatch) -> None:
    planner = _setup(monkeypatch)
    orch = AssistantOrchestrator(planner=planner)

    async def run() -> Any:
        return await orch.ask(
            AskRequest(
                message="please reply in english from now on",
                channel="whatsapp",
                conversation_id="demo-lang-3",
            )
        )

    result = asyncio.run(run())
    # Pure language switch: ack in English without going through the planner.
    assert planner.captured_language is None
    assert "English" in (result.response or "")


def test_bot_switches_english_and_continues_when_buffer_has_reservation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Language switch + reservation in one buffered message → en and keep planning."""
    planner = _setup(monkeypatch)
    orch = AssistantOrchestrator(planner=planner)
    combined = (
        "Since this message aswer in english\n"
        "I wanna make the reservation on september 2"
    )

    async def run() -> Any:
        return await orch.ask(
            AskRequest(
                message=combined,
                channel="whatsapp",
                conversation_id="demo-lang-buffer",
            )
        )

    asyncio.run(run())
    # Planner ran (not pure-language ack) and session language was english.
    assert planner.captured_language == "en"


def test_bot_kills_english_after_explicit_spanish_request(monkeypatch: pytest.MonkeyPatch) -> None:
    planner = _setup(monkeypatch, session_lang="en", override="en")
    orch = AssistantOrchestrator(planner=planner)

    async def run() -> Any:
        return await orch.ask(
            AskRequest(
                message="respóndeme en español por favor",
                channel="whatsapp",
                conversation_id="demo-lang-4",
            )
        )

    result = asyncio.run(run())
    assert planner.captured_language is None
    assert "español" in (result.response or "").lower()