"""Tests for ReservationWhatsAppNotificationService.

Verifies that deterministic WhatsApp messages are sent (via mocked outbound)
when the service methods are called. Does NOT test through the HTTP endpoint —
tests the service layer directly to avoid DB dependencies.
"""

from __future__ import annotations

import asyncio
from types import SimpleNamespace
from typing import Any

import pytest
from beanie import PydanticObjectId

from app.channels.whatsapp.outbound_service import WhatsAppOutboundService
from app.common.enums import ParticipantFormStatus, UserRole
from app.documents import (
    ExperienceDocument,
    ReservationAuditLogDocument,
    ReservationDocument,
)
from app.documents.conversation_turn_document import ConversationTurnDocument
from app.documents.notification_template_document import NotificationTemplateDocument
from app.notifications.reservation_whatsapp_notification_service import (
    ReservationWhatsAppNotificationService,
)
from app.services.participant_form_link_service import ParticipantFormLinkService


# ---------------------------------------------------------------------------
# Fakes
# ---------------------------------------------------------------------------


class FakeDoc:
    def __init__(self, **kwargs: Any) -> None:
        for k, v in kwargs.items():
            setattr(self, k, v)

    async def insert(self) -> None:
        self.id = "fake-id"

    async def save(self) -> None:
        pass


def _fake_reservation(**overrides: Any) -> Any:
    data = {
        "id": PydanticObjectId(),
        "code": "RES-001",
        "experience_id": PydanticObjectId(),
        "holder_phone": "+573001112233",
        "holder_name": "Carlos",
        "holder_email": None,
        "form_url": None,
        "expected_participants_count": 2,
        "participant_form_status": ParticipantFormStatus.NOT_SENT,
        "participant_form_sent_at": None,
        "participant_form_sent_by": None,
        "participant_form_send_count": 0,
        "participant_form_last_message_id": None,
        "confirmation_message_sent_at": None,
        "confirmation_message_sent_by": None,
        "requested_date": None,
        "schedule_id": None,
    }
    data.update(overrides)
    return FakeDoc(**data)


def _fake_experience(**overrides: Any) -> Any:
    data = {"name": "Los Chorros", "id": PydanticObjectId()}
    data.update(overrides)
    return SimpleNamespace(**data)


def _fake_template(**overrides: Any) -> Any:
    data = {
        "template_key": "payment_approved_form_sent.customer",
        "channel": "whatsapp",
        "body": (
            "Hola {{customer_name}}, tu pago para {{experience_name}} "
            "fue aprobado. Formulario: {{form_url}}"
        ),
    }
    data.update(overrides)
    return SimpleNamespace(**data)


def _fake_schedule(**overrides: Any) -> Any:
    data = {
        "date": None,
        "start_time": "08:00:00",
    }
    data.update(overrides)
    return SimpleNamespace(**data)


# ---------------------------------------------------------------------------
# Mocks
# ---------------------------------------------------------------------------


def _apply_base_mocks(monkeypatch: pytest.MonkeyPatch) -> None:
    """Mock all DB document inserts and the outbound service for every test."""

    # ConversationTurnDocument constructor calls get_motor_collection → fail without DB.
    # Replace the whole class with a cheap fake.
    monkeypatch.setattr(
        "app.notifications.reservation_whatsapp_notification_service.ConversationTurnDocument",
        FakeDoc,
    )
    monkeypatch.setattr(ReservationAuditLogDocument, "insert", lambda _: FakeDoc().insert())

    async def fake_save(self: Any) -> None:
        pass

    monkeypatch.setattr(ReservationDocument, "save", fake_save)

    async def fake_find_one_template(*args: Any, **kwargs: Any) -> Any:
        # find_one receives filter as first positional arg
        filter_dict = args[0] if args else kwargs
        template_key = filter_dict.get("template_key", "") if filter_dict else ""
        if "payment_approved_form_sent" in template_key:
            return _fake_template(template_key="payment_approved_form_sent.customer")
        if "payment_rejected_sent" in template_key:
            return _fake_template(
                template_key="payment_rejected_sent.customer",
                body=(
                    "Hola {{customer_name}}, el comprobante para {{experience_name}} "
                    "fue rechazado: {{rejection_reason}}"
                ),
            )
        if "reservation_confirmed_logistics_sent" in template_key:
            return _fake_template(
                template_key="reservation_confirmed_logistics_sent.customer",
                body=(
                    "Hola {{customer_name}}, tu reserva {{reservation_code}} para "
                    "{{experience_name}} el {{scheduled_date}} a las {{start_time}}. "
                    "Lugar: {{meeting_point}}"
                ),
            )
        if "participant_form_resent" in template_key:
            return _fake_template(
                template_key="participant_form_resent.customer",
                body="Hola {{customer_name}}, formulario: {{form_url}}",
            )
        return None

    monkeypatch.setattr(NotificationTemplateDocument, "find_one", fake_find_one_template)

    async def fake_experience_get(_: Any) -> Any:
        return _fake_experience()

    monkeypatch.setattr(ExperienceDocument, "get", fake_experience_get)


