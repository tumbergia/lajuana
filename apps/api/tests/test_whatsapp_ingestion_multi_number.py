from __future__ import annotations

from typing import Any

import pytest

from app.channels.whatsapp.ingestion_service import WhatsAppIngestionService


def _payload(*, phone_number_id: str, wa_message_id: str, from_phone: str, text: str) -> dict:
    return {
        "entry": [
            {
                "changes": [
                    {
                        "value": {
                            "metadata": {
                                "phone_number_id": phone_number_id,
                                "display_phone_number": phone_number_id,
                            },
                            "messages": [
                                {
                                    "id": wa_message_id,
                                    "from": from_phone,
                                    "type": "text",
                                    "text": {"body": text},
                                }
                            ],
                        }
                    }
                ]
            }
        ]
    }


class FakeIntegration:
    def __init__(self, *, phone_number_id: str, is_default: bool, usable: bool = True) -> None:
        self.id = phone_number_id
        self.phone_number_id = phone_number_id
        self.is_default = is_default
        self._usable = usable


class FakeIntegrationService:
    def __init__(self, integrations: dict[str, FakeIntegration]) -> None:
        self._integrations = integrations

    async def resolve_by_phone_number_id(self, phone_number_id: str | None) -> Any:
        if not phone_number_id:
            return None
        return self._integrations.get(phone_number_id)

    def is_usable(self, integration: Any) -> bool:
        return integration is not None and integration._usable


class FakeUpdateResult:
    def __init__(self, upserted_id: Any) -> None:
        self.upserted_id = upserted_id


class FakeCollection:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []
        self._seen_ids: set[str] = set()

    async def update_one(self, filt: dict, update: dict, upsert: bool = False) -> FakeUpdateResult:
        doc = update["$setOnInsert"]
        self.calls.append(doc)
        wa_message_id = filt["wa_message_id"]
        if wa_message_id in self._seen_ids:
            return FakeUpdateResult(upserted_id=None)
        self._seen_ids.add(wa_message_id)
        return FakeUpdateResult(upserted_id=wa_message_id)


class FakeResolver:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    async def resolve(self, **kwargs: Any) -> None:
        self.calls.append(kwargs)


class FakeBufferService:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    async def add_message(self, **kwargs: Any) -> None:
        self.calls.append(kwargs)


@pytest.mark.asyncio
async def test_ingest_skips_unregistered_phone_number_id(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_collection = FakeCollection()
    monkeypatch.setattr(
        "app.channels.whatsapp.ingestion_service.WhatsAppInboundEventDocument.get_motor_collection",
        classmethod(lambda cls: fake_collection),
    )

    resolver = FakeResolver()
    buffer_service = FakeBufferService()
    integration_service = FakeIntegrationService({})  # nada registrado

    service = WhatsAppIngestionService(
        resolver=resolver,
        buffer_service=buffer_service,
        integration_service=integration_service,
    )

    payload = _payload(
        phone_number_id="unknown-pn", wa_message_id="wamid.1", from_phone="573001112233", text="hola"
    )
    ingested = await service.ingest(payload)

    assert ingested == 0
    assert resolver.calls == []
    assert buffer_service.calls == []
    assert fake_collection.calls[0]["status"] == "unregistered_integration"
    assert fake_collection.calls[0]["phone_number_id"] == "unknown-pn"


@pytest.mark.asyncio
async def test_ingest_processes_registered_non_default_number_with_scoped_conversation_id(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_collection = FakeCollection()
    monkeypatch.setattr(
        "app.channels.whatsapp.ingestion_service.WhatsAppInboundEventDocument.get_motor_collection",
        classmethod(lambda cls: fake_collection),
    )

    resolver = FakeResolver()
    buffer_service = FakeBufferService()
    integration = FakeIntegration(phone_number_id="pn-2", is_default=False)
    integration_service = FakeIntegrationService({"pn-2": integration})

    service = WhatsAppIngestionService(
        resolver=resolver,
        buffer_service=buffer_service,
        integration_service=integration_service,
    )

    payload = _payload(
        phone_number_id="pn-2", wa_message_id="wamid.2", from_phone="573001112233", text="hola"
    )
    ingested = await service.ingest(payload)

    assert ingested == 1
    assert resolver.calls[0]["integration_id"] == "pn-2"
    assert resolver.calls[0]["is_default_integration"] is False
    assert buffer_service.calls[0]["conversation_id"] == "whatsapp:pn-2:+573001112233"
    assert fake_collection.calls[0]["integration_id"] == "pn-2"


@pytest.mark.asyncio
async def test_ingest_default_number_keeps_legacy_conversation_id(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_collection = FakeCollection()
    monkeypatch.setattr(
        "app.channels.whatsapp.ingestion_service.WhatsAppInboundEventDocument.get_motor_collection",
        classmethod(lambda cls: fake_collection),
    )

    resolver = FakeResolver()
    buffer_service = FakeBufferService()
    integration = FakeIntegration(phone_number_id="legacy-pn", is_default=True)
    integration_service = FakeIntegrationService({"legacy-pn": integration})

    service = WhatsAppIngestionService(
        resolver=resolver,
        buffer_service=buffer_service,
        integration_service=integration_service,
    )

    payload = _payload(
        phone_number_id="legacy-pn", wa_message_id="wamid.3", from_phone="573001112233", text="hola"
    )
    await service.ingest(payload)

    assert buffer_service.calls[0]["conversation_id"] == "whatsapp:+573001112233"
