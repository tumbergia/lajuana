import asyncio
from datetime import date, time, timedelta
from types import SimpleNamespace
from typing import Any
from uuid import uuid4

import pytest
from beanie import PydanticObjectId

from app.ai.mcp.tools.schedules import (
    list_available_schedules,
    suggest_alternative_dates,
)
from app.common.enums import ScheduleStatus
from app.documents.experience_document import ExperienceDocument
from app.documents.schedule_document import ScheduleDocument
from app.services.experience_catalog_resolver import (
    ExperienceCatalogResolver,
    ExperienceResolutionStatus,
)


class _MockField:
    def __eq__(self, other):
        return self

    def __ne__(self, other):
        return self

    def __ge__(self, other):
        return self

    def __le__(self, other):
        return self

    def __gt__(self, other):
        return self

    def __lt__(self, other):
        return self

    def __hash__(self):
        return 0

    def __bool__(self):
        return True


class FakeToolLogDoc:
    def __init__(self, **kwargs: Any) -> None:
        for k, v in kwargs.items():
            setattr(self, k, v)

    async def insert(self) -> None:
        self.id = "log-fake"


def _patch_schedule_fields(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(ScheduleDocument, "experience_id", _MockField(), raising=False)
    monkeypatch.setattr(ScheduleDocument, "date", _MockField(), raising=False)
    monkeypatch.setattr(ScheduleDocument, "is_active", _MockField(), raising=False)
    monkeypatch.setattr(ScheduleDocument, "status", _MockField(), raising=False)


async def _run_returns_schedules_when_experience_found(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    exp_id = PydanticObjectId()

    async def fake_resolve(self, query):
        return SimpleNamespace(
            status=ExperienceResolutionStatus.FOUND,
            experience_id=str(exp_id),
            experience_name="Test Experience",
        )

    monkeypatch.setattr(ExperienceCatalogResolver, "resolve", fake_resolve)

    async def fake_get(_):
        return SimpleNamespace(
            id=exp_id,
            name="Test Experience",
        )

    monkeypatch.setattr(ExperienceDocument, "get", fake_get)

    schedule_date = date(2026, 6, 15)
    schedule_start = time(9, 0)

    fake_schedules = [
        SimpleNamespace(
            id=PydanticObjectId(),
            date=schedule_date,
            start_time=schedule_start,
            capacity_total=20,
            available_slots=10,
            status=ScheduleStatus.OPEN,
        )
    ]

    class FakeSortQuery:
        def __init__(self, items):
            self._items = items

        async def to_list(self):
            return self._items

    class FakeQuery:
        def sort(self, *args):
            return FakeSortQuery(fake_schedules)

    def fake_find_many(*args, **kwargs):
        return FakeQuery()

    _patch_schedule_fields(monkeypatch)
    monkeypatch.setattr(ScheduleDocument, "find_many", fake_find_many)
    monkeypatch.setattr("app.ai.mcp.tools.schedules.ToolCallLogDocument", FakeToolLogDoc)

    result = await list_available_schedules(
        experience_query="test experience",
        participant_count=2,
    )

    assert result["blocking_reasons"] == []
    assert len(result["schedules"]) == 1
    item = result["schedules"][0]
    assert item["schedule_id"] == str(fake_schedules[0].id)
    assert item["scheduled_date"] == schedule_date.isoformat()
    assert item["start_time"] == str(schedule_start)
    assert item["capacity_total"] == 20
    assert item["capacity_available"] == 10
    assert item["status"] == ScheduleStatus.OPEN


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


async def _run_returns_empty_when_no_schedules(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    exp_id = PydanticObjectId()

    async def fake_resolve(self, query):
        return SimpleNamespace(
            status=ExperienceResolutionStatus.FOUND,
            experience_id=str(exp_id),
            experience_name="Test Experience",
        )

    monkeypatch.setattr(ExperienceCatalogResolver, "resolve", fake_resolve)

    async def fake_get(_):
        return SimpleNamespace(
            id=exp_id,
            name="Test Experience",
        )

    monkeypatch.setattr(ExperienceDocument, "get", fake_get)

    class FakeSortQuery:
        def __init__(self, items):
            self._items = items

        async def to_list(self):
            return self._items

    class FakeQuery:
        def sort(self, *args):
            return FakeSortQuery([])

    def fake_find_many(*args, **kwargs):
        return FakeQuery()

    _patch_schedule_fields(monkeypatch)
    monkeypatch.setattr(ScheduleDocument, "find_many", fake_find_many)
    monkeypatch.setattr("app.ai.mcp.tools.schedules.ToolCallLogDocument", FakeToolLogDoc)

    result = await list_available_schedules(
        experience_query="test experience",
    )

    assert result["schedules"] == []
    assert result["total"] == 0
    assert result["blocking_reasons"] == []


def test_returns_empty_when_no_schedules(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    asyncio.run(_run_returns_empty_when_no_schedules(monkeypatch))


async def _run_resolves_by_experience_id(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    exp_id = PydanticObjectId()
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

    class FakeSortQuery:
        def __init__(self, items):
            self._items = items

        async def to_list(self):
            return self._items

    class FakeQuery:
        def sort(self, *args):
            return FakeSortQuery(
                [
                    SimpleNamespace(
                        id=PydanticObjectId(),
                        date=date(2026, 7, 1),
                        start_time=time(10, 0),
                        capacity_total=15,
                        available_slots=8,
                        status=ScheduleStatus.OPEN,
                    )
                ]
            )

    def fake_find_many(*args, **kwargs):
        return FakeQuery()

    _patch_schedule_fields(monkeypatch)
    monkeypatch.setattr(ScheduleDocument, "find_many", fake_find_many)
    monkeypatch.setattr("app.ai.mcp.tools.schedules.ToolCallLogDocument", FakeToolLogDoc)

    result = await list_available_schedules(
        experience_id=str(exp_id),
    )

    assert resolve_calls == [str(exp_id)]
    assert result["blocking_reasons"] == []
    assert len(result["schedules"]) == 1


def test_resolves_by_experience_id(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    asyncio.run(_run_resolves_by_experience_id(monkeypatch))


async def _run_filters_by_participant_count(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    exp_id = PydanticObjectId()

    async def fake_resolve(self, query):
        return SimpleNamespace(
            status=ExperienceResolutionStatus.FOUND,
            experience_id=str(exp_id),
            experience_name="Test Experience",
        )

    monkeypatch.setattr(ExperienceCatalogResolver, "resolve", fake_resolve)

    async def fake_get(_):
        return SimpleNamespace(
            id=exp_id,
            name="Test Experience",
        )

    monkeypatch.setattr(ExperienceDocument, "get", fake_get)

    schedules_list = [
        SimpleNamespace(
            id=PydanticObjectId(),
            date=date(2026, 8, 1),
            start_time=time(9, 0),
            capacity_total=10,
            available_slots=2,
            status=ScheduleStatus.OPEN,
        ),
        SimpleNamespace(
            id=PydanticObjectId(),
            date=date(2026, 8, 5),
            start_time=time(10, 0),
            capacity_total=20,
            available_slots=10,
            status=ScheduleStatus.OPEN,
        ),
    ]

    class FakeSortQuery:
        def __init__(self, items):
            self._items = items

        async def to_list(self):
            return self._items

    class FakeQuery:
        def sort(self, *args):
            return FakeSortQuery(schedules_list)

    def fake_find_many(*args, **kwargs):
        return FakeQuery()

    _patch_schedule_fields(monkeypatch)
    monkeypatch.setattr(ScheduleDocument, "find_many", fake_find_many)
    monkeypatch.setattr("app.ai.mcp.tools.schedules.ToolCallLogDocument", FakeToolLogDoc)

    result = await list_available_schedules(
        experience_query="test experience",
        participant_count=5,
    )

    assert result["blocking_reasons"] == []
    assert len(result["schedules"]) == 1
    assert result["schedules"][0]["capacity_available"] == 10
    assert result["total"] == 1


def test_filters_by_participant_count(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    asyncio.run(_run_filters_by_participant_count(monkeypatch))


async def _run_accepts_trace_id_and_conversation_turn_id(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    exp_id = PydanticObjectId()

    async def fake_resolve(self, query):
        return SimpleNamespace(
            status=ExperienceResolutionStatus.FOUND,
            experience_id=str(exp_id),
            experience_name="Test Experience",
        )

    monkeypatch.setattr(ExperienceCatalogResolver, "resolve", fake_resolve)

    async def fake_get(_):
        return SimpleNamespace(
            id=exp_id,
            name="Test Experience",
        )

    monkeypatch.setattr(ExperienceDocument, "get", fake_get)

    class FakeSortQuery:
        def __init__(self, items):
            self._items = items

        async def to_list(self):
            return self._items

    class FakeQuery:
        def sort(self, *args):
            return FakeSortQuery(
                [
                    SimpleNamespace(
                        id=PydanticObjectId(),
                        date=date(2026, 9, 1),
                        start_time=time(11, 0),
                        capacity_total=20,
                        available_slots=15,
                        status=ScheduleStatus.OPEN,
                    )
                ]
            )

    def fake_find_many(*args, **kwargs):
        return FakeQuery()

    _patch_schedule_fields(monkeypatch)
    monkeypatch.setattr(ScheduleDocument, "find_many", fake_find_many)
    monkeypatch.setattr("app.ai.mcp.tools.schedules.ToolCallLogDocument", FakeToolLogDoc)

    trace_id = str(uuid4())
    conversation_turn_id = str(uuid4())

    result = await list_available_schedules(
        experience_query="test experience",
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
    exp_id = PydanticObjectId()

    async def fake_resolve(self, query):
        return SimpleNamespace(
            status=ExperienceResolutionStatus.FOUND,
            experience_id=str(exp_id),
            experience_name="Test Experience",
        )

    monkeypatch.setattr(ExperienceCatalogResolver, "resolve", fake_resolve)

    async def fake_get(_):
        return SimpleNamespace(
            id=exp_id,
            name="Test Experience",
        )

    monkeypatch.setattr(ExperienceDocument, "get", fake_get)

    class FakeSortQuery:
        def __init__(self, items):
            self._items = items

        async def to_list(self):
            return self._items

    class FakeQuery:
        def sort(self, *args):
            return FakeSortQuery([])

    def fake_find_many(*args, **kwargs):
        return FakeQuery()

    _patch_schedule_fields(monkeypatch)
    monkeypatch.setattr(ScheduleDocument, "find_many", fake_find_many)
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
    exp_id = PydanticObjectId()

    async def fake_resolve(self, query):
        return SimpleNamespace(
            status=ExperienceResolutionStatus.FOUND,
            experience_id=str(exp_id),
            experience_name="Test Experience",
        )

    monkeypatch.setattr(ExperienceCatalogResolver, "resolve", fake_resolve)

    async def fake_get(_):
        return SimpleNamespace(
            id=exp_id,
            name="Test Experience",
        )

    monkeypatch.setattr(ExperienceDocument, "get", fake_get)

    requested_date = date(2026, 7, 15)
    alt_date = date(2026, 8, 14)

    fake_schedules = [
        SimpleNamespace(
            id=PydanticObjectId(),
            date=alt_date,
            start_time=time(9, 0),
            capacity_total=20,
            available_slots=10,
            status=ScheduleStatus.OPEN,
        )
    ]

    class FakeSortQuery:
        def __init__(self, items):
            self._items = items

        async def to_list(self):
            return self._items

    class FakeQuery:
        def sort(self, *args):
            return FakeSortQuery(fake_schedules)

    def fake_find_many(*args, **kwargs):
        return FakeQuery()

    _patch_schedule_fields(monkeypatch)
    monkeypatch.setattr(ScheduleDocument, "find_many", fake_find_many)
    monkeypatch.setattr("app.ai.mcp.tools.schedules.ToolCallLogDocument", FakeToolLogDoc)

    result = await suggest_alternative_dates(
        experience_query="test experience",
        requested_date=requested_date,
        search_days_after=30,
    )

    assert result["blocking_reasons"] == []
    assert len(result["alternatives"]) == 1
    assert result["total"] == 1
    assert result["alternatives"][0]["scheduled_date"] == alt_date.isoformat()


def test_returns_alternatives_when_schedules_found(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    asyncio.run(_run_returns_alternatives_when_schedules_found(monkeypatch))


async def _run_no_alternatives_available(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    exp_id = PydanticObjectId()

    async def fake_resolve(self, query):
        return SimpleNamespace(
            status=ExperienceResolutionStatus.FOUND,
            experience_id=str(exp_id),
            experience_name="Test Experience",
        )

    monkeypatch.setattr(ExperienceCatalogResolver, "resolve", fake_resolve)

    async def fake_get(_):
        return SimpleNamespace(
            id=exp_id,
            name="Test Experience",
        )

    monkeypatch.setattr(ExperienceDocument, "get", fake_get)

    class FakeSortQuery:
        def __init__(self, items):
            self._items = items

        async def to_list(self):
            return self._items

    class FakeQuery:
        def sort(self, *args):
            return FakeSortQuery([])

    def fake_find_many(*args, **kwargs):
        return FakeQuery()

    _patch_schedule_fields(monkeypatch)
    monkeypatch.setattr(ScheduleDocument, "find_many", fake_find_many)
    monkeypatch.setattr("app.ai.mcp.tools.schedules.ToolCallLogDocument", FakeToolLogDoc)

    result = await suggest_alternative_dates(
        experience_query="test experience",
        requested_date=date(2026, 7, 15),
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


async def _run_alternative_dates_filters_by_participant_count(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    exp_id = PydanticObjectId()

    async def fake_resolve(self, query):
        return SimpleNamespace(
            status=ExperienceResolutionStatus.FOUND,
            experience_id=str(exp_id),
            experience_name="Test Experience",
        )

    monkeypatch.setattr(ExperienceCatalogResolver, "resolve", fake_resolve)

    async def fake_get(_):
        return SimpleNamespace(
            id=exp_id,
            name="Test Experience",
        )

    monkeypatch.setattr(ExperienceDocument, "get", fake_get)

    schedules_list = [
        SimpleNamespace(
            id=PydanticObjectId(),
            date=date(2026, 8, 1),
            start_time=time(9, 0),
            capacity_total=10,
            available_slots=2,
            status=ScheduleStatus.OPEN,
        ),
        SimpleNamespace(
            id=PydanticObjectId(),
            date=date(2026, 8, 5),
            start_time=time(10, 0),
            capacity_total=20,
            available_slots=10,
            status=ScheduleStatus.OPEN,
        ),
    ]

    class FakeSortQuery:
        def __init__(self, items):
            self._items = items

        async def to_list(self):
            return self._items

    class FakeQuery:
        def sort(self, *args):
            return FakeSortQuery(schedules_list)

    def fake_find_many(*args, **kwargs):
        return FakeQuery()

    _patch_schedule_fields(monkeypatch)
    monkeypatch.setattr(ScheduleDocument, "find_many", fake_find_many)
    monkeypatch.setattr("app.ai.mcp.tools.schedules.ToolCallLogDocument", FakeToolLogDoc)

    result = await suggest_alternative_dates(
        experience_query="test experience",
        requested_date=date(2026, 7, 15),
        participant_count=5,
    )

    assert result["blocking_reasons"] == []
    assert len(result["alternatives"]) == 1
    assert result["alternatives"][0]["capacity_available"] == 10
    assert result["total"] == 1


def test_alternative_dates_filters_by_participant_count(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    asyncio.run(_run_alternative_dates_filters_by_participant_count(monkeypatch))


async def _run_alternative_dates_excludes_dates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    exp_id = PydanticObjectId()

    async def fake_resolve(self, query):
        return SimpleNamespace(
            status=ExperienceResolutionStatus.FOUND,
            experience_id=str(exp_id),
            experience_name="Test Experience",
        )

    monkeypatch.setattr(ExperienceCatalogResolver, "resolve", fake_resolve)

    async def fake_get(_):
        return SimpleNamespace(
            id=exp_id,
            name="Test Experience",
        )

    monkeypatch.setattr(ExperienceDocument, "get", fake_get)

    excluded = date(2026, 8, 1)
    included = date(2026, 8, 5)

    schedules_list = [
        SimpleNamespace(
            id=PydanticObjectId(),
            date=excluded,
            start_time=time(9, 0),
            capacity_total=10,
            available_slots=5,
            status=ScheduleStatus.OPEN,
        ),
        SimpleNamespace(
            id=PydanticObjectId(),
            date=included,
            start_time=time(10, 0),
            capacity_total=20,
            available_slots=10,
            status=ScheduleStatus.OPEN,
        ),
    ]

    class FakeSortQuery:
        def __init__(self, items):
            self._items = items

        async def to_list(self):
            return self._items

    class FakeQuery:
        def sort(self, *args):
            return FakeSortQuery(schedules_list)

    def fake_find_many(*args, **kwargs):
        return FakeQuery()

    _patch_schedule_fields(monkeypatch)
    monkeypatch.setattr(ScheduleDocument, "find_many", fake_find_many)
    monkeypatch.setattr("app.ai.mcp.tools.schedules.ToolCallLogDocument", FakeToolLogDoc)

    result = await suggest_alternative_dates(
        experience_query="test experience",
        requested_date=date(2026, 7, 15),
        exclude_dates=[excluded],
    )

    assert result["blocking_reasons"] == []
    assert len(result["alternatives"]) == 1
    assert result["alternatives"][0]["scheduled_date"] == included.isoformat()
    assert result["total"] == 1


def test_alternative_dates_excludes_dates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    asyncio.run(_run_alternative_dates_excludes_dates(monkeypatch))


async def _run_alternative_dates_default_requested_date(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    exp_id = PydanticObjectId()

    async def fake_resolve(self, query):
        return SimpleNamespace(
            status=ExperienceResolutionStatus.FOUND,
            experience_id=str(exp_id),
            experience_name="Test Experience",
        )

    monkeypatch.setattr(ExperienceCatalogResolver, "resolve", fake_resolve)

    async def fake_get(_):
        return SimpleNamespace(
            id=exp_id,
            name="Test Experience",
        )

    monkeypatch.setattr(ExperienceDocument, "get", fake_get)

    class FakeSortQuery:
        def __init__(self, items):
            self._items = items

        async def to_list(self):
            return self._items

    class FakeQuery:
        def sort(self, *args):
            return FakeSortQuery([])

    def fake_find_many(*args, **kwargs):
        return FakeQuery()

    _patch_schedule_fields(monkeypatch)
    monkeypatch.setattr(ScheduleDocument, "find_many", fake_find_many)
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
    exp_id = PydanticObjectId()

    async def fake_resolve(self, query):
        return SimpleNamespace(
            status=ExperienceResolutionStatus.FOUND,
            experience_id=str(exp_id),
            experience_name="Test Experience",
        )

    monkeypatch.setattr(ExperienceCatalogResolver, "resolve", fake_resolve)

    async def fake_get(_):
        return SimpleNamespace(
            id=exp_id,
            name="Test Experience",
        )

    monkeypatch.setattr(ExperienceDocument, "get", fake_get)

    class FakeSortQuery:
        def __init__(self, items):
            self._items = items

        async def to_list(self):
            return self._items

    class FakeQuery:
        def sort(self, *args):
            return FakeSortQuery(
                [
                    SimpleNamespace(
                        id=PydanticObjectId(),
                        date=date(2026, 9, 1),
                        start_time=time(11, 0),
                        capacity_total=20,
                        available_slots=15,
                        status=ScheduleStatus.OPEN,
                    )
                ]
            )

    def fake_find_many(*args, **kwargs):
        return FakeQuery()

    _patch_schedule_fields(monkeypatch)
    monkeypatch.setattr(ScheduleDocument, "find_many", fake_find_many)
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
    assert len(result["alternatives"]) == 1


def test_alternative_dates_accepts_trace_id(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    asyncio.run(_run_alternative_dates_accepts_trace_id(monkeypatch))


async def _run_alternative_dates_search_window_bounds(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    exp_id = PydanticObjectId()

    async def fake_resolve(self, query):
        return SimpleNamespace(
            status=ExperienceResolutionStatus.FOUND,
            experience_id=str(exp_id),
            experience_name="Test Experience",
        )

    monkeypatch.setattr(ExperienceCatalogResolver, "resolve", fake_resolve)

    async def fake_get(_):
        return SimpleNamespace(
            id=exp_id,
            name="Test Experience",
        )

    monkeypatch.setattr(ExperienceDocument, "get", fake_get)

    class FakeSortQuery:
        def __init__(self, items):
            self._items = items

        async def to_list(self):
            return self._items

    class FakeQuery:
        def sort(self, *args):
            return FakeSortQuery([])

    def fake_find_many(*args, **kwargs):
        return FakeQuery()

    _patch_schedule_fields(monkeypatch)
    monkeypatch.setattr(ScheduleDocument, "find_many", fake_find_many)

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
    exp_id = PydanticObjectId()

    async def fake_resolve(self, query):
        return SimpleNamespace(
            status=ExperienceResolutionStatus.FOUND,
            experience_id=str(exp_id),
            experience_name="Test Experience",
        )

    monkeypatch.setattr(ExperienceCatalogResolver, "resolve", fake_resolve)

    async def fake_get(_):
        return SimpleNamespace(
            id=exp_id,
            name="Test Experience",
        )

    monkeypatch.setattr(ExperienceDocument, "get", fake_get)

    schedules_list = [
        SimpleNamespace(
            id=PydanticObjectId(),
            date=date(2026, 8, d),
            start_time=time(9, 0),
            capacity_total=20,
            available_slots=10,
            status=ScheduleStatus.OPEN,
        )
        for d in range(1, 8)
    ]

    class FakeSortQuery:
        def __init__(self, items):
            self._items = items

        async def to_list(self):
            return self._items

    class FakeQuery:
        def sort(self, *args):
            return FakeSortQuery(schedules_list)

    def fake_find_many(*args, **kwargs):
        return FakeQuery()

    _patch_schedule_fields(monkeypatch)
    monkeypatch.setattr(ScheduleDocument, "find_many", fake_find_many)
    monkeypatch.setattr("app.ai.mcp.tools.schedules.ToolCallLogDocument", FakeToolLogDoc)

    result = await suggest_alternative_dates(
        experience_query="test experience",
        requested_date=date(2026, 7, 15),
        limit=3,
    )

    assert result["blocking_reasons"] == []
    assert len(result["alternatives"]) == 3
    assert result["total"] == 7


def test_alternative_dates_limit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    asyncio.run(_run_alternative_dates_limit(monkeypatch))


async def _run_alternative_dates_excludes_dates_from_json(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Regression test: exclude_dates arriving as list[str] (from orchestrator kwargs via JSON)."""
    exp_id = PydanticObjectId()

    async def fake_resolve(self, query):
        return SimpleNamespace(
            status=ExperienceResolutionStatus.FOUND,
            experience_id=str(exp_id),
            experience_name="Test Experience",
        )

    monkeypatch.setattr(ExperienceCatalogResolver, "resolve", fake_resolve)

    async def fake_get(_):
        return SimpleNamespace(
            id=exp_id,
            name="Test Experience",
        )

    monkeypatch.setattr(ExperienceDocument, "get", fake_get)

    excluded = date(2026, 8, 1)
    included = date(2026, 8, 5)

    schedules_list = [
        SimpleNamespace(
            id=PydanticObjectId(),
            date=excluded,
            start_time=time(9, 0),
            capacity_total=10,
            available_slots=5,
            status=ScheduleStatus.OPEN,
        ),
        SimpleNamespace(
            id=PydanticObjectId(),
            date=included,
            start_time=time(10, 0),
            capacity_total=20,
            available_slots=10,
            status=ScheduleStatus.OPEN,
        ),
    ]

    class FakeSortQuery:
        def __init__(self, items):
            self._items = items

        async def to_list(self):
            return self._items

    class FakeQuery:
        def sort(self, *args):
            return FakeSortQuery(schedules_list)

    def fake_find_many(*args, **kwargs):
        return FakeQuery()

    _patch_schedule_fields(monkeypatch)
    monkeypatch.setattr(ScheduleDocument, "find_many", fake_find_many)
    monkeypatch.setattr("app.ai.mcp.tools.schedules.ToolCallLogDocument", FakeToolLogDoc)

    # Simulate real orchestrator pipeline: exclude_dates arrives as list[str]
    # (planner JSON -> ToolArgs -> model_dump -> kwargs)
    result = await suggest_alternative_dates(
        experience_query="test experience",
        requested_date=date(2026, 7, 15),
        exclude_dates=["2026-08-01"],
    )

    assert result["blocking_reasons"] == []
    assert len(result["alternatives"]) == 1
    assert result["alternatives"][0]["scheduled_date"] == included.isoformat()
    assert result["total"] == 1


def test_alternative_dates_excludes_dates_from_json(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    asyncio.run(_run_alternative_dates_excludes_dates_from_json(monkeypatch))
