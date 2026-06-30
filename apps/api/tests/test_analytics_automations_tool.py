import asyncio
from datetime import date
from types import SimpleNamespace
from typing import Any
from uuid import uuid4

import pytest
from beanie import PydanticObjectId

from app.ai.mcp.tools.analytics import (
    admin_get_channel_performance,
    admin_get_equine_workload_report,
    admin_get_occupancy_report,
    admin_get_reservation_funnel,
    admin_get_sales_summary,
)
from app.ai.mcp.tools.automations import (
    schedule_birthday_automation,
    schedule_visit_anniversary_automation,
    send_post_service_message,
)
from app.common.enums import Channel, ReservationStatus
from app.documents import (
    AppConfigDocument,
    AssignmentDocument,
    EquineDocument,
    ExperienceDocument,
    ReservationDocument,
)


class FakeToolLogDoc:
    def __init__(self, **kwargs: Any) -> None:
        for k, v in kwargs.items():
            setattr(self, k, v)

    async def insert(self) -> None:
        self.id = "log-fake"


class _MockField:
    def __eq__(self, other):
        return self

    def __ne__(self, other):
        return self

    def __hash__(self):
        return 0

    def __bool__(self):
        return True


def _patch_beanie_find(
    monkeypatch: pytest.MonkeyPatch,
    doc_cls: type,
    field_names: list[str],
    fake_list_fn: Any,
) -> None:
    for fn in field_names:
        monkeypatch.setattr(doc_cls, fn, _MockField(), raising=False)
    monkeypatch.setattr(doc_cls, "find", lambda *a, **kw: SimpleNamespace(to_list=fake_list_fn))


# ---------------------------------------------------------------------------
# admin_get_sales_summary
# ---------------------------------------------------------------------------


async def _run_returns_summary(monkeypatch: pytest.MonkeyPatch) -> None:
    reservations = [
        SimpleNamespace(
            status=ReservationStatus.CONFIRMED,
            quoted_total_amount=500000,
            channel=Channel.WHATSAPP,
        ),
        SimpleNamespace(
            status=ReservationStatus.CONTACT,
            quoted_total_amount=None,
            channel=Channel.INSTAGRAM,
        ),
    ]

    class FakeReservationDoc:
        @staticmethod
        async def to_list():
            return reservations

    class FakeAggregateQuery:
        def __init__(self, data):
            self._data = data
        async def to_list(self):
            return self._data

    def fake_aggregate(pipeline):
        status_amounts: dict[str, int] = {}
        for r in reservations:
            s = r.status.value if hasattr(r.status, 'value') else str(r.status)
            amt = int(r.quoted_total_amount) if hasattr(r, 'quoted_total_amount') and r.quoted_total_amount else 0
            status_amounts[s] = status_amounts.get(s, 0) + amt
        results = [
            {"_id": s, "count": sum(1 for r in reservations if (r.status.value if hasattr(r.status, 'value') else str(r.status)) == s), "total_amount": status_amounts[s]}
            for s in status_amounts
        ]
        return FakeAggregateQuery(results)

    monkeypatch.setattr(ReservationDocument, "aggregate", fake_aggregate)
    monkeypatch.setattr("app.ai.mcp.tools.analytics.ToolCallLogDocument", FakeToolLogDoc)

    result = await admin_get_sales_summary(trace_id=str(uuid4()))

    assert result["blocking_reasons"] == []
    assert result["total_reservations"] == 2
    assert result["total_revenue"] == 500000
    assert len(result["by_status"]) == 2


def test_returns_summary(monkeypatch: pytest.MonkeyPatch) -> None:
    asyncio.run(_run_returns_summary(monkeypatch))


# ---------------------------------------------------------------------------
# admin_get_reservation_funnel
# ---------------------------------------------------------------------------


