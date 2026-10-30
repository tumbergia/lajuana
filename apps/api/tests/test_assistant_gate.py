"""Unit tests for AssistantGate."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.ai.assistant.assistant_gate import AssistantGate
from app.schemas.config import AiConfigurationSchema, AiRouteSchema


def _ai(*, enabled: bool, muted_phones: list[str] | None = None) -> AiConfigurationSchema:
    return AiConfigurationSchema(
        enabled=enabled,
        source="database",
        muted_phones=muted_phones or [],
        routes=[AiRouteSchema(position=i) for i in range(1, 4)],
    )


def _patch_reservations(monkeypatch: pytest.MonkeyPatch, docs: list) -> None:
    monkeypatch.setattr(
        "app.ai.assistant.assistant_gate.ReservationDocument.find",
        lambda *_a, **_k: SimpleNamespace(to_list=AsyncMock(return_value=docs)),
    )


@pytest.mark.asyncio
async def test_gate_blocks_when_globally_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_reservations(monkeypatch, [])
    config = SimpleNamespace(get_ai_configuration=AsyncMock(return_value=_ai(enabled=False)))
    gate = AssistantGate(config_service=config)  # type: ignore[arg-type]
    assert await gate.is_allowed("+573001112233") is False
    decision = await gate.evaluate("+573001112233")
    assert decision.allowed is False
    assert decision.reason == "global_disabled"


@pytest.mark.asyncio
async def test_gate_blocks_muted_phone(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_reservations(monkeypatch, [])
    config = SimpleNamespace(
        get_ai_configuration=AsyncMock(
            return_value=_ai(enabled=True, muted_phones=["+573001112233"])
        )
    )
    gate = AssistantGate(config_service=config)  # type: ignore[arg-type]
    assert await gate.is_allowed("+573001112233") is False
    assert await gate.is_allowed("+573009998887") is True
    decision = await gate.evaluate("+573001112233")
    assert decision.reason == "muted_phone"


@pytest.mark.asyncio
async def test_gate_blocks_when_reservation_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_reservations(monkeypatch, [SimpleNamespace(holder_phone="+573001112233")])
    config = SimpleNamespace(get_ai_configuration=AsyncMock(return_value=_ai(enabled=True)))
    gate = AssistantGate(config_service=config)  # type: ignore[arg-type]
    assert await gate.is_allowed("+573001112233") is False
    decision = await gate.evaluate("+573001112233")
    assert decision.allowed is False
    assert decision.reason == "reservation_disabled"


@pytest.mark.asyncio
async def test_gate_allows_global_probe_without_phone(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_reservations(monkeypatch, [SimpleNamespace(holder_phone="+573001112233")])
    config = SimpleNamespace(get_ai_configuration=AsyncMock(return_value=_ai(enabled=True)))
    gate = AssistantGate(config_service=config)  # type: ignore[arg-type]

    decision = await gate.evaluate()

    assert decision.allowed is True
    assert decision.reason == "allowed"


@pytest.mark.asyncio
async def test_gate_marks_invalid_phone_explicitly(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_reservations(monkeypatch, [])
    config = SimpleNamespace(get_ai_configuration=AsyncMock(return_value=_ai(enabled=True)))
    gate = AssistantGate(config_service=config)  # type: ignore[arg-type]

    decision = await gate.evaluate("not-a-phone")

    assert decision.allowed is False
    assert decision.reason == "invalid_phone"
