from __future__ import annotations

import hashlib
import hmac
import json
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.api.endpoints import ask as ask_endpoint
from app.api.endpoints.whatsapp import _receive_webhook
from app.core.config import settings
from app.schemas.ask import AskRequest


@pytest.mark.asyncio
async def test_public_ask_never_trusts_admin_channel(monkeypatch: pytest.MonkeyPatch) -> None:
    captured = None

    class FakeOrchestrator:
        async def ask(self, request):
            nonlocal captured
            captured = request
            return SimpleNamespace()

    monkeypatch.setattr(ask_endpoint, "AssistantOrchestrator", FakeOrchestrator)
    await ask_endpoint.ask(AskRequest(message="hola", channel="admin_api"))
    assert captured.channel == "test"


class FakeRequest:
    def __init__(self, body: bytes, signature: str) -> None:
        self._body = body
        self.headers = {"X-Hub-Signature-256": signature}

    async def body(self) -> bytes:
        return self._body


class FakeIngestion:
    async def ingest(self, payload):
        return 1


@pytest.mark.asyncio
async def test_whatsapp_webhook_requires_valid_signature(monkeypatch: pytest.MonkeyPatch) -> None:
    body = json.dumps({"entry": []}).encode()
    monkeypatch.setattr(settings, "whatsapp_app_secret", "secret")
    with pytest.raises(HTTPException) as error:
        await _receive_webhook(FakeRequest(body, "sha256=bad"), FakeIngestion())
    assert error.value.status_code == 403

    signature = "sha256=" + hmac.new(b"secret", body, hashlib.sha256).hexdigest()
    result = await _receive_webhook(FakeRequest(body, signature), FakeIngestion())
    assert result["ingested_messages"] == 1