async def _run_returns_funnel(monkeypatch: pytest.MonkeyPatch) -> None:
    reservations = [
        SimpleNamespace(status=ReservationStatus.CONTACT),
        SimpleNamespace(status=ReservationStatus.QUOTED),
        SimpleNamespace(status=ReservationStatus.CONFIRMED),
        SimpleNamespace(status=ReservationStatus.COMPLETED),
    ]

    class FakeReservationDoc:
        @staticmethod
        async def to_list():
            return reservations

    class FakeAggregateQuery:
        def __init__(self, data):
            self._data = data
        async def to_list(self):
            return self._data

    def fake_aggregate(pipeline):
        from collections import Counter
        status_counts: Counter = Counter(r.status.value if hasattr(r.status, 'value') else str(r.status) for r in reservations)
        return FakeAggregateQuery([{"_id": s, "count": c} for s, c in status_counts.items()])

    monkeypatch.setattr(ReservationDocument, "aggregate", fake_aggregate)
    monkeypatch.setattr("app.ai.mcp.tools.analytics.ToolCallLogDocument", FakeToolLogDoc)

    result = await admin_get_reservation_funnel(trace_id=str(uuid4()))

    assert result["blocking_reasons"] == []
    assert len(result["stages"]) == 6
    assert result["total_start"] == 4
    assert result["total_converted"] == 2

    stages = {s["stage"]: s["count"] for s in result["stages"]}
    assert stages["contact"] == 1
    assert stages["quoted"] == 1
    assert stages["confirmed"] == 1
    assert stages["completed"] == 1


def test_returns_funnel(monkeypatch: pytest.MonkeyPatch) -> None:
    asyncio.run(_run_returns_funnel(monkeypatch))


# ---------------------------------------------------------------------------
# admin_get_channel_performance
# ---------------------------------------------------------------------------


async def _run_returns_channel_performance(monkeypatch: pytest.MonkeyPatch) -> None:
    reservations = [
        SimpleNamespace(
            status=ReservationStatus.CONFIRMED,
            channel=Channel.WHATSAPP,
        ),
        SimpleNamespace(
            status=ReservationStatus.CONTACT,
            channel=Channel.WHATSAPP,
        ),
        SimpleNamespace(
            status=ReservationStatus.COMPLETED,
            channel=Channel.INSTAGRAM,
        ),
    ]

    class FakeReservationDoc:
        @staticmethod
        async def to_list():
            return reservations

    class FakeAggregateQuery:
        def __init__(self, data):
            self._data = data
        async def to_list(self):
            return self._data

    def fake_aggregate(pipeline):
        from collections import Counter
        channel_counts: Counter = Counter()
        channel_confirmed: Counter = Counter()
        for r in reservations:
            ch = r.channel.value if hasattr(r.channel, 'value') else str(r.channel)
            channel_counts[ch] += 1
            if r.status in (ReservationStatus.CONFIRMED, ReservationStatus.COMPLETED):
                channel_confirmed[ch] += 1
        return FakeAggregateQuery([
            {"_id": ch, "count": channel_counts[ch], "confirmed": channel_confirmed[ch]}
            for ch in channel_counts
        ])

    monkeypatch.setattr(ReservationDocument, "aggregate", fake_aggregate)
    monkeypatch.setattr("app.ai.mcp.tools.analytics.ToolCallLogDocument", FakeToolLogDoc)

    result = await admin_get_channel_performance(trace_id=str(uuid4()))

    assert result["blocking_reasons"] == []
    assert result["total"] == 3
    whatsapp = next(c for c in result["channels"] if c["channel"] == "whatsapp")
    assert whatsapp["count"] == 2
    assert whatsapp["confirmed"] == 1


def test_returns_channel_performance(monkeypatch: pytest.MonkeyPatch) -> None:
    asyncio.run(_run_returns_channel_performance(monkeypatch))


# ---------------------------------------------------------------------------
# admin_get_occupancy_report
# ---------------------------------------------------------------------------


