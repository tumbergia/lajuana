"""Tests for PolicyService.

Covers: create with reservation/provider validation, update, not-found errors.
"""

from __future__ import annotations

import asyncio
from datetime import datetime
from types import SimpleNamespace

import pytest

from app.common.labels import ErrorCode
from app.core.errors import ApiError


def _fake_reservation(**overrides: object) -> SimpleNamespace:
    base = dict(id="reservation_001", code="RES-001")
    base.update(overrides)
    return SimpleNamespace(**base)


def _fake_provider(**overrides: object) -> SimpleNamespace:
    base = dict(id="provider_001", name="Test Provider", is_active=True)
    base.update(overrides)
    return SimpleNamespace(**base)


class TestPolicyServiceCreate:
    def test_create_success(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from app.schemas.policy import PolicyCreateSchema
        from app.services.policy_service import PolicyService

        inserted_docs: list[object] = []
        captured_kwargs: dict[str, object] = {}

        class FakePolicyDoc:
            def __init__(self, **kwargs: object) -> None:
                captured_kwargs.update(kwargs)
                for k, v in kwargs.items():
                    setattr(self, k, v)

            async def insert(self) -> None:
                inserted_docs.append(self)

        async def get_reservation(_id: str) -> SimpleNamespace:
            return _fake_reservation()

        async def get_provider(_id: str) -> SimpleNamespace:
            return _fake_provider()

        async def run() -> None:
            monkeypatch.setattr(
                "app.services.policy_service.ReservationDocument.get",
                get_reservation,
            )
            monkeypatch.setattr(
                "app.services.policy_service.ProviderDocument.get",
                get_provider,
            )
            monkeypatch.setattr(
                "app.services.policy_service.PolicyDocument",
                FakePolicyDoc,
            )

            service = PolicyService()
            payload = PolicyCreateSchema(
                reservation_id="reservation_001",
                provider_id="provider_001",
                policy_number="POL-001",
                issued_at=datetime(2026, 1, 1),
                expires_at=datetime(2027, 1, 1),
            )
            result = await service.create(payload)
            assert result is not None
            assert len(inserted_docs) == 1
            assert captured_kwargs["policy_number"] == "POL-001"
            assert captured_kwargs["reservation_id"] == "reservation_001"

        asyncio.run(run())

    def test_create_reservation_not_found(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from app.schemas.policy import PolicyCreateSchema
        from app.services.policy_service import PolicyService

        async def get_none(_id: str) -> None:
            return None

        async def run() -> None:
            monkeypatch.setattr(
                "app.services.policy_service.ReservationDocument.get",
                get_none,
            )

            service = PolicyService()
            payload = PolicyCreateSchema(
                reservation_id="nonexistent",
                policy_number="POL-999",
            )
            with pytest.raises(ApiError) as exc:
                await service.create(payload)
            assert exc.value.status_code == 404
            assert exc.value.code == ErrorCode.RESERVATION_NOT_FOUND

        asyncio.run(run())

    def test_create_provider_not_found(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from app.schemas.policy import PolicyCreateSchema
        from app.services.policy_service import PolicyService

        async def get_reservation(_id: str) -> SimpleNamespace:
            return _fake_reservation()

        async def get_none(_id: str) -> None:
            return None

        async def run() -> None:
            monkeypatch.setattr(
                "app.services.policy_service.ReservationDocument.get",
                get_reservation,
            )
            monkeypatch.setattr(
                "app.services.policy_service.ProviderDocument.get",
                get_none,
            )

            service = PolicyService()
            payload = PolicyCreateSchema(
                reservation_id="reservation_001",
                provider_id="nonexistent",
                policy_number="POL-999",
            )
            with pytest.raises(ApiError) as exc:
                await service.create(payload)
            assert exc.value.status_code == 404
            assert exc.value.code == ErrorCode.PROVIDER_NOT_FOUND

        asyncio.run(run())


class TestPolicyServiceUpdate:
    def test_update_success(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from app.schemas.policy import PolicyUpdateSchema
        from app.services.policy_service import PolicyService

        saved_docs: list[object] = []

        async def fake_save() -> None:
            saved_docs.append(fake_doc)

        fake_doc = SimpleNamespace(id="pol_001", provider_id="old_provider", save=fake_save)

        async def get_policy(_id: str) -> SimpleNamespace:
            return fake_doc

        async def get_provider(_id: str) -> SimpleNamespace:
            return _fake_provider()

        async def run() -> None:
            monkeypatch.setattr(
                "app.services.policy_service.PolicyDocument.get",
                get_policy,
            )
            monkeypatch.setattr(
                "app.services.policy_service.ProviderDocument.get",
                get_provider,
            )

            service = PolicyService()
            payload = PolicyUpdateSchema(provider_id="new_provider")
            result = await service.update("pol_001", payload)
            assert len(saved_docs) == 1
            # Service resolves provider_id to the provider document's actual id
            assert result.provider_id == "provider_001"

        asyncio.run(run())

    def test_update_not_found(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from app.schemas.policy import PolicyUpdateSchema
        from app.services.policy_service import PolicyService

        async def get_none(_id: str) -> None:
            return None

        async def run() -> None:
            monkeypatch.setattr(
                "app.services.policy_service.PolicyDocument.get",
                get_none,
            )

            service = PolicyService()
            payload = PolicyUpdateSchema(provider_id="new_provider")
            with pytest.raises(ApiError) as exc:
                await service.update("nonexistent", payload)
            assert exc.value.status_code == 404
            assert exc.value.code == ErrorCode.POLICY_NOT_FOUND

        asyncio.run(run())
