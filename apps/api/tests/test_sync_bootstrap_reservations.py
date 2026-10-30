"""build_bootstrap() debe incluir un snapshot de reservas (activas+recientes)
con participantes/comprobantes anidados, para que el bootstrap móvil pueda
cachear todo sin depender de haber abierto cada pantalla online antes.
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest

from app.common.enums import UserRole
from app.schemas.config import EmergencyContactsResponseSchema, ReservationRulesSchema
from app.services import sync_service as sync_service_module
from app.services.config_service import ConfigService
from app.services.sync_service import SyncService


class _FakeListService:
    def __init__(self, items: list[object]) -> None:
        self._items = items

    async def list(self, *_args: object, **_kwargs: object) -> list[object]:
        return self._items


class _FakeReservationService:
    def __init__(self, items: list[object]) -> None:
        self._items = items
        self.last_actor_role: UserRole | None = None

    async def list_for_bootstrap(self, actor_role: UserRole, **_kwargs: object) -> list[object]:
        self.last_actor_role = actor_role
        return self._items


class _FakeCursor:
    def sort(self, *_args: object) -> _FakeCursor:
        return self

    async def first_or_none(self) -> None:
        return None


class _FakeSyncChangeDocumentFind:
    @staticmethod
    def find(*_args: object, **_kwargs: object) -> _FakeCursor:
        return _FakeCursor()


def _fake_user(user_id: str, role: UserRole) -> SimpleNamespace:
    now = datetime.now(UTC)
    return SimpleNamespace(
        id=user_id,
        role=role,
        model_dump=lambda **_kwargs: {
            "id": user_id,
            "email": "user@test.com",
            "full_name": "Test User",
            "role": role,
            "is_active": True,
            "version": 1,
            "created_at": now,
            "updated_at": now,
            "deleted_at": None,
        },
    )


def _fake_config_service(monkeypatch: pytest.MonkeyPatch) -> ConfigService:
    config_service = ConfigService()

    async def _fake_rules() -> ReservationRulesSchema:
        return ReservationRulesSchema(min_days_in_advance=3)

    async def _fake_contacts() -> EmergencyContactsResponseSchema:
        return EmergencyContactsResponseSchema(items=[])

    monkeypatch.setattr(config_service, "get_reservation_rules", _fake_rules)
    monkeypatch.setattr(config_service, "get_emergency_contacts", _fake_contacts)
    return config_service


def test_bootstrap_includes_reservations_from_list_for_bootstrap(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_reservation = SimpleNamespace(id="r1")

    async def _fake_reservation_to_response(doc: object) -> SimpleNamespace:
        return SimpleNamespace(
            model_dump=lambda mode="json": {
                "id": doc.id,
                "participants": [{"id": "p1"}],
                "payment_proofs": [{"id": "pp1"}],
            }
        )

    monkeypatch.setattr(
        sync_service_module, "reservation_to_response", _fake_reservation_to_response
    )
    monkeypatch.setattr(sync_service_module, "SyncChangeDocument", _FakeSyncChangeDocumentFind)

    reservation_service = _FakeReservationService([fake_reservation])
    service = SyncService(
        config_service=_fake_config_service(monkeypatch),
        experience_service=_FakeListService([]),
        equine_service=_FakeListService([]),
        reservation_service=reservation_service,
        saddle_service=_FakeListService([]),
    )

    async def run() -> None:
        current_user = _fake_user("u1", UserRole.ADMIN)
        body = await service.build_bootstrap(current_user=current_user)

        assert "reservations" in body
        assert body["reservations"] == [
            {
                "id": "r1",
                "participants": [{"id": "p1"}],
                "payment_proofs": [{"id": "pp1"}],
            }
        ]
        # El rol del usuario actual se propaga a la ventana de bootstrap.
        assert reservation_service.last_actor_role == UserRole.ADMIN
        assert "reservations" in body["cursors"]

    asyncio.run(run())


def test_bootstrap_guide_role_propagates_to_reservation_window(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def _fake_reservation_to_response(doc: object) -> SimpleNamespace:
        return SimpleNamespace(model_dump=lambda mode="json": {"id": doc.id})

    monkeypatch.setattr(
        sync_service_module, "reservation_to_response", _fake_reservation_to_response
    )
    monkeypatch.setattr(sync_service_module, "SyncChangeDocument", _FakeSyncChangeDocumentFind)

    reservation_service = _FakeReservationService([])
    service = SyncService(
        config_service=_fake_config_service(monkeypatch),
        experience_service=_FakeListService([]),
        equine_service=_FakeListService([]),
        reservation_service=reservation_service,
        saddle_service=_FakeListService([]),
    )

    async def run() -> None:
        current_user = _fake_user("u2", UserRole.GUIDE)
        await service.build_bootstrap(current_user=current_user)
        assert reservation_service.last_actor_role == UserRole.GUIDE

    asyncio.run(run())


def test_bootstrap_without_reservation_service_returns_empty_list(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Si no hay reservation_service configurado (DI parcial), no debe romper."""
    monkeypatch.setattr(sync_service_module, "SyncChangeDocument", _FakeSyncChangeDocumentFind)

    service = SyncService(
        config_service=_fake_config_service(monkeypatch),
        experience_service=_FakeListService([]),
        equine_service=_FakeListService([]),
        saddle_service=_FakeListService([]),
    )

    async def run() -> None:
        current_user = _fake_user("u3", UserRole.ADMIN)
        body = await service.build_bootstrap(current_user=current_user)
        assert body["reservations"] == []

    asyncio.run(run())
