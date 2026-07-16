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


class _FakeReservation:
    """Replica mínima de ReservationDocument para validar la sincronización
    de `holder_language` cuando el usuario pide explícitamente un idioma."""

    synced_phones: list[str] = []
    synced_languages: list[str] = []

    @classmethod
    def reset(cls) -> None:
        cls.synced_phones = []
        cls.synced_languages = []

    @classmethod
    def find(cls, query: dict[str, Any]) -> SimpleNamespace:
        holder_phone = query.get("holder_phone")

        async def _update_many(update: dict[str, Any]) -> Any:
            _FakeReservation.synced_phones.append(holder_phone or "")
            lang = (update.get("$set") or {}).get("holder_language")
            if lang:
                _FakeReservation.synced_languages.append(lang)
            return SimpleNamespace(modified_count=1)

        return SimpleNamespace(update_many=_update_many)


def _plan() -> AssistantPlan:
    return AssistantPlan(
        action=AssistantAction.FINAL_RESPONSE,
        confidence=0.95,
        tool_name=None,
        arguments={},
        risk_level=RiskLevel.LOW,
        user_goal="Test.",
        audit_summary="Test.",
    )


class _CapturingPlanner:
    def __init__(self) -> None:
        self.captured_language: str | None = None

    async def plan(self, **kwargs: Any) -> AssistantPlan:
        self.captured_language = kwargs.get("language")
        return _plan()


def _setup(monkeypatch: pytest.MonkeyPatch) -> _CapturingPlanner:
    monkeypatch.setattr(
        "app.ai.assistant.orchestrator.ConversationTurnDocument", _FindableTurn
    )
    monkeypatch.setattr(
        "app.ai.assistant.orchestrator.ToolCallLogDocument", _FakeLog
    )
    _FakeReservation.reset()
    monkeypatch.setattr(
        "app.ai.assistant.orchestrator.ReservationDocument", _FakeReservation
    )

    async def fake_load_session(self: Any, **_: Any) -> Any:
        async def noop_save() -> None:
            return None

        return SimpleNamespace(
            id="ses",
            language="es",
            language_override=None,
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
    return _CapturingPlanner()


def test_explicit_language_request_with_phone_does_not_crash(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Repro del bug UnboundLocalError de `phone`.

    Antes del fix, la rama `if explicit_request:` referenciaba `phone` antes de
    su asignación (línea ~333), provocando el crash que rompía el path de audio
    en `ingestion_service.py`. Este test verifica que con `from_phone` válido,
    el orchestrator procesa la petición explícita sin lanzar excepción y
    sincroniza `holder_language` en las reservas activas.
    """
    planner = _setup(monkeypatch)
    orch = AssistantOrchestrator(planner=planner)  # type: ignore[arg-type]

    async def run() -> Any:
        return await orch.ask(
            AskRequest(
                message="respóndeme en inglés por favor",
                channel="whatsapp",
                from_phone="+573138659839",
                conversation_id="demo-phone-1",
            )
        )

    response = asyncio.run(run())

    # Sin crash, respuesta coherente en el idioma solicitado.
    assert response.response is not None
    assert planner.captured_language == "en"

    # La sincronización de holder_language debe haberse disparado.
    assert _FakeReservation.synced_phones == ["+573138659839"]
    assert _FakeReservation.synced_languages == ["en"]


def test_explicit_language_request_without_phone_does_not_crash(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Variante sin `from_phone`: la sincronización de reservas se omite
    silenciosamente (no hay crash) y el idioma sí cambia en la sesión."""
    planner = _setup(monkeypatch)
    orch = AssistantOrchestrator(planner=planner)  # type: ignore[arg-type]

    async def run() -> Any:
        return await orch.ask(
            AskRequest(
                message="respóndeme en inglés por favor",
                channel="test",
                conversation_id="demo-phone-2",
            )
        )

    response = asyncio.run(run())
    assert response.response is not None
    assert planner.captured_language == "en"
    # Sin phone no se sincronizan reservas.
    assert _FakeReservation.synced_phones == []
