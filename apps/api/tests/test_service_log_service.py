"""Tests for ServiceLogService.

Covers: create with reservation/checkpoint validation, update, not-found errors.
"""

from __future__ import annotations

import asyncio
from datetime import datetime
from types import SimpleNamespace

import pytest

from app.common.labels import ErrorCode
from app.core.errors import ApiError


class TestServiceLogServiceCreate:

    def test_create_note_success(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Valid note log → ServiceLogDocument inserted."""
        from app.documents.service_log_document import ServiceLogEventType
        from app.schemas.service_log import ServiceLogCreateSchema
        from app.services.service_log_service import ServiceLogService

        inserted_docs: list[object] = []
        captured_kwargs: dict[str, object] = {}

        class FakeDoc:
            def __init__(self, **kwargs: object) -> None:
                captured_kwargs.update(kwargs)
                for k, v in kwargs.items():
                    setattr(self, k, v)

            async def insert(self) -> None:
                inserted_docs.append(self)

        async def get_reservation(_id: str) -> SimpleNamespace:
            return SimpleNamespace(id="res_001", code="RES-001")

        async def run() -> None:
            monkeypatch.setattr(
                "app.services.service_log_service.ReservationDocument.get",
                get_reservation,
            )
            monkeypatch.setattr(
                "app.services.service_log_service.ServiceLogDocument",
                FakeDoc,
            )

            service = ServiceLogService()
            payload = ServiceLogCreateSchema(
                reservation_id="res_001",
                event_type=ServiceLogEventType.NOTE,
                happened_at=datetime(2026, 6, 1, 10, 0),
                notes="Test note entry",
            )
            result = await service.create(payload)
            assert result is not None
            assert len(inserted_docs) == 1
            assert captured_kwargs["event_type"] == ServiceLogEventType.NOTE
            assert captured_kwargs["notes"] == "Test note entry"

        asyncio.run(run())

    def test_create_reservation_not_found(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Missing reservation → ApiError 404."""
        from app.schemas.service_log import ServiceLogCreateSchema
        from app.services.service_log_service import ServiceLogService

        async def get_none(_id: str) -> None:
            return None

        async def run() -> None:
            monkeypatch.setattr(
                "app.services.service_log_service.ReservationDocument.get",
                get_none,
            )

            service = ServiceLogService()
            payload = ServiceLogCreateSchema(
                reservation_id="nonexistent",
                event_type="note",
                happened_at=datetime(2026, 6, 1, 10, 0),
            )
            with pytest.raises(ApiError) as exc:
                await service.create(payload)
            assert exc.value.status_code == 404
            assert exc.value.code == ErrorCode.RESERVATION_NOT_FOUND

        asyncio.run(run())

    def test_create_checkpoint_without_name_raises_400(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Checkpoint event type without checkpoint_name → ApiError 400."""
        from app.documents.service_log_document import ServiceLogEventType
        from app.schemas.service_log import ServiceLogCreateSchema
        from app.services.service_log_service import ServiceLogService

        async def get_reservation(_id: str) -> SimpleNamespace:
            return SimpleNamespace(id="res_001")

        async def run() -> None:
            monkeypatch.setattr(
                "app.services.service_log_service.ReservationDocument.get",
                get_reservation,
            )

            service = ServiceLogService()
            payload = ServiceLogCreateSchema(
                reservation_id="res_001",
                event_type=ServiceLogEventType.CHECKPOINT,
                happened_at=datetime(2026, 6, 1, 10, 0),
                checkpoint_name=None,
            )
            with pytest.raises(ApiError) as exc:
                await service.create(payload)
            assert exc.value.status_code == 400
            assert exc.value.code == ErrorCode.LOG_CHECKPOINT_NAME_REQUIRED

        asyncio.run(run())

    def test_create_checkpoint_success(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Checkpoint with valid name → ServiceLogDocument inserted."""
        from app.documents.service_log_document import ServiceLogEventType
        from app.schemas.service_log import ServiceLogCreateSchema
        from app.services.service_log_service import ServiceLogService

        inserted_docs: list[object] = []

        class FakeDoc:
            def __init__(self, **kwargs: object) -> None:
                for k, v in kwargs.items():
                    setattr(self, k, v)

            async def insert(self) -> None:
                inserted_docs.append(self)

        async def get_reservation(_id: str) -> SimpleNamespace:
            return SimpleNamespace(id="res_001")

        async def run() -> None:
            monkeypatch.setattr(
                "app.services.service_log_service.ReservationDocument.get",
                get_reservation,
            )
            monkeypatch.setattr(
                "app.services.service_log_service.ServiceLogDocument",
                FakeDoc,
            )

            service = ServiceLogService()
            payload = ServiceLogCreateSchema(
                reservation_id="res_001",
                event_type=ServiceLogEventType.CHECKPOINT,
                happened_at=datetime(2026, 6, 1, 10, 0),
                checkpoint_name="mount_preparation",
            )
            result = await service.create(payload)
            assert result is not None
            assert len(inserted_docs) == 1
            assert result.checkpoint_name == "mount_preparation"

        asyncio.run(run())