def _apply_outbound_mock(monkeypatch: pytest.MonkeyPatch) -> list[dict[str, Any]]:
    """Replace WhatsAppOutboundService.send with a captor. Returns the call list."""
    calls: list[dict[str, Any]] = []

    async def fake_send(self: Any, *, turn: Any, to_phone: str, text: str) -> Any:
        calls.append({"to_phone": to_phone, "text": text, "turn": turn})
        return SimpleNamespace(provider_message_id="wamid.fake", status="sent")

    monkeypatch.setattr(WhatsAppOutboundService, "send", fake_send)
    return calls


def _apply_form_link_mock(monkeypatch: pytest.MonkeyPatch) -> None:
    """Mock ParticipantFormLinkService.generate so form_url is generated."""
    async def fake_generate(
        self: Any,
        *,
        reservation_id: str,
        expected_participants_count: int,
        created_by: PydanticObjectId | None = None,
        channel: str = "whatsapp",
        sent_to_phone: str | None = None,
    ) -> tuple[Any, str]:
        doc = SimpleNamespace(
            max_participants=expected_participants_count,
            used_count=0,
            expires_at=None,
        )
        return doc, "fake-raw-token"

    monkeypatch.setattr(ParticipantFormLinkService, "generate", fake_generate)


# ---------------------------------------------------------------------------
# Tests: payment approved → form WhatsApp
# ---------------------------------------------------------------------------


