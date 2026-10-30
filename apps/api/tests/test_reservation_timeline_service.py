"""Tests for reservation timeline and service log permissions."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest
from beanie import PydanticObjectId

from app.common.enums import UserRole
from app.common.labels import ErrorCode
from app.core.errors import ApiError
from app.documents.service_log_document import ServiceLogEventType
from app.schemas.service_log import ServiceLogUpdateSchema
from app.services.reservation_timeline_service import ReservationTimelineService
from app.services.service_log_service import ServiceLogService

RESERVATION_ID = "6600000000000000000000aa"


def _fake_query(items: list[object]) -> SimpleNamespace:
    query = SimpleNamespace(_items=items)

    def sort(*_args: object, **_kwargs: object) -> SimpleNamespace:
        return query

    def limit(*_args: object, **_kwargs: object) -> SimpleNamespace:
        return query

    async def to_list() -> list[object]:
        return query._items

    query.sort = sort
    query.limit = limit
    query.to_list = to_list
    return query


class TestReservationTimelineService:
    def test_timeline_merges_sources_sorted_desc(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        from app.services import reservation_timeline_service as mod

        reservation_oid = PydanticObjectId(RESERVATION_ID)
        reservation = SimpleNamespace(
            id=reservation_oid,
            code="RES-001",
            created_at=datetime(2026, 1, 1, 8, 0, tzinfo=UTC),
            status=SimpleNamespace(value="confirmed"),
        )

        log = SimpleNamespace(
            id=PydanticObjectId(),
            event_type=ServiceLogEventType.NOTE,
            happened_at=datetime(2026, 6, 2, 12, 0, tzinfo=UTC),
            checkpoint_name=None,
            notes="Nota reciente",
            related_participant_id=None,
        )

        audit = SimpleNamespace(
            id=PydanticObjectId(),
            action="payment_proof.approved",
            created_at=datetime(2026, 6, 1, 10, 0, tzinfo=UTC),
            actor_user_id=None,
            actor_role=None,
            reason=None,
            metadata=None,
        )

        async def fake_get(_id: str) -> SimpleNamespace:
            return reservation

        monkeypatch.setattr(mod.ReservationDocument, "get", fake_get)
        monkeypatch.setattr(
            mod.ServiceLogDocument,
            "find",
            lambda *_args, **_kwargs: _fake_query([log]),
        )
        monkeypatch.setattr(
            mod.ReservationAuditLogDocument,
            "find",
            lambda *_args, **_kwargs: _fake_query([audit]),
        )
        monkeypatch.setattr(
            mod.ParticipantDocument,
            "find",
            lambda *_args, **_kwargs: _fake_query([]),
        )
        monkeypatch.setattr(
            mod.PaymentProofDocument,
            "find",
            lambda *_args, **_kwargs: _fake_query([]),
        )

        async def run() -> None:
            service = ReservationTimelineService()
            entries = await service.get_timeline(
                RESERVATION_ID,
                actor_role=UserRole.GUIDE,
                limit=50,
            )
            assert len(entries) == 3
            assert entries[0].kind == "note"
            assert entries[1].kind == "payment_proof.approved"
            assert entries[2].kind == "reservation.created"
            assert entries[0].editable is True
            assert entries[0].deletable is True

        asyncio.run(run())

    def test_timeline_excludes_assignment_audit_actions(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        from app.services import reservation_timeline_service as mod

        reservation_oid = PydanticObjectId(RESERVATION_ID)
        reservation = SimpleNamespace(
            id=reservation_oid,
            code="RES-002",
            created_at=datetime(2026, 1, 1, 8, 0, tzinfo=UTC),
            status=SimpleNamespace(value="confirmed"),
        )

        assignment_audit = SimpleNamespace(
            id=PydanticObjectId(),
            action="assignment.finalized",
            created_at=datetime(2026, 6, 1, 9, 0, tzinfo=UTC),
            actor_user_id=None,
            actor_role=None,
            reason=None,
            metadata=None,
        )

        async def fake_get(_id: str) -> SimpleNamespace:
            return reservation

        monkeypatch.setattr(mod.ReservationDocument, "get", fake_get)
        monkeypatch.setattr(
            mod.ServiceLogDocument,
            "find",
            lambda *_args, **_kwargs: _fake_query([]),
        )
        monkeypatch.setattr(
            mod.ReservationAuditLogDocument,
            "find",
            lambda *_args, **_kwargs: _fake_query([assignment_audit]),
        )
        monkeypatch.setattr(
            mod.ParticipantDocument,
            "find",
            lambda *_args, **_kwargs: _fake_query([]),
        )
        monkeypatch.setattr(
            mod.PaymentProofDocument,
            "find",
            lambda *_args, **_kwargs: _fake_query([]),
        )

        async def run() -> None:
            service = ReservationTimelineService()
            entries = await service.get_timeline(
                RESERVATION_ID,
                actor_role=UserRole.ADMIN,
            )
            kinds = {entry.kind for entry in entries}
            assert "assignment.finalized" not in kinds
            assert "reservation.created" in kinds

        asyncio.run(run())


class TestServiceLogPermissions:
    def test_guide_cannot_delete_automatic_log(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        doc = SimpleNamespace(
            id="log_001",
            event_type=ServiceLogEventType.ARRIVAL,
            deleted_at=None,
        )

        async def fake_get(_self: ServiceLogService, _id: str) -> SimpleNamespace:
            return doc

        monkeypatch.setattr(ServiceLogService, "get", fake_get)

        async def run() -> None:
            service = ServiceLogService()
            with pytest.raises(ApiError) as exc:
                await service.soft_delete("log_001", actor_role=UserRole.GUIDE)
            assert exc.value.status_code == 403
            assert exc.value.code == ErrorCode.AUTH_FORBIDDEN

        asyncio.run(run())

    def test_guide_can_update_manual_note(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        doc = SimpleNamespace(
            id="log_001",
            event_type=ServiceLogEventType.NOTE,
            checkpoint_name=None,
            notes="Antes",
        )
        saved: list[object] = []

        async def fake_get(_self: ServiceLogService, _id: str) -> SimpleNamespace:
            return doc

        async def fake_save() -> None:
            saved.append(doc)

        monkeypatch.setattr(ServiceLogService, "get", fake_get)
        doc.save = fake_save  # type: ignore[method-assign]

        async def run() -> None:
            service = ServiceLogService()
            updated = await service.update(
                "log_001",
                ServiceLogUpdateSchema(notes="Después"),
                actor_role=UserRole.GUIDE,
            )
            assert updated.notes == "Después"
            assert len(saved) == 1

        asyncio.run(run())
