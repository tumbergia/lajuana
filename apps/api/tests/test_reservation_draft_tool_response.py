import asyncio
from datetime import date
from types import SimpleNamespace

import pytest

from app.ai.mcp.tools import reservation_draft
from app.ai.mcp.tools.reservation_draft import (
    attach_payment_proof_to_reservation,
    create_reservation_draft,
    get_reservation_public_summary,
    get_reservation_status_by_phone,
)
from app.services.config_service import ConfigService
from app.services.payment_proof_service import PaymentProofService
from app.services.reservation_draft_service import ReservationDraftService


async def _run_create_reservation_draft_includes_payment_and_disclaimer(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_create(self, **kwargs):
        return {
            "created": True,
            "code": "PR-20260515-ABC123",
            "status": "pre_reserved",
            "expire_at": "2026-05-16T11:30:00Z",
            "message": "ok",
        }

    async def fake_payment_instructions(self):
        return SimpleNamespace(
            manual_transfer_enabled=True,
            account_bank="Banco Demo",
            account_type="Ahorros",
            account_number="1234567890",
            account_holder_name="La Juana SAS",
            account_holder_id="NIT 900000000-1",
            transfer_note="Enviar soporte con codigo.",
            bold_enabled=True,
            bold_checkout_url="https://checkout.bold.co/demo",
            bold_surcharge_percent=7,
            bold_note="Comisión del intermediario.",
        )

    class FakeToolCallLogDocument:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

        async def insert(self):
            return None

    monkeypatch.setattr(ReservationDraftService, "create_reservation_draft", fake_create)
    monkeypatch.setattr(ConfigService, "get_payment_instructions", fake_payment_instructions)
    monkeypatch.setattr(reservation_draft, "ToolCallLogDocument", FakeToolCallLogDocument)

    result = await create_reservation_draft(
        experience_id="681f6fd71909bdcf4f7405ba",
        schedule_id="681f6fd71909bdcf4f7405bb",
        participant_count=3,
        holder_phone="+573001234567",
        holder_name="Test",
        requested_date=date(2026, 5, 20),
        quote_snapshot={
            "experience_name": "Cabalgata Basica",
            "subtotal": 450000,
            "currency": "COP",
        },
        conversation_id="conv-1",
    )

    response = result.get("response") or ""
    assert "Pre-reserva registrada" in response
    assert "Resumen:" in response
    assert "Cabalgata Basica" in response
    assert "2026-05-20" in response
    assert "3" in response
    assert "PR-20260515-ABC123" in response
    assert "Para confirmar la reserva sigue estos pasos:" in response
    assert "BANCO DEMO" in response
    assert "no está confirmada" in response
    assert "verifica el pago" in response
    assert "revalida la disponibilidad" in response


def test_create_reservation_draft_includes_payment_and_disclaimer(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    asyncio.run(_run_create_reservation_draft_includes_payment_and_disclaimer(monkeypatch))


async def _run_get_payment_instructions_returns_defaults(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_get_payment_instructions_document(self):
        return None

    monkeypatch.setattr(
        ConfigService,
        "get_payment_instructions_document",
        fake_get_payment_instructions_document,
    )

    config = await ConfigService().get_payment_instructions()
    assert config.account_bank == "Bancolombia"
    assert config.account_type == "Ahorros"
    assert config.account_number == "7165 1544 758"
    assert config.account_holder_name == "Jairo Ramírez Londoño"
    assert config.transfer_note


def test_get_payment_instructions_returns_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    asyncio.run(_run_get_payment_instructions_returns_defaults(monkeypatch))


def test_attach_payment_proof_to_reservation_returns_under_review(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeToolCallLogDocument:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

        async def insert(self):
            return None

    async def fake_get_attachable_reservation(self, **kwargs):
        return SimpleNamespace(
            id="res-1", code="PR-123", status=SimpleNamespace(value="pending_payment")
        )

    async def fake_find_existing_by_whatsapp_message(self, **kwargs):
        return None

    async def fake_find_existing_by_hash(self, **kwargs):
        return None

    async def fake_create_metadata_only(self, **kwargs):
        return SimpleNamespace(id="proof-1")

    async def fake_get(*args, **kwargs):
        return SimpleNamespace(code="PR-123", status=SimpleNamespace(value="pending_payment"))

    monkeypatch.setattr(reservation_draft, "ToolCallLogDocument", FakeToolCallLogDocument)
    monkeypatch.setattr(
        PaymentProofService, "get_attachable_reservation", fake_get_attachable_reservation
    )
    monkeypatch.setattr(
        PaymentProofService,
        "find_existing_by_whatsapp_message",
        fake_find_existing_by_whatsapp_message,
    )
    monkeypatch.setattr(PaymentProofService, "find_existing_by_hash", fake_find_existing_by_hash)
    monkeypatch.setattr(PaymentProofService, "create_metadata_only", fake_create_metadata_only)
    monkeypatch.setattr(reservation_draft.ReservationDocument, "get", fake_get)

    result = asyncio.run(
        attach_payment_proof_to_reservation(
            reservation_id="res-1",
            from_phone="+573001112233",
            whatsapp_message_id="wamid.1",
            media_id="media-1",
            media_mime_type="image/jpeg",
            filename="proof.jpg",
        )
    )

    assert result["attached"] is True
    assert result["proof_status"] == "under_review"
    assert "NO esta confirmada" in result["response"]


def test_get_reservation_public_summary_uses_single_query_argument(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeToolCallLogDocument:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

        async def insert(self):
            return None

    captured: dict[str, object] = {}

    async def fake_find_one(query):
        captured["query"] = query
        return SimpleNamespace(
            code="PR-123",
            status=SimpleNamespace(value="pending_payment"),
            expire_at=None,
            participant_count=2,
        )

    monkeypatch.setattr(reservation_draft, "ToolCallLogDocument", FakeToolCallLogDocument)
    monkeypatch.setattr(reservation_draft.ReservationDocument, "find_one", fake_find_one)

    result = asyncio.run(
        get_reservation_public_summary(code="PR-123", holder_phone="+573001112233")
    )

    assert result["found"] is True
    assert captured["query"] == {"code": "PR-123", "holder_phone": "+573001112233"}


def test_get_reservation_public_summary_requires_holder_phone(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeToolCallLogDocument:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

        async def insert(self):
            return None

    monkeypatch.setattr(reservation_draft, "ToolCallLogDocument", FakeToolCallLogDocument)

    result = asyncio.run(get_reservation_public_summary(code="PR-123"))

    assert result["found"] is False
    assert result["blocking_reasons"][0]["code"] == "tool.unhandled_error"
    assert "holder_phone" in result["blocking_reasons"][0]["message"]


def test_get_reservation_status_by_phone_prefers_active_then_newest(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeToolCallLogDocument:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

        async def insert(self):
            return None

    class FakeFindQuery:
        def __init__(self, items):
            self.items = items

        async def to_list(self):
            return self.items

    monkeypatch.setattr(reservation_draft, "ToolCallLogDocument", FakeToolCallLogDocument)

    older_active = SimpleNamespace(
        code="PR-OLD-ACTIVE",
        status=SimpleNamespace(value="pending_payment"),
        updated_at="2026-05-10T10:00:00Z",
        created_at="2026-05-10T09:00:00Z",
        expire_at=None,
        participant_count=2,
    )
    newer_terminal = SimpleNamespace(
        code="PR-NEW-TERM",
        status=SimpleNamespace(value="cancelled"),
        updated_at="2026-05-12T10:00:00Z",
        created_at="2026-05-12T09:00:00Z",
        expire_at=None,
        participant_count=4,
    )

    def fake_find(_query):
        return FakeFindQuery([older_active, newer_terminal])

    monkeypatch.setattr(reservation_draft.ReservationDocument, "find", fake_find)

    result = asyncio.run(get_reservation_status_by_phone(holder_phone="+573001112233"))

    assert result["found"] is True
    assert result["code"] == "PR-OLD-ACTIVE"


def test_get_reservation_status_by_phone_falls_back_to_newest_any(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeToolCallLogDocument:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

        async def insert(self):
            return None

    class FakeFindQuery:
        def __init__(self, items):
            self.items = items

        async def to_list(self):
            return self.items

    monkeypatch.setattr(reservation_draft, "ToolCallLogDocument", FakeToolCallLogDocument)

    older_terminal = SimpleNamespace(
        code="PR-OLD",
        status=SimpleNamespace(value="expired"),
        updated_at="2026-05-10T10:00:00Z",
        created_at="2026-05-10T09:00:00Z",
        expire_at=None,
        participant_count=2,
    )
    newer_terminal = SimpleNamespace(
        code="PR-NEW",
        status=SimpleNamespace(value="cancelled"),
        updated_at="2026-05-12T10:00:00Z",
        created_at="2026-05-12T09:00:00Z",
        expire_at=None,
        participant_count=4,
    )

    def fake_find(_query):
        return FakeFindQuery([older_terminal, newer_terminal])

    monkeypatch.setattr(reservation_draft.ReservationDocument, "find", fake_find)

    result = asyncio.run(get_reservation_status_by_phone(holder_phone="+573001112233"))

    assert result["found"] is True
    assert result["code"] == "PR-NEW"
