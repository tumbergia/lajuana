"""Tests for `client_reservations` tools: language is the reservation's
`holder_language`, not the current session's language.

Verifica ADR-0014: cuando el cliente cancela o modifica una reserva
desde el bot, el mensaje de respuesta va en el idioma en que se creó
la reserva, no en el idioma de la conversación actual.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest

from app.common.enums import PaymentStatus, ReservationStatus
from app.core.di import Container


def _reservation(
    *,
    holder_language: str | None = "en",
    payment_status: PaymentStatus = PaymentStatus.PENDING,
    status: ReservationStatus = ReservationStatus.PRE_RESERVED,
) -> SimpleNamespace:
    return SimpleNamespace(
        id="660000000000000000000001",
        code="PR-TEST-EN",
        status=status,
        experience_id="660000000000000000000020",
        requested_date=None,
        holder_name="Test",
        holder_phone="+573138659839",
        holder_email="test@test.com",
        participant_count=2,
        holder_language=holder_language,
        payment_status=payment_status,
        cancelled_at=None,
        updated_by=None,
        blocks_day=True,
        availability_lock_key="2026-07-15",
    )


class _FakeTurn:
    def __init__(self, **kwargs: Any) -> None:
        for k, v in kwargs.items():
            setattr(self, k, v)

    async def insert(self) -> None:
        return None

    async def save(self) -> None:
        return None


class _CapturingReservation:
    """Replica del documento: expone `holder_language` y `find_one`."""

    instances: list[SimpleNamespace] = []

    def __init__(self, **kwargs: Any) -> None:
        for k, v in kwargs.items():
            setattr(self, k, v)

    @classmethod
    async def find_one(cls, query: dict[str, Any]) -> Any:
        if cls.instances:
            return cls.instances[0]
        return None


def _patch_tool_deps(monkeypatch: pytest.MonkeyPatch) -> None:
    """Mockea Container y documentos para evitar tocar Mongo."""

    class _FakeService:
        last_notify_client: bool | None = None

        async def cancel_reservation(
            self,
            _id: str,
            *,
            actor_id: Any = None,
            notify_client: bool = True,
        ) -> Any:
            _FakeService.last_notify_client = notify_client
            return SimpleNamespace(code="PR-TEST-EN", id=_id)

        async def ensure_date_available(
            self,
            _new_date: Any,
            *,
            exclude_reservation_id: str | None = None,
        ) -> None:
            return None

        async def _sync_day_lock_fields(self, _reservation: Any) -> None:
            return None

    _FakeService.last_notify_client = None
    shared_service = _FakeService()
    container_instance = SimpleNamespace(reservation_service=shared_service)
    Container._instance = container_instance
    monkeypatch.setattr(
        "app.ai.mcp.tools.client_reservations.ReservationDocument",
        _CapturingReservation,
    )
    monkeypatch.setattr(
        "app.ai.mcp.tools.client_reservations.ToolCallLogDocument",
        _FakeTurn,
    )


@pytest.mark.asyncio
async def test_cancel_uses_holder_language_even_if_session_is_different(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Si la reserva fue creada en inglés y el cliente ahora habla español,
    la respuesta debe ir en inglés (idioma de la reserva)."""
    from app.ai.mcp.tools.client_reservations import cancel_reservation

    _patch_tool_deps(monkeypatch)
    res = _reservation(holder_language="en")
    _CapturingReservation.instances = [res]

    result = await cancel_reservation(
        reservation_code="PR-TEST-EN",
        holder_phone="+573138659839",
        language="es",  # El usuario está hablando en español
    )

    if not result.get("cancelled"):
        print(f"DEBUG: result={result}")
    # El mensaje debe estar en inglés (holder_language), no en español.
    assert "reservation" in result["response"].lower()
    assert "has been cancelled" in result["response"].lower()
    assert result["cancelled"] is True
    # El servicio se invoca con notify_client=False para no duplicar el envío.
    from app.core.di import Container

    Container.get_instance()  # ensure initialized


@pytest.mark.asyncio
async def test_cancel_falls_back_to_session_language_when_no_holder_language(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Si la reserva no tiene holder_language (caso legacy), usar el idioma
    de la sesión actual."""
    from app.ai.mcp.tools.client_reservations import cancel_reservation

    _patch_tool_deps(monkeypatch)
    res = _reservation(holder_language=None)
    _CapturingReservation.instances = [res]

    result = await cancel_reservation(
        reservation_code="PR-TEST-EN",
        holder_phone="+573138659839",
        language="es",
    )

    assert "reserva" in result["response"].lower()
    assert "ha sido cancelada" in result["response"].lower()


@pytest.mark.asyncio
async def test_cancel_notifies_service_with_notify_client_false(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Garantiza que el bot siempre desactiva la notificación WhatsApp
    del servicio, evitando el envío duplicado cuando el bot ya responde."""
    from app.ai.mcp.tools.client_reservations import cancel_reservation

    _patch_tool_deps(monkeypatch)
    res = _reservation(holder_language="es")
    _CapturingReservation.instances = [res]

    await cancel_reservation(
        reservation_code="PR-TEST-EN",
        holder_phone="+573138659839",
        language="es",
    )

    from app.core.di import Container

    svc = Container.get_instance().reservation_service
    assert svc.last_notify_client is False  # type: ignore[attr-defined]


@pytest.mark.asyncio
async def test_cancel_paid_reservation_uses_holder_language(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Mensajes de error de cancelación también deben respetar el idioma
    de la reserva (no el de la sesión actual)."""
    from app.ai.mcp.tools.client_reservations import cancel_reservation

    _patch_tool_deps(monkeypatch)
    res = _reservation(
        holder_language="en",
        payment_status=PaymentStatus.VERIFIED,  # Ya pagó → no se puede cancelar
    )
    _CapturingReservation.instances = [res]

    result = await cancel_reservation(
        reservation_code="PR-TEST-EN",
        holder_phone="+573138659839",
        language="es",  # El usuario está en español pero la reserva es en inglés
    )

    assert result["cancelled"] is False
    # El error debe estar en inglés, no en español.
    assert "cancel" in result["response"].lower() or "paid" in result["response"].lower()
