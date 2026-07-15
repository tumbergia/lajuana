"""Tests for the expanded LITERAL_RESPONSE_TOOLS set.

Tools in this set must return their response verbatim to the user when
their output has a 'response' field and no error/blocking_reasons.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest

from app.schemas.ask import AskRequest
from app.schemas.assistant_plan import AssistantAction, AssistantPlan, RiskLevel


def _make_planner_mock(tool_name: str) -> Any:
    """Build a planner mock that always returns a tool_call plan for the given tool.

    The plan includes the required args for each tool so the slot merge step
    doesn't downgrade the action to ask_clarifying_question.
    """
    required_args = {
        "cancel_reservation": {
            "reservation_code": "PR-TEST-001",
            "holder_phone": "+573001112233",
        },
        "update_reservation_date": {
            "reservation_code": "PR-TEST-001",
            "holder_phone": "+573001112233",
            "new_date": "2026-08-15",
        },
        "update_reservation_participants": {
            "reservation_code": "PR-TEST-001",
            "holder_phone": "+573001112233",
            "new_participant_count": 4,
        },
    }
    from app.schemas.assistant_plan import ToolArgs

    args = ToolArgs(**required_args.get(tool_name, {}))
    fake_plan = AssistantPlan(
        action=AssistantAction.TOOL_CALL,
        confidence=0.9,
        tool_name=tool_name,
        arguments=args,
        user_goal="test",
        audit_summary="test",
        risk_level=RiskLevel.LOW,
    )

    class _Planner:
        async def plan(self, **_kwargs: Any) -> AssistantPlan:
            return fake_plan

    return _Planner()


def _apply_common_mocks(monkeypatch: pytest.MonkeyPatch) -> None:
    """Apply session + turn mocks that the orchestrator needs."""

    async def fake_load_session(self: Any, **_: Any) -> Any:
        async def noop_save() -> None:
            pass

        return SimpleNamespace(
            id="ses-001",
            channel="whatsapp",
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

    from app.ai.assistant.orchestrator import AssistantOrchestrator

    monkeypatch.setattr(AssistantOrchestrator, "_load_or_create_session", fake_load_session)

    class _FakeTurnDoc:
        def __init__(self, **kwargs: Any) -> None:
            for k, v in kwargs.items():
                setattr(self, k, v)

        async def insert(self) -> None:
            self.id = "turn-001"

        async def save(self) -> None:
            pass

        @classmethod
        def find(cls, *_args: Any, **_kwargs: Any) -> SimpleNamespace:
            async def _to_list() -> list:
                return []

            chain = SimpleNamespace()
            chain.sort = lambda _f: SimpleNamespace(
                limit=lambda _n: SimpleNamespace(to_list=_to_list)
            )
            return chain

    class _FakeLogDoc:
        def __init__(self, **kwargs: Any) -> None:
            for k, v in kwargs.items():
                setattr(self, k, v)

        async def insert(self) -> None:
            self.id = "log-001"

    monkeypatch.setattr(
        "app.ai.assistant.orchestrator.ConversationTurnDocument", _FakeTurnDoc
    )
    monkeypatch.setattr(
        "app.ai.assistant.orchestrator.ToolCallLogDocument", _FakeLogDoc
    )


@pytest.mark.asyncio
async def test_cancel_reservation_literal_path(monkeypatch: pytest.MonkeyPatch) -> None:
    """cancel_reservation: response is returned verbatim when no error."""
    from app.ai.assistant.orchestrator import AssistantOrchestrator

    _apply_common_mocks(monkeypatch)
    orchestrator = AssistantOrchestrator(planner=_make_planner_mock("cancel_reservation"))

    with patch(
        "app.ai.assistant.orchestrator.registry.call",
        AsyncMock(return_value={"response": "Reserva cancelada con éxito."}),
    ):
        request = AskRequest(
            message="cancela mi reserva", channel="whatsapp", conversation_id="demo-1"
        )
        result = await orchestrator.ask(request)

    assert result.response == "Reserva cancelada con éxito."


@pytest.mark.asyncio
async def test_update_reservation_date_literal_path(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.ai.assistant.orchestrator import AssistantOrchestrator

    _apply_common_mocks(monkeypatch)
    orchestrator = AssistantOrchestrator(planner=_make_planner_mock("update_reservation_date"))

    with patch(
        "app.ai.assistant.orchestrator.registry.call",
        AsyncMock(return_value={"response": "Fecha actualizada."}),
    ):
        request = AskRequest(
            message="cambia mi fecha", channel="whatsapp", conversation_id="demo-1"
        )
        result = await orchestrator.ask(request)

    assert result.response == "Fecha actualizada."


@pytest.mark.asyncio
async def test_update_reservation_participants_literal_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.ai.assistant.orchestrator import AssistantOrchestrator

    _apply_common_mocks(monkeypatch)
    orchestrator = AssistantOrchestrator(
        planner=_make_planner_mock("update_reservation_participants")
    )

    with patch(
        "app.ai.assistant.orchestrator.registry.call",
        AsyncMock(return_value={"response": "Participantes actualizados."}),
    ):
        request = AskRequest(
            message="cambia los participantes", channel="whatsapp", conversation_id="demo-1"
        )
        result = await orchestrator.ask(request)

    assert result.response == "Participantes actualizados."


@pytest.mark.asyncio
async def test_literal_tool_falls_back_to_composer_on_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """If the tool returns an error, we must NOT use the literal response path."""
    from app.ai.assistant.orchestrator import AssistantOrchestrator

    _apply_common_mocks(monkeypatch)
    orchestrator = AssistantOrchestrator(planner=_make_planner_mock("cancel_reservation"))

    with patch(
        "app.ai.assistant.orchestrator.registry.call",
        AsyncMock(
            return_value={
                "error": "no_se_pudo",
                "response": "Mensaje literal que NO deberíamos enviar.",
            }
        ),
    ), patch(
        "app.ai.assistant.orchestrator.compose_tool_response",
        AsyncMock(return_value="Mensaje re-formateado por el composer."),
    ):
        request = AskRequest(
            message="cancela mi reserva", channel="whatsapp", conversation_id="demo-1"
        )
        result = await orchestrator.ask(request)

    assert result.response == "Mensaje re-formateado por el composer."


@pytest.mark.asyncio
async def test_literal_tool_falls_back_to_composer_on_blocking_reasons(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """If the tool returns blocking_reasons, we must NOT use the literal path."""
    from app.ai.assistant.orchestrator import AssistantOrchestrator

    _apply_common_mocks(monkeypatch)
    orchestrator = AssistantOrchestrator(planner=_make_planner_mock("cancel_reservation"))

    with patch(
        "app.ai.assistant.orchestrator.registry.call",
        AsyncMock(
            return_value={
                "blocking_reasons": [{"code": "payment_done", "message": "Ya pagaste"}],
                "response": "Literal que NO deberíamos enviar.",
            }
        ),
    ), patch(
        "app.ai.assistant.orchestrator.compose_tool_response",
        AsyncMock(return_value="Mensaje re-formateado."),
    ):
        request = AskRequest(
            message="cancela mi reserva", channel="whatsapp", conversation_id="demo-1"
        )
        result = await orchestrator.ask(request)

    assert result.response == "Mensaje re-formateado."
