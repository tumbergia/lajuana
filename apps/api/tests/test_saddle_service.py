from __future__ import annotations

import asyncio
from types import SimpleNamespace

import pytest

from app.services.saddle_service import SaddleService


def _fake_saddle(**overrides: object) -> SimpleNamespace:
    base = {
        "id": "660000000000000000000202",
        "code": "ASG-22",
        "name": "Principal",
        "is_available": True,
    }
    base.update(overrides)
    return SimpleNamespace(**base)


def test_resolve_saddle_reference_unique_code_match(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_list = [
        _fake_saddle(id="660000000000000000000202", code="ASG-22"),
        _fake_saddle(id="660000000000000000000203", code="ASG-23"),
    ]

    async def fake_list_fn(self: SaddleService, **kwargs: object) -> list[SimpleNamespace]:
        return fake_list

    monkeypatch.setattr(SaddleService, "list", fake_list_fn)
    service = SaddleService()

    async def run() -> None:
        result = await service.resolve_saddle_reference("asg-22")
        assert result["status"] == "resolved"
        assert result["saddle_id"] == "660000000000000000000202"

    asyncio.run(run())


def test_resolve_saddle_reference_ambiguous_name_match(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_list = [
        _fake_saddle(id="660000000000000000000202", code="ASG-22", name="Patio"),
        _fake_saddle(id="660000000000000000000203", code="ASG-23", name="Patio"),
    ]

    async def fake_list_fn(self: SaddleService, **kwargs: object) -> list[SimpleNamespace]:
        return fake_list

    monkeypatch.setattr(SaddleService, "list", fake_list_fn)
    service = SaddleService()

    async def run() -> None:
        result = await service.resolve_saddle_reference("patio")
        assert result["status"] == "ambiguous"
        assert len(result["matches"]) == 2

    asyncio.run(run())