def test_send_payment_approved_creates_form_url_and_sends_whatsapp(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _apply_base_mocks(monkeypatch)
    _apply_form_link_mock(monkeypatch)
    calls = _apply_outbound_mock(monkeypatch)

    reservation = _fake_reservation()

    service = ReservationWhatsAppNotificationService()

    async def run() -> bool:
        return await service.send_payment_approved_participant_form(
            reservation=reservation,
            actor_id=PydanticObjectId(),
        )

    result = asyncio.run(run())

    assert result is True
    assert len(calls) == 1
    assert calls[0]["to_phone"] == "+573001112233"
    assert "Carlos" in calls[0]["text"]
    assert "Los Chorros" in calls[0]["text"]
    assert "formulario-participantes?t=fake-raw-token" in calls[0]["text"]
    assert reservation.form_url is not None
    assert "formulario-participantes" in reservation.form_url


def test_send_payment_approved_idempotent_skips_if_already_sent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _apply_base_mocks(monkeypatch)
    calls = _apply_outbound_mock(monkeypatch)

    reservation = _fake_reservation(
        participant_form_sent_at="2026-01-01T00:00:00",
        form_url="http://test.form/url",
    )

    service = ReservationWhatsAppNotificationService()

    async def run() -> bool:
        return await service.send_payment_approved_participant_form(
            reservation=reservation,
            actor_id=PydanticObjectId(),
        )

    result = asyncio.run(run())

    assert result is True
    assert len(calls) == 0  # No WhatsApp sent


def test_send_payment_approved_no_phone_skips(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _apply_base_mocks(monkeypatch)
    calls = _apply_outbound_mock(monkeypatch)

    reservation = _fake_reservation(holder_phone=None)
    service = ReservationWhatsAppNotificationService()

    async def run() -> bool:
        return await service.send_payment_approved_participant_form(
            reservation=reservation,
            actor_id=PydanticObjectId(),
        )

    result = asyncio.run(run())

    assert result is False
    assert len(calls) == 0


def test_send_payment_approved_outbound_failure_returns_false(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _apply_base_mocks(monkeypatch)
    _apply_form_link_mock(monkeypatch)

    async def fake_send_fail(self: Any, **kwargs: Any) -> Any:
        raise RuntimeError("Graph API down")

    monkeypatch.setattr(WhatsAppOutboundService, "send", fake_send_fail)

    reservation = _fake_reservation()
    service = ReservationWhatsAppNotificationService()

    async def run() -> bool:
        return await service.send_payment_approved_participant_form(
            reservation=reservation,
            actor_id=PydanticObjectId(),
        )

    result = asyncio.run(run())

    assert result is False  # Failure doesn't raise, returns False


# ---------------------------------------------------------------------------
# Tests: payment rejected → rejection WhatsApp
# ---------------------------------------------------------------------------


def test_send_payment_rejected_sends_whatsapp_with_reason(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _apply_base_mocks(monkeypatch)
    calls = _apply_outbound_mock(monkeypatch)

    reservation = _fake_reservation()
    service = ReservationWhatsAppNotificationService()

    async def run() -> bool:
        return await service.send_payment_rejected(
            reservation=reservation,
            reason="Monto incorrecto",
            actor_id=PydanticObjectId(),
        )

    result = asyncio.run(run())

    assert result is True
    assert len(calls) == 1
    assert "Monto incorrecto" in calls[0]["text"]
    assert "Carlos" in calls[0]["text"]
    assert "Los Chorros" in calls[0]["text"]
    # Rejection should NOT include form URL
    assert "formulario" not in calls[0]["text"].lower()


# ---------------------------------------------------------------------------
# Tests: reservation confirmed → logistics WhatsApp
# ---------------------------------------------------------------------------


def test_send_confirmed_logistics_sends_whatsapp(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from datetime import date

    _apply_base_mocks(monkeypatch)
    calls = _apply_outbound_mock(monkeypatch)

    reservation = _fake_reservation(
        requested_date=date(2026, 6, 20),
        schedule_id=PydanticObjectId(),
    )

    async def fake_schedule_get(_: Any) -> Any:
        return _fake_schedule(date=date(2026, 6, 20))

    monkeypatch.setattr(
        "app.notifications.reservation_whatsapp_notification_service.ScheduleDocument.get",
        fake_schedule_get,
    )

    service = ReservationWhatsAppNotificationService()

    async def run() -> bool:
        return await service.send_reservation_confirmed_logistics(
            reservation=reservation,
            actor_id=PydanticObjectId(),
        )

    result = asyncio.run(run())

    assert result is True
    assert len(calls) == 1
    assert "Carlos" in calls[0]["text"]
    assert "RES-001" in calls[0]["text"]
    assert "Los Chorros" in calls[0]["text"]
    assert "08:00" in calls[0]["text"]
    # Logistics should NOT include form URL
    assert "formulario" not in calls[0]["text"].lower()


def test_send_confirmed_logistics_idempotent_skips_if_already_sent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _apply_base_mocks(monkeypatch)
    calls = _apply_outbound_mock(monkeypatch)

    reservation = _fake_reservation(confirmation_message_sent_at="2026-01-01T00:00:00")
    service = ReservationWhatsAppNotificationService()

    async def run() -> bool:
        return await service.send_reservation_confirmed_logistics(
            reservation=reservation,
            actor_id=PydanticObjectId(),
        )

    result = asyncio.run(run())

    assert result is True
    assert len(calls) == 0


# ---------------------------------------------------------------------------
# Tests: resend form (manual admin)
# ---------------------------------------------------------------------------


def test_resend_form_sends_whatsapp(monkeypatch: pytest.MonkeyPatch) -> None:
    _apply_base_mocks(monkeypatch)
    _apply_form_link_mock(monkeypatch)
    calls = _apply_outbound_mock(monkeypatch)

    reservation = _fake_reservation()
    service = ReservationWhatsAppNotificationService()

    async def run() -> bool:
        return await service.resend_participant_form(
            reservation=reservation,
            actor_id=PydanticObjectId(),
        )

    result = asyncio.run(run())

    assert result is True
    assert len(calls) == 1
    assert "formulario" in calls[0]["text"]


def test_resend_form_no_phone_skips(monkeypatch: pytest.MonkeyPatch) -> None:
    _apply_base_mocks(monkeypatch)
    calls = _apply_outbound_mock(monkeypatch)

    reservation = _fake_reservation(holder_phone=None)
    service = ReservationWhatsAppNotificationService()

    async def run() -> bool:
        return await service.resend_participant_form(
            reservation=reservation,
            actor_id=PydanticObjectId(),
        )

    result = asyncio.run(run())

    assert result is False
    assert len(calls) == 0


# ---------------------------------------------------------------------------
# Tests: conversation_id uses canonical format
# ---------------------------------------------------------------------------


def test_send_approved_uses_canonical_conversation_id(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _apply_base_mocks(monkeypatch)
    _apply_form_link_mock(monkeypatch)
    calls = _apply_outbound_mock(monkeypatch)

    reservation = _fake_reservation(holder_phone="+573001112233")
    service = ReservationWhatsAppNotificationService()

    async def run() -> bool:
        return await service.send_payment_approved_participant_form(
            reservation=reservation,
            actor_id=PydanticObjectId(),
        )

    asyncio.run(run())

    assert len(calls) == 1
    assert calls[0]["turn"].conversation_id == "whatsapp:+573001112233"


# ---------------------------------------------------------------------------
# Tests: audit trail is created
# ---------------------------------------------------------------------------


def test_approved_creates_audit_log(monkeypatch: pytest.MonkeyPatch) -> None:
    _apply_base_mocks(monkeypatch)
    _apply_form_link_mock(monkeypatch)

    inserts: list[dict[str, Any]] = []

    class TrackingAuditLog(FakeDoc):
        async def insert(self) -> None:
            inserts.append(
                {
                    "action": self.action,
                    "metadata": self.metadata,
                }
            )

    monkeypatch.setattr(
        "app.notifications.reservation_whatsapp_notification_service.ReservationAuditLogDocument",
        TrackingAuditLog,
    )

    # Avoid BaseException from remaining mocks
    calls = _apply_outbound_mock(monkeypatch)

    reservation = _fake_reservation()
    service = ReservationWhatsAppNotificationService()

    async def run() -> bool:
        return await service.send_payment_approved_participant_form(
            reservation=reservation,
            actor_id=PydanticObjectId(),
        )

    asyncio.run(run())

    assert len(inserts) == 1
    assert inserts[0]["action"] == "notification.payment_approved_form_sent"
    assert inserts[0]["metadata"]["status"] == "sent"
    assert inserts[0]["metadata"]["template_key"] == "payment_approved_form_sent.customer"
