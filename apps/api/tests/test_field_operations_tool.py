import asyncio
from datetime import date
from types import SimpleNamespace
from typing import Any
from uuid import uuid4

import pytest
from beanie import PydanticObjectId

from app.ai.mcp.tools.operations import (
    admin_add_equine_health_event,
    admin_close_service_execution,
    admin_get_equine_workload,
    admin_get_logistics_checklist,
    admin_update_equine_availability,
    guide_create_service_log,
    guide_report_incident,
)
from app.common.enums import ReservationStatus
from app.documents import (
    AssignmentDocument,
    EquineDocument,
    ParticipantDocument,
    PolicyDocument,
    ReservationDocument,
    ServiceLogDocument,
    ServiceLogEventType,
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
# admin_get_logistics_checklist
# ---------------------------------------------------------------------------


async def _run_returns_checklist_for_found_reservation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    res_id = PydanticObjectId()
    reservation = SimpleNamespace(
        id=res_id,
        status=ReservationStatus.CONFIRMED,
        participant_count=4,
        holder_name="Juan",
    )

    async def fake_get(_):
        return reservation

    monkeypatch.setattr(ReservationDocument, "get", fake_get)

    async def fake_participant_list():
        return [
            SimpleNamespace(is_completed=True),
            SimpleNamespace(is_completed=True),
        ]

    async def fake_assignments_list():
        return [
            SimpleNamespace(
                id=PydanticObjectId(), saddle_id=PydanticObjectId(), equine_id=PydanticObjectId()
            )
        ]

    async def fake_policies_list():
        return [SimpleNamespace(id=PydanticObjectId())]

    async def fake_logs_list():
        return [SimpleNamespace(event_type=ServiceLogEventType.ARRIVAL)]

    _patch_beanie_find(
        monkeypatch,
        ParticipantDocument,
        ["reservation_id"],
        fake_participant_list,
    )
    _patch_beanie_find(
        monkeypatch,
        AssignmentDocument,
        ["reservation_id", "equine_id"],
        fake_assignments_list,
    )
    _patch_beanie_find(
        monkeypatch,
        PolicyDocument,
        ["reservation_id"],
        fake_policies_list,
    )
    _patch_beanie_find(
        monkeypatch,
        ServiceLogDocument,
        ["reservation_id"],
        fake_logs_list,
    )

    # Mock EquineDocument.get for availability check
    async def fake_equine_get(_eid: str) -> SimpleNamespace:
        return SimpleNamespace(id=PydanticObjectId(), is_available=True, is_active=True)

    monkeypatch.setattr("app.ai.mcp.tools.operations.EquineDocument.get", fake_equine_get)

    monkeypatch.setattr("app.ai.mcp.tools.operations.ToolCallLogDocument", FakeToolLogDoc)

    result = await admin_get_logistics_checklist(
        reservation_id=str(res_id),
        trace_id=str(uuid4()),
    )

    assert result["blocking_reasons"] == []
    assert result["total"] >= 5
    assert result["completed"] >= 1
    assert result["reservation_id"] == str(res_id)


def test_returns_checklist_for_found_reservation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    asyncio.run(_run_returns_checklist_for_found_reservation(monkeypatch))


async def _run_returns_blocking_when_reservation_not_found(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_get(_):
        return None

    monkeypatch.setattr(ReservationDocument, "get", fake_get)
    monkeypatch.setattr("app.ai.mcp.tools.operations.ToolCallLogDocument", FakeToolLogDoc)

    result = await admin_get_logistics_checklist(
        reservation_id=str(PydanticObjectId()),
        trace_id=str(uuid4()),
    )

    assert len(result["blocking_reasons"]) == 1
    assert result["blocking_reasons"][0]["code"] == "reservation.not_found"
    assert result["total"] == 0


def test_returns_blocking_when_reservation_not_found(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    asyncio.run(_run_returns_blocking_when_reservation_not_found(monkeypatch))


# ---------------------------------------------------------------------------
# guide_create_service_log
# ---------------------------------------------------------------------------


async def _run_creates_service_log_successfully(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    res_id = PydanticObjectId()
    reservation = SimpleNamespace(id=res_id, status=ReservationStatus.CONFIRMED)

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

    monkeypatch.setattr("app.ai.mcp.tools.operations.ServiceLogDocument", FakeServiceLogDoc)
    monkeypatch.setattr("app.ai.mcp.tools.operations.ToolCallLogDocument", FakeToolLogDoc)

    result = await guide_create_service_log(
        reservation_id=str(res_id),
        event_type="arrival",
        notes="Llegada puntual",
        trace_id=str(uuid4()),
    )

    assert result["created"] is True
    assert result["log_id"] is not None
    assert result["blocking_reasons"] == []
    assert len(inserted) == 1


def test_creates_service_log_successfully(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    asyncio.run(_run_creates_service_log_successfully(monkeypatch))


async def _run_blocks_when_reservation_not_found(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_get(_):
        return None

    monkeypatch.setattr(ReservationDocument, "get", fake_get)
    monkeypatch.setattr("app.ai.mcp.tools.operations.ToolCallLogDocument", FakeToolLogDoc)

    result = await guide_create_service_log(
        reservation_id=str(PydanticObjectId()),
        event_type="arrival",
        trace_id=str(uuid4()),
    )

    assert result["created"] is False
    assert len(result["blocking_reasons"]) == 1
    assert result["blocking_reasons"][0]["code"] == "reservation.not_found"


def test_blocks_when_reservation_not_found(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    asyncio.run(_run_blocks_when_reservation_not_found(monkeypatch))


async def _run_blocks_invalid_event_type(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    res_id = PydanticObjectId()
    reservation = SimpleNamespace(id=res_id, status=ReservationStatus.CONFIRMED)

    async def fake_get(_):
        return reservation

    monkeypatch.setattr(ReservationDocument, "get", fake_get)
    monkeypatch.setattr("app.ai.mcp.tools.operations.ToolCallLogDocument", FakeToolLogDoc)

    result = await guide_create_service_log(
        reservation_id=str(res_id),
        event_type="invalid_type",
        trace_id=str(uuid4()),
    )

    assert result["created"] is False
    assert len(result["blocking_reasons"]) == 1
    assert result["blocking_reasons"][0]["code"] == "log.invalid_event_type"


def test_blocks_invalid_event_type(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    asyncio.run(_run_blocks_invalid_event_type(monkeypatch))


# ---------------------------------------------------------------------------
# guide_report_incident
# ---------------------------------------------------------------------------


async def _run_reports_incident_successfully(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    res_id = PydanticObjectId()
    reservation = SimpleNamespace(id=res_id, status=ReservationStatus.CONFIRMED)

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

    monkeypatch.setattr("app.ai.mcp.tools.operations.ServiceLogDocument", FakeServiceLogDoc)
    monkeypatch.setattr("app.ai.mcp.tools.operations.ToolCallLogDocument", FakeToolLogDoc)

    result = await guide_report_incident(
        reservation_id=str(res_id),
        severity="high",
        description="Caballo se asusto durante el recorrido. Sin lesiones.",
        trace_id=str(uuid4()),
    )

    assert result["reported"] is True
    assert result["incident_id"] is not None
    assert result["blocking_reasons"] == []
    assert len(inserted) == 1


def test_reports_incident_successfully(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    asyncio.run(_run_reports_incident_successfully(monkeypatch))


async def _run_incident_blocks_when_reservation_not_found(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_get(_):
        return None

    monkeypatch.setattr(ReservationDocument, "get", fake_get)
    monkeypatch.setattr("app.ai.mcp.tools.operations.ToolCallLogDocument", FakeToolLogDoc)

    result = await guide_report_incident(
        reservation_id=str(PydanticObjectId()),
        severity="medium",
        description="Incidente de prueba sin reserva.",
        trace_id=str(uuid4()),
    )

    assert result["reported"] is False
    assert len(result["blocking_reasons"]) == 1
    assert result["blocking_reasons"][0]["code"] == "reservation.not_found"


def test_incident_blocks_when_reservation_not_found(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    asyncio.run(_run_incident_blocks_when_reservation_not_found(monkeypatch))


# ---------------------------------------------------------------------------
# admin_close_service_execution
# ---------------------------------------------------------------------------


async def _run_closes_service_successfully(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    res_id = PydanticObjectId()
    reservation = SimpleNamespace(
        id=res_id,
        status=ReservationStatus.CONFIRMED,
        completed_at=None,
    )

    async def fake_get(_):
        return reservation

    monkeypatch.setattr(ReservationDocument, "get", fake_get)

    saved = []

    async def fake_save():
        saved.append(True)

    reservation.save = fake_save

    inserted = []

    class FakeServiceLogDoc:
        def __init__(self, **kwargs: Any) -> None:
            for k, v in kwargs.items():
                setattr(self, k, v)

        async def insert(self) -> None:
            self.id = PydanticObjectId()
            inserted.append(self)

    monkeypatch.setattr("app.ai.mcp.tools.operations.ServiceLogDocument", FakeServiceLogDoc)
    monkeypatch.setattr("app.ai.mcp.tools.operations.ToolCallLogDocument", FakeToolLogDoc)

    result = await admin_close_service_execution(
        reservation_id=str(res_id),
        notes="Servicio completado sin novedad.",
        trace_id=str(uuid4()),
    )

    assert result["closed"] is True
    assert result["reservation_id"] == str(res_id)
    assert result["blocking_reasons"] == []
    assert len(saved) == 1
    assert reservation.status == ReservationStatus.COMPLETED
    assert len(inserted) == 1


def test_closes_service_successfully(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    asyncio.run(_run_closes_service_successfully(monkeypatch))


async def _run_close_blocks_when_not_confirmed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    res_id = PydanticObjectId()
    reservation = SimpleNamespace(
        id=res_id,
        status=ReservationStatus.PENDING_PAYMENT,
        completed_at=None,
        status_value="pending_payment",
    )

    async def fake_get(_):
        return reservation

    monkeypatch.setattr(ReservationDocument, "get", fake_get)
    monkeypatch.setattr("app.ai.mcp.tools.operations.ToolCallLogDocument", FakeToolLogDoc)

    result = await admin_close_service_execution(
        reservation_id=str(res_id),
        trace_id=str(uuid4()),
    )

    assert result["closed"] is False
    assert len(result["blocking_reasons"]) == 1
    assert result["blocking_reasons"][0]["code"] == "reservation.invalid_status_transition"


def test_close_blocks_when_not_confirmed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    asyncio.run(_run_close_blocks_when_not_confirmed(monkeypatch))


# ---------------------------------------------------------------------------
# admin_add_equine_health_event
# ---------------------------------------------------------------------------


async def _run_adds_health_event_successfully(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    equine_id = PydanticObjectId()
    equine = SimpleNamespace(id=equine_id, name="Pegaso")

    async def fake_get(_):
        return equine

    monkeypatch.setattr(EquineDocument, "get", fake_get)

    inserted = []

    class FakeServiceLogDoc:
        def __init__(self, **kwargs: Any) -> None:
            for k, v in kwargs.items():
                setattr(self, k, v)

        async def insert(self) -> None:
            self.id = PydanticObjectId()
            inserted.append(self)

    monkeypatch.setattr("app.ai.mcp.tools.operations.ServiceLogDocument", FakeServiceLogDoc)
    monkeypatch.setattr("app.ai.mcp.tools.operations.ToolCallLogDocument", FakeToolLogDoc)

    result = await admin_add_equine_health_event(
        equine_id=str(equine_id),
        event_type="health_check",
        description="Revision veterinaria general. Todo en orden.",
        severity="low",
        trace_id=str(uuid4()),
    )

    assert result["created"] is True
    assert result["event_id"] is not None
    assert "Pegaso" in result["message"]
    assert result["blocking_reasons"] == []


def test_adds_health_event_successfully(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    asyncio.run(_run_adds_health_event_successfully(monkeypatch))


async def _run_health_event_blocks_when_equine_not_found(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_get(_):
        return None

    monkeypatch.setattr(EquineDocument, "get", fake_get)
    monkeypatch.setattr("app.ai.mcp.tools.operations.ToolCallLogDocument", FakeToolLogDoc)

    result = await admin_add_equine_health_event(
        equine_id=str(PydanticObjectId()),
        event_type="note",
        description="Evento sin equino.",
        trace_id=str(uuid4()),
    )

    assert result["created"] is False
    assert len(result["blocking_reasons"]) == 1
    assert result["blocking_reasons"][0]["code"] == "equine.not_found"


def test_health_event_blocks_when_equine_not_found(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    asyncio.run(_run_health_event_blocks_when_equine_not_found(monkeypatch))


# ---------------------------------------------------------------------------
# admin_get_equine_workload
# ---------------------------------------------------------------------------


async def _run_returns_workload_for_all_equines(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    equine_id = PydanticObjectId()
    equines = [
        SimpleNamespace(id=equine_id, name="Pegaso", is_available=True),
        SimpleNamespace(id=PydanticObjectId(), name="Relampago", is_available=False),
    ]

    async def fake_equine_list():
        return equines

    async def fake_assignment_list():
        return [
            SimpleNamespace(
                equine_id=equine_id,
                reservation_id=PydanticObjectId(),
            )
        ]

    monkeypatch.setattr(
        EquineDocument,
        "find_all",
        lambda: SimpleNamespace(to_list=fake_equine_list),
    )
    _patch_beanie_find(
        monkeypatch,
        AssignmentDocument,
        ["equine_id", "reservation_id"],
        fake_assignment_list,
    )

    confirmed_reservation = SimpleNamespace(
        status=ReservationStatus.CONFIRMED,
        requested_date=date(2026, 6, 20),
    )

    async def fake_reservation_get(rid):
        return confirmed_reservation

    monkeypatch.setattr(ReservationDocument, "get", fake_reservation_get)
    monkeypatch.setattr("app.ai.mcp.tools.operations.ToolCallLogDocument", FakeToolLogDoc)

    result = await admin_get_equine_workload(trace_id=str(uuid4()))

    assert result["blocking_reasons"] == []
    assert result["total"] == 2
    pegaso = next(w for w in result["workload"] if w["name"] == "Pegaso")
    assert pegaso["upcoming_assignments"] == 1
    assert pegaso["next_date"] == "2026-06-20"


def test_returns_workload_for_all_equines(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    asyncio.run(_run_returns_workload_for_all_equines(monkeypatch))


async def _run_workload_filters_by_available(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    equines = [
        SimpleNamespace(id=PydanticObjectId(), name="Pegaso", is_available=True),
        SimpleNamespace(id=PydanticObjectId(), name="Relampago", is_available=False),
    ]

    async def fake_equine_list():
        return equines

    async def fake_empty_list():
        return []

    monkeypatch.setattr(
        EquineDocument,
        "find_all",
        lambda: SimpleNamespace(to_list=fake_equine_list),
    )
    _patch_beanie_find(
        monkeypatch,
        AssignmentDocument,
        ["equine_id", "reservation_id"],
        fake_empty_list,
    )
    monkeypatch.setattr("app.ai.mcp.tools.operations.ToolCallLogDocument", FakeToolLogDoc)

    result = await admin_get_equine_workload(
        only_available=True,
        trace_id=str(uuid4()),
    )

    assert result["total"] == 1
    assert result["workload"][0]["name"] == "Pegaso"
    assert result["workload"][0]["is_available"] is True


def test_workload_filters_by_available(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    asyncio.run(_run_workload_filters_by_available(monkeypatch))


# ---------------------------------------------------------------------------
# admin_update_equine_availability
# ---------------------------------------------------------------------------


async def _run_updates_availability_successfully(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    equine_id = PydanticObjectId()
    equine = SimpleNamespace(
        id=equine_id,
        name="Pegaso",
        is_available=True,
        availability_notes=None,
    )
    saved = []

    async def fake_save():
        saved.append(True)

    equine.save = fake_save

    async def fake_get(_):
        return equine

    monkeypatch.setattr(EquineDocument, "get", fake_get)
    monkeypatch.setattr("app.ai.mcp.tools.operations.ToolCallLogDocument", FakeToolLogDoc)

    result = await admin_update_equine_availability(
        equine_id=str(equine_id),
        is_available=False,
        reason="Lesion en pata derecha. Reposo 2 semanas.",
        trace_id=str(uuid4()),
    )

    assert result["updated"] is True
    assert result["is_available"] is False
    assert "Pegaso" in result["message"]
    assert result["blocking_reasons"] == []
    assert len(saved) == 1


def test_updates_availability_successfully(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    asyncio.run(_run_updates_availability_successfully(monkeypatch))


async def _run_update_availability_blocks_when_equine_not_found(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_get(_):
        return None

    monkeypatch.setattr(EquineDocument, "get", fake_get)
    monkeypatch.setattr("app.ai.mcp.tools.operations.ToolCallLogDocument", FakeToolLogDoc)

    result = await admin_update_equine_availability(
        equine_id=str(PydanticObjectId()),
        is_available=False,
        reason="Prueba de equino no encontrado.",
        trace_id=str(uuid4()),
    )

    assert result["updated"] is False
    assert len(result["blocking_reasons"]) == 1
    assert result["blocking_reasons"][0]["code"] == "equine.not_found"


def test_update_availability_blocks_when_equine_not_found(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    asyncio.run(_run_update_availability_blocks_when_equine_not_found(monkeypatch))


async def _run_update_availability_accepts_trace_id(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    equine_id = PydanticObjectId()
    equine = SimpleNamespace(
        id=equine_id,
        name="Pegaso",
        is_available=True,
        availability_notes=None,
    )

    async def fake_save():
        pass

    equine.save = fake_save

    async def fake_get(_):
        return equine

    monkeypatch.setattr(EquineDocument, "get", fake_get)
    monkeypatch.setattr("app.ai.mcp.tools.operations.ToolCallLogDocument", FakeToolLogDoc)

    trace_id = str(uuid4())
    result = await admin_update_equine_availability(
        equine_id=str(equine_id),
        is_available=True,
        reason="Actualizacion de disponibilidad.",
        trace_id=trace_id,
    )

    assert result["trace_id"] == trace_id
    assert result["updated"] is True


def test_update_availability_accepts_trace_id(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    asyncio.run(_run_update_availability_accepts_trace_id(monkeypatch))
