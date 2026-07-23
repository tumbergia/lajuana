from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import httpx
import pytest

from app.channels.whatsapp.normalizer import strip_whatsapp_markup
from app.channels.whatsapp.outbound_service import WhatsAppOutboundService

# ───────────────────────── strip_whatsapp_markup ──────────────────────────


def test_markup_strips_bold_asterisks_preserving_accents() -> None:
    out = strip_whatsapp_markup("La *Cabalgata Básica* cuesta $120.000")
    assert out == "La Cabalgata Básica cuesta $120.000"
    assert "*" not in out


def test_markup_strips_double_asterisks_bold() -> None:
    out = strip_whatsapp_markup("La **Cabalgata Básica** cuesta $120.000")
    assert out == "La Cabalgata Básica cuesta $120.000"


def test_markup_strips_italics_underscores_word_only() -> None:
    out = strip_whatsapp_markup("Experiencia _súper chéveres_ disponible")
    assert out == "Experiencia súper chéveres disponible"


def test_markup_preserves_underscores_inside_identifiers() -> None:
    # Snake-case tokens con `_` intermedio no son cursiva; deben conservarse.
    out = strip_whatsapp_markup("referencia PR_1234 sigue activa")
    assert out == "referencia PR_1234 sigue activa"


def test_markup_strips_strikethrough_tildes() -> None:
    out = strip_whatsapp_markup("Promo ~caduca~ vigente")
    assert out == "Promo caduca vigente"


def test_markup_strips_code_blocks() -> None:
    out = strip_whatsapp_markup("```cabalgata-basica```")
    assert out == "cabalgata-basica"


def test_markup_collapses_three_or_more_newlines() -> None:
    out = strip_whatsapp_markup("Hola\n\n\n\n¿te ayudo?")
    assert out == "Hola\n\n¿te ayudo?"


def test_markup_preserves_all_spanish_accents() -> None:
    text = "¡Hola! Básica día más ¿te gustaría? ñandú güéi"
    assert strip_whatsapp_markup(text) == text


def test_markup_handles_empty_or_none() -> None:
    assert strip_whatsapp_markup("") == ""
    result: Any = strip_whatsapp_markup(None)  # type: ignore[arg-type]
    assert result is None


def test_markup_does_not_touch_emojis_or_long_isolated_tokens() -> None:
    out = strip_whatsapp_markup("mensaje\n👍\nfin")
    assert out == "mensaje\n👍\nfin"


# ──────────────────── WhatsAppOutboundService.send (payload) ────────────────


class _FakeOutboundDoc:
    def __init__(self, **kwargs: Any) -> None:
        for k, v in kwargs.items():
            setattr(self, k, v)
        self.outbound_id = "ob-1"
        self.provider_message_id = None
        self.status = kwargs.get("status", "queued")
        self.sent_at = None
        self.error = None

    async def insert(self) -> None:
        return None

    async def save(self) -> None:
        return None


@pytest.mark.asyncio
async def test_outbound_send_strips_markup_before_payload(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = WhatsAppOutboundService()

    sent_payload: dict[str, Any] = {}
    captured: dict[str, Any] = {}

    class _CapturingOutbound(_FakeOutboundDoc):
        def __init__(self, **kwargs: Any) -> None:
            super().__init__(**kwargs)
            captured["body"] = kwargs.get("body")

    monkeypatch.setattr(
        "app.channels.whatsapp.outbound_service.OutboundMessageDocument",
        _CapturingOutbound,
    )

    def fake_post(url: str, *, json: dict[str, Any], headers: Any) -> Any:
        sent_payload["url"] = url
        sent_payload["json"] = json

        class _Resp:
            status_code = 200

            def raise_for_status(self) -> None:
                return None

            def json(self) -> dict[str, Any]:
                return {"messages": [{"id": "wamid.X"}]}

        return _Resp()

    class _FakeClient:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            pass

        async def __aenter__(self) -> _FakeClient:
            return self

        async def __aexit__(self, *args: Any) -> None:
            return None

        async def post(self, url: str, *, json: dict[str, Any], headers: Any) -> Any:
            return fake_post(url, json=json, headers=headers)

    monkeypatch.setattr(
        "app.channels.whatsapp.outbound_service.settings",
        SimpleNamespace(
            whatsapp_send_enabled=True,
            whatsapp_access_token="tok",
            whatsapp_phone_number_id="phone123",
            whatsapp_api_version="v18",
        ),
    )
    monkeypatch.setattr(httpx, "AsyncClient", _FakeClient)

    turn = SimpleNamespace(
        id="turn-1",
        conversation_id="conv-x",
    )

    dirty = "La *Cabalgata Básica* _día_ ~viejo~ cuesta $120.000"
    await service.send(turn=turn, to_phone="+573001112233", text=dirty)

    assert "*" not in captured["body"]
    assert "~" not in captured["body"]
    assert captured["body"] == "La Cabalgata Básica día viejo cuesta $120.000"
    assert sent_payload["json"]["text"]["body"] == captured["body"]
    assert sent_payload["json"]["type"] == "text"
    assert sent_payload["json"]["to"] == "573001112233"


@pytest.mark.asyncio
async def test_outbound_send_disabled_stores_saneado(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = WhatsAppOutboundService()
    captured: dict[str, Any] = {}

    class _CapturingOutbound(_FakeOutboundDoc):
        def __init__(self, **kwargs: Any) -> None:
            super().__init__(**kwargs)
            captured["body"] = kwargs.get("body")

    monkeypatch.setattr(
        "app.channels.whatsapp.outbound_service.OutboundMessageDocument",
        _CapturingOutbound,
    )
    monkeypatch.setattr(
        "app.channels.whatsapp.outbound_service.settings",
        SimpleNamespace(
            whatsapp_send_enabled=False,
            whatsapp_access_token="",
            whatsapp_phone_number_id="",
            whatsapp_api_version="v18",
        ),
    )

    turn = SimpleNamespace(id="turn-2", conversation_id="conv-y")
    await service.send(turn=turn, to_phone="+571", text="*Básica* ```día```")

    assert captured["body"] == "Básica día"