async def _run_returns_occupancy(monkeypatch: pytest.MonkeyPatch) -> None:
    exp_id = PydanticObjectId()
    reservation_date = date(2026, 7, 1)
    reservations = [
        SimpleNamespace(
            id=PydanticObjectId(),
            experience_id=exp_id,
            requested_date=reservation_date,
            participant_count=4,
            status=ReservationStatus.CONFIRMED,
        ),
    ]

    class FakeReservationQuery:
        @staticmethod
        async def to_list():
            return reservations

    monkeypatch.setattr(
        ReservationDocument,
        "find",
        lambda *args, **kw: FakeReservationQuery(),
    )

    async def fake_exp_get(_):
        return SimpleNamespace(name="Media Jornada")

    monkeypatch.setattr(ExperienceDocument, "get", fake_exp_get)
    monkeypatch.setattr("app.ai.mcp.tools.analytics.ToolCallLogDocument", FakeToolLogDoc)

    result = await admin_get_occupancy_report(trace_id=str(uuid4()))

    assert result["blocking_reasons"] == []
    assert result["total_schedules"] == 1
    assert result["avg_occupancy_pct"] == 100.0
    assert result["occupancy"][0]["experience_name"] == "Media Jornada"


def test_returns_occupancy(monkeypatch: pytest.MonkeyPatch) -> None:
    asyncio.run(_run_returns_occupancy(monkeypatch))


# ---------------------------------------------------------------------------
# admin_get_equine_workload_report
# ---------------------------------------------------------------------------


async def _run_returns_workload_report(monkeypatch: pytest.MonkeyPatch) -> None:
    equine_id = PydanticObjectId()
    equines = [
        SimpleNamespace(id=equine_id, name="Pegaso", is_available=True),
    ]

    async def fake_equine_list():
        return equines

    monkeypatch.setattr(
        EquineDocument,
        "find_all",
        lambda: SimpleNamespace(to_list=fake_equine_list),
    )

    async def fake_empty_list():
        return []

    _patch_beanie_find(
        monkeypatch,
        AssignmentDocument,
        ["equine_id", "reservation_id"],
        fake_empty_list,
    )

    monkeypatch.setattr("app.ai.mcp.tools.analytics.ToolCallLogDocument", FakeToolLogDoc)

    result = await admin_get_equine_workload_report(trace_id=str(uuid4()))

    assert result["blocking_reasons"] == []
    assert result["total_equines"] == 1
    assert result["total_assignments"] == 0


def test_returns_workload_report(monkeypatch: pytest.MonkeyPatch) -> None:
    asyncio.run(_run_returns_workload_report(monkeypatch))


# ---------------------------------------------------------------------------
# send_post_service_message
# ---------------------------------------------------------------------------


async def _run_sends_post_service_message(monkeypatch: pytest.MonkeyPatch) -> None:
    res_id = PydanticObjectId()
    reservation = SimpleNamespace(
        id=res_id,
        status=ReservationStatus.COMPLETED,
    )

    async def fake_get(_):
        return reservation

    monkeypatch.setattr(ReservationDocument, "get", fake_get)

    inserted = []

    class FakeServiceLogDoc:
        def __init__(self, **kwargs: Any) -> None:
            for k, v in kwargs.items():
                setattr(self, k, v)

        async def insert(self) -> None:
            self.id = PydanticObjectId()
            inserted.append(self)

    monkeypatch.setattr("app.ai.mcp.tools.automations.ServiceLogDocument", FakeServiceLogDoc)
    monkeypatch.setattr("app.ai.mcp.tools.automations.ToolCallLogDocument", FakeToolLogDoc)

    result = await send_post_service_message(
        reservation_id=str(res_id),
        trace_id=str(uuid4()),
    )

    assert result["sent"] is True
    assert result["blocking_reasons"] == []


