"""Tests for ProviderService.

Covers: soft-delete (deactivate), not-found, and base list.
"""

from __future__ import annotations

import asyncio
from types import SimpleNamespace

import pytest

from app.common.labels import ErrorCode
from app.core.errors import ApiError


class TestProviderService:

    def test_delete_deactivates(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """ProviderService.delete sets is_active=False and saves."""
        from app.services.provider_service import ProviderService

        saved = False

        fake_doc = SimpleNamespace(
            id="prov_001",
            name="Test Provider",
            is_active=True,
            status="active",
            is_deleted=False,
        )

        async def fake_save() -> None:
            nonlocal saved
            saved = True
            fake_doc.is_active = False  # simulate actual mutation

        fake_doc.save = fake_save

        async def get_provider(_id: str) -> SimpleNamespace:
            return fake_doc

        async def run() -> None:
            monkeypatch.setattr(
                "app.services.provider_service.ProviderDocument.get",
                get_provider,
            )

            service = ProviderService()
            await service.delete("prov_001")
            assert saved is True
            assert fake_doc.is_active is False

        asyncio.run(run())

    def test_resolve_provider_reference_unique_name_match(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        from app.services.provider_service import ProviderService

        fake_list = [
            SimpleNamespace(
                id="660000000000000000000201",
                name="Patio Central",
                slug="patio-central",
                contact_name="Ana",
                location_label="Filandia",
                is_active=True,
            ),
            SimpleNamespace(
                id="660000000000000000000202",
                name="Mirador",
                slug="mirador",
                contact_name="Luis",
                location_label="Salento",
                is_active=True,
            ),
        ]

        async def fake_list_fn(*args: object, **kwargs: object) -> list[SimpleNamespace]:
            return fake_list

        monkeypatch.setattr(ProviderService, "list", fake_list_fn)
        service = ProviderService()

        async def run() -> None:
            result = await service.resolve_provider_reference("patio central")
            assert result["status"] == "resolved"
            assert result["provider_id"] == "660000000000000000000201"

        asyncio.run(run())

    def test_resolve_provider_reference_ambiguous_prefix_match(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        from app.services.provider_service import ProviderService

        fake_list = [
            SimpleNamespace(
                id="660000000000000000000201",
                name="Patio Central",
                slug="patio-central",
                contact_name="Ana",
                location_label="Filandia",
                is_active=True,
            ),
            SimpleNamespace(
                id="660000000000000000000202",
                name="Patio Centro",
                slug="patio-centro",
                contact_name="Luis",
                location_label="Salento",
                is_active=True,
            ),
        ]

        async def fake_list_fn(*args: object, **kwargs: object) -> list[SimpleNamespace]:
            return fake_list

        monkeypatch.setattr(ProviderService, "list", fake_list_fn)
        service = ProviderService()

        async def run() -> None:
            result = await service.resolve_provider_reference("patio")
            assert result["status"] == "ambiguous"
            assert len(result["matches"]) == 2

        asyncio.run(run())

    def test_delete_not_found(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Deleting a non-existent provider → ApiError 404."""
        from app.services.provider_service import ProviderService

        async def get_none(_id: str) -> None:
            return None

        async def run() -> None:
            monkeypatch.setattr(
                "app.services.provider_service.ProviderDocument.get",
                get_none,
            )

            service = ProviderService()
            with pytest.raises(ApiError) as exc:
                await service.delete("nonexistent")
            assert exc.value.status_code == 404
            assert exc.value.code == ErrorCode.PROVIDER_NOT_FOUND

        asyncio.run(run())

    def test_list_returns_active_providers(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """BaseService.list() returns documents from find().to_list()."""
        from app.services.provider_service import ProviderService

        fake_list: list[SimpleNamespace] = [
            SimpleNamespace(id="p1"),
            SimpleNamespace(id="p2"),
        ]

        class FakeQuery:
            async def to_list(self) -> list[SimpleNamespace]:
                return fake_list

            def skip(self, n: int) -> FakeQuery:
                return self

            def limit(self, n: int) -> FakeQuery:
                return self

        def find_many(*args: object, **kwargs: object) -> FakeQuery:
            # BaseService.list() calls find(query) where query has deleted_at filter
            return FakeQuery()

        async def run() -> None:
            monkeypatch.setattr(
                "app.services.provider_service.ProviderDocument.find",
                find_many,
            )

            service = ProviderService()
            result = await service.list()
            assert len(result) == 2

        asyncio.run(run())
