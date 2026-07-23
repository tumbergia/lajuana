"""Tests for ReservationProviderService."""

from __future__ import annotations

import asyncio
from types import SimpleNamespace

import pytest

from app.common.labels import ErrorCode
from app.core.errors import ApiError
from app.documents.provider_document import ProviderStatus, ProviderType


class TestReservationProviderService:
    def test_create_rejects_inactive_provider(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from app.services.reservation_provider_service import ReservationProviderService

        reservation = SimpleNamespace(id="res_1", experience_id="exp_1", code="R-001")
        provider = SimpleNamespace(
            id="prov_1",
            name="Hotel",
            type=ProviderType.LODGING,
            is_active=False,
            status=ProviderStatus.INACTIVE,
            contact_name=None,
            email=None,
            whatsapp_phone=None,
            location_label=None,
            capacity_notes=None,
            operational_notes=None,
            tariff_notes=None,
        )

        async def get_reservation(_id: str) -> SimpleNamespace:
            return reservation

        async def get_provider(_id: str) -> SimpleNamespace:
            return provider

        async def run() -> None:
            service = ReservationProviderService()
            monkeypatch.setattr(service, "_get_reservation", get_reservation)
            monkeypatch.setattr(service, "_get_provider", get_provider)

            from app.schemas.reservation_provider import ReservationProviderCreateSchema

            with pytest.raises(ApiError) as exc:
                await service.create_for_reservation(
                    "res_1",
                    ReservationProviderCreateSchema(provider_id="prov_1"),
                )
            assert exc.value.code == ErrorCode.PROVIDER_NOT_ASSOCIABLE

        asyncio.run(run())

    def test_create_rejects_duplicate(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from app.services.reservation_provider_service import ReservationProviderService

        reservation = SimpleNamespace(
            id="res_1",
            experience_id="exp_1",
            code="R-001",
            requested_date=None,
            participant_count=2,
        )
        provider = SimpleNamespace(
            id="prov_1",
            name="Hotel",
            type=ProviderType.LODGING,
            is_active=True,
            status=ProviderStatus.ACTIVE,
            contact_name=None,
            email=None,
            whatsapp_phone=None,
            location_label=None,
            capacity_notes=None,
            operational_notes=None,
            tariff_notes=None,
        )
        existing = SimpleNamespace(id="link_1")

        async def get_reservation(_id: str) -> SimpleNamespace:
            return reservation

        async def get_provider(_id: str) -> SimpleNamespace:
            return provider

        async def find_one(_query: dict) -> SimpleNamespace:
            return existing

        async def run() -> None:
            service = ReservationProviderService()
            monkeypatch.setattr(service, "_get_reservation", get_reservation)
            monkeypatch.setattr(service, "_get_provider", get_provider)
            monkeypatch.setattr(
                "app.services.reservation_provider_service.ReservationProviderDocument.find_one",
                find_one,
            )

            from app.schemas.reservation_provider import ReservationProviderCreateSchema

            with pytest.raises(ApiError) as exc:
                await service.create_for_reservation(
                    "res_1",
                    ReservationProviderCreateSchema(
                        provider_id="prov_1",
                        service_label="Alojamiento",
                    ),
                )
            assert exc.value.code == ErrorCode.RESERVATION_PROVIDER_DUPLICATE

        asyncio.run(run())

    def test_delete_not_found_for_other_reservation(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        from app.services.reservation_provider_service import ReservationProviderService

        reservation = SimpleNamespace(id="res_1")
        link = SimpleNamespace(id="link_1", reservation_id="res_other", provider_id="prov_1")

        async def get_reservation(_id: str) -> SimpleNamespace:
            return reservation

        async def get(_id: str) -> SimpleNamespace:
            return link

        async def run() -> None:
            service = ReservationProviderService()
            monkeypatch.setattr(service, "_get_reservation", get_reservation)
            monkeypatch.setattr(service, "get", get)

            with pytest.raises(ApiError) as exc:
                await service.delete_for_reservation("res_1", "link_1")
            assert exc.value.code == ErrorCode.RESERVATION_PROVIDER_NOT_FOUND

        asyncio.run(run())
