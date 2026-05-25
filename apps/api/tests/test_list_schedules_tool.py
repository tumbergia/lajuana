import asyncio
from datetime import date, timedelta
from types import SimpleNamespace
from typing import Any
from uuid import uuid4

import pytest

from app.ai.mcp.tools.schedules import (
    list_available_schedules,
    suggest_alternative_dates,
)
from app.documents.experience_document import ExperienceDocument
from app.services.experience_catalog_resolver import (
    ExperienceCatalogResolver,
    ExperienceResolutionStatus,
)
from app.services.reservation_service import ReservationService


class FakeToolLogDoc:
    def __init__(self, **kwargs: Any) -> None:
        for k, v in kwargs.items():
            setattr(self, k, v)

    async def insert(self) -> None:
        self.id = "log-fake"


async def _run_returns_schedules_when_experience_found(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    exp_id = "507f1f77bcf86cd799439011"

    async def fake_resolve(self, query):
        return SimpleNamespace(
            status=ExperienceResolutionStatus.FOUND,
            experience_id=exp_id,
            experience_name="Test Experience",
        )

    monkeypatch.setattr(ExperienceCatalogResolver, "resolve", fake_resolve)

    async def fake_get(_):
        return SimpleNamespace(
            id=exp_id,
            name="Test Experience",
        )

    monkeypatch.setattr(ExperienceDocument, "get", fake_get)

    async def fake_has_active(self, requested_date):
        return False

    monkeypatch.setattr(ReservationService, "has_active_reservation_for_date", fake_has_active)
    monkeypatch.setattr("app.ai.mcp.tools.schedules.ToolCallLogDocument", FakeToolLogDoc)

    requested_date = date(2026, 10, 15)
    result = await list_available_schedules(
        experience_query="test experience",
        requested_date=requested_date,
        participant_count=2,
        limit=100,
    )

    assert result["blocking_reasons"] == []
    assert len(result["schedules"]) > 0
    item = result["schedules"][0]
    assert item["schedule_id"] == ""
    assert item["scheduled_date"] == requested_date.isoformat()
    assert item["start_time"] is None
    assert item["capacity_total"] == 8
    assert item["capacity_available"] == 8
    assert item["status"] == "open"
    assert item["experience_id"] == exp_id


def test_returns_schedules_when_experience_found(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    asyncio.run(_run_returns_schedules_when_experience_found(monkeypatch))


async def _run_returns_empty_when_experience_not_found(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_resolve(self, query):
        return SimpleNamespace(
            status=ExperienceResolutionStatus.NOT_FOUND,
        )

    monkeypatch.setattr(ExperienceCatalogResolver, "resolve", fake_resolve)
    monkeypatch.setattr("app.ai.mcp.tools.schedules.ToolCallLogDocument", FakeToolLogDoc)

    result = await list_available_schedules(
        experience_query="nonexistent",
    )

    assert result["schedules"] == []
    assert len(result["blocking_reasons"]) == 1
    assert result["blocking_reasons"][0]["code"] == "experience.not_found"


def test_returns_empty_when_experience_not_found(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    asyncio.run(_run_returns_empty_when_experience_not_found(monkeypatch))


async def _run_returns_empty_when_all_dates_blocked(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    exp_id = "507f1f77bcf86cd799439011"

    async def fake_resolve(self, query):
        return SimpleNamespace(
            status=ExperienceResolutionStatus.FOUND,
            experience_id=exp_id,
            experience_name="Test Experience",
        )

    monkeypatch.setattr(ExperienceCatalogResolver, "resolve", fake_resolve)

    async def fake_get(_):
        return SimpleNamespace(
            id=exp_id,
            name="Test Experience",
        )

    monkeypatch.setattr(ExperienceDocument, "get", fake_get)

    async def fake_has_active(self, requested_date):
        return True

    monkeypatch.setattr(ReservationService, "has_active_reservation_for_date", fake_has_active)
    monkeypatch.setattr("app.ai.mcp.tools.schedules.ToolCallLogDocument", FakeToolLogDoc)

    result = await list_available_schedules(
        experience_query="test experience",
        requested_date=date(2026, 10, 15),
        limit=100,
    )

    assert result["schedules"] == []
    assert result["total"] == 0
    assert result["blocking_reasons"] == []


def test_returns_empty_when_all_dates_blocked(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    asyncio.run(_run_returns_empty_when_all_dates_blocked(monkeypatch))


async def _run_resolves_by_experience_id(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    exp_id = "507f1f77bcf86cd799439011"
    resolve_calls: list[str] = []

    async def fake_resolve(self, query):
        resolve_calls.append(query)
        return SimpleNamespace(
            status=ExperienceResolutionStatus.FOUND,
            experience_id=query,
            experience_name="Test Experience",
        )

    monkeypatch.setattr(ExperienceCatalogResolver, "resolve", fake_resolve)

    async def fake_get(_):
        return SimpleNamespace(
            id=exp_id,
            name="Test Experience",
        )

    monkeypatch.setattr(ExperienceDocument, "get", fake_get)

    async def fake_has_active(self, requested_date):
        return False

    monkeypatch.setattr(ReservationService, "has_active_reservation_for_date", fake_has_active)
    monkeypatch.setattr("app.ai.mcp.tools.schedules.ToolCallLogDocument", FakeToolLogDoc)

    result = await list_available_schedules(
        experience_id=exp_id,
        requested_date=date(2026, 7, 1),
        limit=1,
    )

    assert resolve_calls == [exp_id]
    assert result["blocking_reasons"] == []
    assert len(result["schedules"]) == 1


def test_resolves_by_experience_id(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    asyncio.run(_run_resolves_by_experience_id(monkeypatch))


async def _run_accepts_trace_id_and_conversation_turn_id(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    exp_id = "507f1f77bcf86cd799439011"

    async def fake_resolve(self, query):
        return SimpleNamespace(
            status=ExperienceResolutionStatus.FOUND,
            experience_id=exp_id,
            experience_name="Test Experience",
        )

    monkeypatch.setattr(ExperienceCatalogResolver, "resolve", fake_resolve)

    async def fake_get(_):
        return SimpleNamespace(
            id=exp_id,
            name="Test Experience",
        )

    monkeypatch.setattr(ExperienceDocument, "get", fake_get)

    async def fake_has_active(self, requested_date):
        return False

    monkeypatch.setattr(ReservationService, "has_active_reservation_for_date", fake_has_active)
    monkeypatch.setattr("app.ai.mcp.tools.schedules.ToolCallLogDocument", FakeToolLogDoc)

    trace_id = str(uuid4())
    conversation_turn_id = str(uuid4())

    result = await list_available_schedules(
        experience_query="test experience",
        requested_date=date(2026, 9, 1),
        trace_id=trace_id,
        conversation_turn_id=conversation_turn_id,
    )

    assert result["trace_id"] == trace_id
    assert result["blocking_reasons"] == []


def test_accepts_trace_id_and_conversation_turn_id(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    asyncio.run(_run_accepts_trace_id_and_conversation_turn_id(monkeypatch))


async def _run_date_range_derivation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    exp_id = "507f1f77bcf86cd799439011"

    async def fake_resolve(self, query):
        return SimpleNamespace(
            status=ExperienceResolutionStatus.FOUND,
            experience_id=exp_id,
            experience_name="Test Experience",
        )

    monkeypatch.setattr(ExperienceCatalogResolver, "resolve", fake_resolve)

    async def fake_get(_):
        return SimpleNamespace(
            id=exp_id,
            name="Test Experience",
        )

    monkeypatch.setattr(ExperienceDocument, "get", fake_get)

    async def fake_has_active(self, requested_date):
        return False

    monkeypatch.setattr(ReservationService, "has_active_reservation_for_date", fake_has_active)
    monkeypatch.setattr("app.ai.mcp.tools.schedules.ToolCallLogDocument", FakeToolLogDoc)

    requested = date(2026, 10, 15)
    result = await list_available_schedules(
        experience_query="test experience",
        requested_date=requested,
    )

    assert result["date_from"] == requested.isoformat()
    assert result["date_to"] == (requested + timedelta(days=60)).isoformat()
    assert result["blocking_reasons"] == []


def test_date_range_derivation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    asyncio.run(_run_date_range_derivation(monkeypatch))


# ---------------------------------------------------------------------------
# suggest_alternative_dates tests
# ---------------------------------------------------------------------------


async def _run_returns_alternatives_when_schedules_found(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    exp_id = "507f1f77bcf86cd799439011"

    async def fake_resolve(self, query):
        return SimpleNamespace(
            status=ExperienceResolutionStatus.FOUND,
            experience_id=exp_id,
            experience_name="Test Experience",
        )

    monkeypatch.setattr(ExperienceCatalogResolver, "resolve", fake_resolve)

    async def fake_get(_):
        return SimpleNamespace(
            id=exp_id,
            name="Test Experience",
        )

    monkeypatch.setattr(ExperienceDocument, "get", fake_get)

    async def fake_has_active(self, requested_date):
        return False

    monkeypatch.setattr(ReservationService, "has_active_reservation_for_date", fake_has_active)
    monkeypatch.setattr("app.ai.mcp.tools.schedules.ToolCallLogDocument", FakeToolLogDoc)

    requested_date = date(2026, 7, 15)
    result = await suggest_alternative_dates(
        experience_query="test experience",
        requested_date=requested_date,
        limit=100,
    )

    assert result["blocking_reasons"] == []
    assert len(result["alternatives"]) > 0
    assert result["total"] > 0
    item = result["alternatives"][0]
    assert item["schedule_id"] == ""
    assert item["capacity_total"] == 8
    assert item["capacity_available"] == 8
    assert item["status"] == "open"


def test_returns_alternatives_when_schedules_found(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    asyncio.run(_run_returns_alternatives_when_schedules_found(monkeypatch))


async def _run_no_alternatives_available(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    exp_id = "507f1f77bcf86cd799439011"

    async def fake_resolve(self, query):
        return SimpleNamespace(
            status=ExperienceResolutionStatus.FOUND,
            experience_id=exp_id,
            experience_name="Test Experience",
        )

    monkeypatch.setattr(ExperienceCatalogResolver, "resolve", fake_resolve)

    async def fake_get(_):
        return SimpleNamespace(
            id=exp_id,
            name="Test Experience",
        )

    monkeypatch.setattr(ExperienceDocument, "get", fake_get)

    async def fake_has_active(self, requested_date):
        return True

    monkeypatch.setattr(ReservationService, "has_active_reservation_for_date", fake_has_active)
    monkeypatch.setattr("app.ai.mcp.tools.schedules.ToolCallLogDocument", FakeToolLogDoc)

    result = await suggest_alternative_dates(
        experience_query="test experience",
        requested_date=date(2026, 7, 15),
        limit=100,
    )

    assert result["alternatives"] == []
    assert result["total"] == 0
    assert result["blocking_reasons"] == []


def test_no_alternatives_available(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    asyncio.run(_run_no_alternatives_available(monkeypatch))


async def _run_alternative_dates_experience_not_found(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_resolve(self, query):
        return SimpleNamespace(
            status=ExperienceResolutionStatus.NOT_FOUND,
        )

    monkeypatch.setattr(ExperienceCatalogResolver, "resolve", fake_resolve)
    monkeypatch.setattr("app.ai.mcp.tools.schedules.ToolCallLogDocument", FakeToolLogDoc)

    result = await suggest_alternative_dates(
        experience_query="nonexistent",
        requested_date=date(2026, 7, 15),
    )

    assert result["alternatives"] == []
    assert len(result["blocking_reasons"]) == 1
    assert result["blocking_reasons"][0]["code"] == "experience.not_found"


def test_alternative_dates_experience_not_found(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    asyncio.run(_run_alternative_dates_experience_not_found(monkeypatch))


async def _run_alternative_dates_excludes_dates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    exp_id = "507f1f77bcf86cd799439011"

    async def fake_resolve(self, query):
        return SimpleNamespace(
            status=ExperienceResolutionStatus.FOUND,
            experience_id=exp_id,
            experience_name="Test Experience",
        )

    monkeypatch.setattr(ExperienceCatalogResolver, "resolve", fake_resolve)

    async def fake_get(_):
        return SimpleNamespace(
            id=exp_id,
            name="Test Experience",
        )

    monkeypatch.setattr(ExperienceDocument, "get", fake_get)

    async def fake_has_active(self, requested_date):
        return False

    monkeypatch.setattr(ReservationService, "has_active_reservation_for_date", fake_has_active)
    monkeypatch.setattr("app.ai.mcp.tools.schedules.ToolCallLogDocument", FakeToolLogDoc)

    excluded = date(2026, 7, 5)
    result = await suggest_alternative_dates(
        experience_query="test experience",
        requested_date=date(2026, 7, 15),
        search_days_before=10,
        search_days_after=10,
        exclude_dates=[excluded],
        limit=100,
    )

    assert result["blocking_reasons"] == []
    returned_dates = [alt["scheduled_date"] for alt in result["alternatives"]]
    assert excluded.isoformat() not in returned_dates
    assert result["total"] == len(result["alternatives"])


def test_alternative_dates_excludes_dates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    asyncio.run(_run_alternative_dates_excludes_dates(monkeypatch))


async def _run_alternative_dates_default_requested_date(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    exp_id = "507f1f77bcf86cd799439011"

    async def fake_resolve(self, query):
        return SimpleNamespace(
            status=ExperienceResolutionStatus.FOUND,
            experience_id=exp_id,
            experience_name="Test Experience",
        )

    monkeypatch.setattr(ExperienceCatalogResolver, "resolve", fake_resolve)

    async def fake_get(_):
        return SimpleNamespace(
            id=exp_id,
            name="Test Experience",
        )

    monkeypatch.setattr(ExperienceDocument, "get", fake_get)

    async def fake_has_active(self, requested_date):
        return True

    monkeypatch.setattr(ReservationService, "has_active_reservation_for_date", fake_has_active)
    monkeypatch.setattr("app.ai.mcp.tools.schedules.ToolCallLogDocument", FakeToolLogDoc)

    result = await suggest_alternative_dates(
        experience_query="test experience",
    )

    assert "requested_date" in result
    assert isinstance(result["requested_date"], str)
    assert result["blocking_reasons"] == []
    assert result["alternatives"] == []


def test_alternative_dates_default_requested_date(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    asyncio.run(_run_alternative_dates_default_requested_date(monkeypatch))


async def _run_alternative_dates_accepts_trace_id(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    exp_id = "507f1f77bcf86cd799439011"

    async def fake_resolve(self, query):
        return SimpleNamespace(
            status=ExperienceResolutionStatus.FOUND,
            experience_id=exp_id,
            experience_name="Test Experience",
        )

    monkeypatch.setattr(ExperienceCatalogResolver, "resolve", fake_resolve)

    async def fake_get(_):
        return SimpleNamespace(
            id=exp_id,
            name="Test Experience",
        )

    monkeypatch.setattr(ExperienceDocument, "get", fake_get)

    async def fake_has_active(self, requested_date):
        return False

    monkeypatch.setattr(ReservationService, "has_active_reservation_for_date", fake_has_active)
    monkeypatch.setattr("app.ai.mcp.tools.schedules.ToolCallLogDocument", FakeToolLogDoc)

    trace_id = str(uuid4())
    conversation_turn_id = str(uuid4())

    result = await suggest_alternative_dates(
        experience_query="test experience",
        requested_date=date(2026, 7, 15),
        trace_id=trace_id,
        conversation_turn_id=conversation_turn_id,
    )

    assert result["trace_id"] == trace_id
    assert result["blocking_reasons"] == []
    assert len(result["alternatives"]) > 0


def test_alternative_dates_accepts_trace_id(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    asyncio.run(_run_alternative_dates_accepts_trace_id(monkeypatch))


async def _run_alternative_dates_search_window_bounds(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    exp_id = "507f1f77bcf86cd799439011"

    async def fake_resolve(self, query):
        return SimpleNamespace(
            status=ExperienceResolutionStatus.FOUND,
            experience_id=exp_id,
            experience_name="Test Experience",
        )

    monkeypatch.setattr(ExperienceCatalogResolver, "resolve", fake_resolve)

    async def fake_get(_):
        return SimpleNamespace(
            id=exp_id,
            name="Test Experience",
        )

    monkeypatch.setattr(ExperienceDocument, "get", fake_get)

    async def fake_has_active(self, requested_date):
        return False

    monkeypatch.setattr(ReservationService, "has_active_reservation_for_date", fake_has_active)

    capture = {}

    class CapturingToolLogDoc(FakeToolLogDoc):
        async def insert(self):
            capture["log_input"] = self.input
            return await super().insert()

    monkeypatch.setattr("app.ai.mcp.tools.schedules.ToolCallLogDocument", CapturingToolLogDoc)

    requested = date(2026, 10, 15)
    search_before = 15
    search_after = 30
    result = await suggest_alternative_dates(
        experience_query="test experience",
        requested_date=requested,
        search_days_before=search_before,
        search_days_after=search_after,
    )

    assert result["requested_date"] == requested.isoformat()
    assert result["blocking_reasons"] == []

    payload = capture["log_input"]
    assert isinstance(payload["date_from"], date)
    assert payload["date_to"] == requested + timedelta(days=search_after)
    assert payload["date_from"] == requested - timedelta(days=search_before)


def test_alternative_dates_search_window_bounds(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    asyncio.run(_run_alternative_dates_search_window_bounds(monkeypatch))


async def _run_alternative_dates_limit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    exp_id = "507f1f77bcf86cd799439011"

    async def fake_resolve(self, query):
        return SimpleNamespace(
            status=ExperienceResolutionStatus.FOUND,
            experience_id=exp_id,
            experience_name="Test Experience",
        )

    monkeypatch.setattr(ExperienceCatalogResolver, "resolve", fake_resolve)

    async def fake_get(_):
        return SimpleNamespace(
            id=exp_id,
            name="Test Experience",
        )

    monkeypatch.setattr(ExperienceDocument, "get", fake_get)

    async def fake_has_active(self, requested_date):
        return False

    monkeypatch.setattr(ReservationService, "has_active_reservation_for_date", fake_has_active)
    monkeypatch.setattr("app.ai.mcp.tools.schedules.ToolCallLogDocument", FakeToolLogDoc)

    result = await suggest_alternative_dates(
        experience_query="test experience",
        requested_date=date(2026, 7, 15),
        limit=3,
        search_days_before=30,
        search_days_after=30,
    )

    assert result["blocking_reasons"] == []
    assert len(result["alternatives"]) == 3
    assert result["total"] == 3


def test_alternative_dates_limit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    asyncio.run(_run_alternative_dates_limit(monkeypatch))


async def _run_alternative_dates_excludes_dates_from_json(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Regression test: exclude_dates arriving as list[str] (from orchestrator kwargs via JSON)."""
    exp_id = "507f1f77bcf86cd799439011"

    async def fake_resolve(self, query):
        return SimpleNamespace(
            status=ExperienceResolutionStatus.FOUND,
            experience_id=exp_id,
            experience_name="Test Experience",
        )

    monkeypatch.setattr(ExperienceCatalogResolver, "resolve", fake_resolve)

    async def fake_get(_):
        return SimpleNamespace(
            id=exp_id,
            name="Test Experience",
        )

    monkeypatch.setattr(ExperienceDocument, "get", fake_get)

    async def fake_has_active(self, requested_date):
        return False

    monkeypatch.setattr(ReservationService, "has_active_reservation_for_date", fake_has_active)
    monkeypatch.setattr("app.ai.mcp.tools.schedules.ToolCallLogDocument", FakeToolLogDoc)

    excluded_str = "2026-07-05"
    result = await suggest_alternative_dates(
        experience_query="test experience",
        requested_date=date(2026, 7, 15),
        search_days_before=10,
        search_days_after=10,
        exclude_dates=[excluded_str],
        limit=100,
    )

    assert result["blocking_reasons"] == []
    returned_dates = [alt["scheduled_date"] for alt in result["alternatives"]]
    assert excluded_str not in returned_dates


def test_alternative_dates_excludes_dates_from_json(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    asyncio.run(_run_alternative_dates_excludes_dates_from_json(monkeypatch))
