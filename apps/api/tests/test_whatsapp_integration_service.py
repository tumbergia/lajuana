from __future__ import annotations

from typing import Any

import pytest

from app.channels.whatsapp.integration_service import WhatsAppIntegrationService
from app.channels.whatsapp.normalizer import build_conversation_id

# ── build_conversation_id: multi-número ──


def test_build_conversation_id_default_keeps_legacy_format() -> None:
    # El número default no debe cambiar de formato: rompería sesiones activas.
    assert (
        build_conversation_id("whatsapp", "+573001112233", phone_number_id="pn-1", is_default=True)
        == "whatsapp:+573001112233"
    )


def test_build_conversation_id_non_default_includes_phone_number_id() -> None:
    assert (
        build_conversation_id(
            "whatsapp", "+573001112233", phone_number_id="pn-2", is_default=False
        )
        == "whatsapp:pn-2:+573001112233"
    )


def test_build_conversation_id_without_phone_number_id_falls_back_to_legacy() -> None:
    assert build_conversation_id("whatsapp", "+573001112233", is_default=False) == (
        "whatsapp:+573001112233"
    )


# ── WhatsAppIntegrationService ──


class FakeIntegrationDoc:
    _store: dict[str, FakeIntegrationDoc] = {}

    def __init__(self, **kwargs: Any) -> None:
        self.id = kwargs.pop("id", None)
        for k, v in kwargs.items():
            setattr(self, k, v)
        self.is_default = kwargs.get("is_default", False)
        self.is_enabled = kwargs.get("is_enabled", True)
        self.status = kwargs.get("status", "active")
        self.access_token = kwargs.get("access_token")
        self.api_version = kwargs.get("api_version")

    async def insert(self) -> None:
        self.id = self.phone_number_id
        FakeIntegrationDoc._store[self.id] = self

    async def save(self) -> None:
        FakeIntegrationDoc._store[self.id] = self

    @classmethod
    async def find_one(cls, *args: Any, **kwargs: Any) -> FakeIntegrationDoc | None:
        filt = args[0] if args else kwargs
        phone_number_id = filt.get("phone_number_id")
        is_default = filt.get("is_default")
        for doc in cls._store.values():
            if phone_number_id is not None and doc.phone_number_id != phone_number_id:
                continue
            if is_default is not None and doc.is_default != is_default:
                continue
            return doc
        return None

    @classmethod
    async def get(cls, integration_id: str) -> FakeIntegrationDoc | None:
        return cls._store.get(integration_id)


@pytest.fixture(autouse=True)
def _reset_store() -> None:
    FakeIntegrationDoc._store.clear()


@pytest.mark.asyncio
async def test_resolve_by_phone_number_id_bootstraps_from_settings(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "app.channels.whatsapp.integration_service.WhatsAppIntegrationDocument",
        FakeIntegrationDoc,
    )
    monkeypatch.setattr(
        "app.channels.whatsapp.integration_service.settings",
        type("S", (), {"whatsapp_phone_number_id": "legacy-pn", "whatsapp_access_token": "tok"})(),
    )

    service = WhatsAppIntegrationService()
    integration = await service.resolve_by_phone_number_id("legacy-pn")

    assert integration is not None
    assert integration.is_default is True
    assert integration.phone_number_id == "legacy-pn"


@pytest.mark.asyncio
async def test_resolve_by_phone_number_id_unknown_returns_none(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "app.channels.whatsapp.integration_service.WhatsAppIntegrationDocument",
        FakeIntegrationDoc,
    )
    monkeypatch.setattr(
        "app.channels.whatsapp.integration_service.settings",
        type("S", (), {"whatsapp_phone_number_id": "legacy-pn", "whatsapp_access_token": "tok"})(),
    )

    service = WhatsAppIntegrationService()
    integration = await service.resolve_by_phone_number_id("some-other-number")

    assert integration is None


@pytest.mark.asyncio
async def test_is_usable_rejects_disabled_and_revoked(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "app.channels.whatsapp.integration_service.WhatsAppIntegrationDocument",
        FakeIntegrationDoc,
    )
    service = WhatsAppIntegrationService()

    disabled = FakeIntegrationDoc(phone_number_id="p1", is_enabled=False, status="active")
    revoked = FakeIntegrationDoc(phone_number_id="p2", is_enabled=True, status="revoked")
    active = FakeIntegrationDoc(phone_number_id="p3", is_enabled=True, status="active")

    assert service.is_usable(disabled) is False
    assert service.is_usable(revoked) is False
    assert service.is_usable(active) is True
    assert service.is_usable(None) is False


@pytest.mark.asyncio
async def test_get_send_credentials_falls_back_to_settings_when_token_unset(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "app.channels.whatsapp.integration_service.settings",
        type(
            "S",
            (),
            {"whatsapp_access_token": "settings-tok", "whatsapp_api_version": "v20.0"},
        )(),
    )
    service = WhatsAppIntegrationService()
    integration = FakeIntegrationDoc(
        phone_number_id="p1", access_token=None, api_version=None, id="p1"
    )

    creds = service.get_send_credentials(integration)

    assert creds.phone_number_id == "p1"
    assert creds.access_token == "settings-tok"
    assert creds.api_version == "v20.0"


@pytest.mark.asyncio
async def test_register_integration_rejects_duplicate_phone_number_id(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "app.channels.whatsapp.integration_service.WhatsAppIntegrationDocument",
        FakeIntegrationDoc,
    )
    service = WhatsAppIntegrationService()
    await service.register_integration(phone_number_id="p1")

    with pytest.raises(ValueError):
        await service.register_integration(phone_number_id="p1")


@pytest.mark.asyncio
async def test_register_integration_as_default_clears_previous_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "app.channels.whatsapp.integration_service.WhatsAppIntegrationDocument",
        FakeIntegrationDoc,
    )
    service = WhatsAppIntegrationService()
    first = await service.register_integration(phone_number_id="p1", is_default=True)
    second = await service.register_integration(phone_number_id="p2", is_default=True)

    assert first.is_default is False
    assert second.is_default is True


@pytest.mark.asyncio
async def test_mark_degraded_updates_status_and_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "app.channels.whatsapp.integration_service.WhatsAppIntegrationDocument",
        FakeIntegrationDoc,
    )
    service = WhatsAppIntegrationService()
    integration = await service.register_integration(phone_number_id="p1")

    await service.mark_degraded(integration.id, "401 Unauthorized")

    reloaded = await FakeIntegrationDoc.get(integration.id)
    assert reloaded is not None
    assert reloaded.status == "degraded"
    assert reloaded.last_error_message == "401 Unauthorized"