def test_sends_post_service_message(monkeypatch: pytest.MonkeyPatch) -> None:
    asyncio.run(_run_sends_post_service_message(monkeypatch))


async def _run_blocks_post_service_when_not_found(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_get(_):
        return None

    monkeypatch.setattr(ReservationDocument, "get", fake_get)
    monkeypatch.setattr("app.ai.mcp.tools.automations.ToolCallLogDocument", FakeToolLogDoc)

    result = await send_post_service_message(
        reservation_id=str(PydanticObjectId()),
        trace_id=str(uuid4()),
    )

    assert result["sent"] is False
    assert len(result["blocking_reasons"]) == 1
    assert result["blocking_reasons"][0]["code"] == "reservation.not_found"


def test_blocks_post_service_when_not_found(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    asyncio.run(_run_blocks_post_service_when_not_found(monkeypatch))


# ---------------------------------------------------------------------------
# schedule_birthday_automation
# ---------------------------------------------------------------------------


async def _run_gets_birthday_automation_state(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_find_one(**kw):
        return SimpleNamespace(
            automation=SimpleNamespace(
                birthday_messages_enabled=True,
                anniversary_messages_enabled=False,
            ),
        )

    monkeypatch.setattr(
        AppConfigDocument,
        "key",
        _MockField(),
        raising=False,
    )
    monkeypatch.setattr(
        AppConfigDocument,
        "created_at",
        _MockField(),
        raising=False,
    )
    monkeypatch.setattr(
        AppConfigDocument,
        "updated_at",
        _MockField(),
        raising=False,
    )
    monkeypatch.setattr(
        AppConfigDocument,
        "reservation_rules",
        _MockField(),
        raising=False,
    )
    monkeypatch.setattr(
        AppConfigDocument,
        "automation",
        _MockField(),
        raising=False,
    )
    monkeypatch.setattr(
        AppConfigDocument,
        "find_one",
        lambda *a, **kw: fake_find_one(),
    )
    monkeypatch.setattr(
        "app.ai.mcp.tools.automations.ToolCallLogDocument",
        FakeToolLogDoc,
    )

    result = await schedule_birthday_automation(
        enabled=None,
        trace_id=str(uuid4()),
    )

    assert result["enabled"] is True
    assert result["blocking_reasons"] == []


def test_gets_birthday_automation_state(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    asyncio.run(_run_gets_birthday_automation_state(monkeypatch))


# ---------------------------------------------------------------------------
# schedule_visit_anniversary_automation
# ---------------------------------------------------------------------------


async def _run_gets_anniversary_automation_state(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_find_one(**kw):
        return SimpleNamespace(
            automation=SimpleNamespace(
                birthday_messages_enabled=False,
                anniversary_messages_enabled=True,
            ),
        )

    monkeypatch.setattr(
        AppConfigDocument,
        "key",
        _MockField(),
        raising=False,
    )
    monkeypatch.setattr(
        AppConfigDocument,
        "created_at",
        _MockField(),
        raising=False,
    )
    monkeypatch.setattr(
        AppConfigDocument,
        "updated_at",
        _MockField(),
        raising=False,
    )
    monkeypatch.setattr(
        AppConfigDocument,
        "reservation_rules",
        _MockField(),
        raising=False,
    )
    monkeypatch.setattr(
        AppConfigDocument,
        "automation",
        _MockField(),
        raising=False,
    )
    monkeypatch.setattr(
        AppConfigDocument,
        "find_one",
        lambda *a, **kw: fake_find_one(),
    )
    monkeypatch.setattr("app.ai.mcp.tools.automations.ToolCallLogDocument", FakeToolLogDoc)

    result = await schedule_visit_anniversary_automation(
        enabled=None,
        trace_id=str(uuid4()),
    )

    assert result["enabled"] is True
    assert result["blocking_reasons"] == []


def test_gets_anniversary_automation_state(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    asyncio.run(_run_gets_anniversary_automation_state(monkeypatch))
