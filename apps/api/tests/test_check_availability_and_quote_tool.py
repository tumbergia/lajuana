"""Tests for the check_availability_and_quote combined tool.

The combined tool returns a single response with availability + price quote
to streamline the WhatsApp reservation flow. It also fixes a pydantic
validation issue with AttachPaymentProofToReservationOutput.
"""

from __future__ import annotations

import asyncio
from datetime import date
from types import SimpleNamespace
from typing import Any

import pytest

from app.ai.language.messages import t
from app.ai.mcp.tool_contracts import AttachPaymentProofToReservationOutput


# ── Combined tool: contract + language templates ────────────────────────


def test_attach_payment_proof_output_allows_blocking_reasons() -> None:
    """Fix: AttachPaymentProofToReservationOutput debe permitir blocking_reasons.

    Antes, la tool intentaba pasar blocking_reasons en la salida pero el
    contrato (extra='forbid') lo rechazaba con pydantic, rompiendo el flujo
    de pago cuando había un error y la respuesta no llegaba al usuario.
    """
    from app.ai.mcp.tools.reservation_draft import ToolBlockingReason

    output = AttachPaymentProofToReservationOutput(
        attached=False,
        trace_id="t-1",
        message="Error X",
        response="No se pudo",
        blocking_reasons=[ToolBlockingReason(code="x.error", message="Detalle")],
    )
    dumped = output.model_dump(mode="json")
    assert "blocking_reasons" in dumped
    assert dumped["blocking_reasons"][0]["code"] == "x.error"


def test_check_quote_available_templates_bilingual() -> None:
    """El template del combined tool debe estar traducido en ambos idiomas."""
    es = t("check_quote_available_with_quote", "es", experience_name="X", participants=3, date="2026-08-05", subtotal="750.000", unit_price="250.000")
    en = t("check_quote_available_with_quote", "en", experience_name="X", participants=3, date="2026-08-05", subtotal="750.000", unit_price="250.000")
    assert es and en and es != en
    # ES mantiene el estilo (precio, persona, etc.)
    assert "$750.000 COP" in es
    assert "nombre completo" in es
    # EN mantiene el estilo en inglés
    assert "$750.000 COP" in en
    assert "name" in en.lower() and "email" in en.lower()


def test_check_quote_error_templates_bilingual() -> None:
    """Los templates de error del combined tool también bilingües."""
    for key in [
        "check_quote_not_found",
        "check_quote_min_notice",
        "check_quote_already_booked",
        "check_quote_pricing_missing",
    ]:
        es = t(key, "es", min_notice_days=2)
        en = t(key, "en", min_notice_days=2)
        assert es and en, f"Missing translation for {key}"
        assert es != en, f"Same translation for {key}"


# ── Combined tool: execution paths (mocked) ─────────────────────────────


class _FakeLogDoc:
    def __init__(self, **kwargs: Any) -> None:
        self.kwargs = kwargs

    async def insert(self) -> None:
        return None


def _patch_log(monkeypatch: pytest.MonkeyPatch) -> None:
    import app.ai.mcp.tools.check_and_quote as cq

    monkeypatch.setattr(cq, "ToolCallLogDocument", _FakeLogDoc)


def _patch_container_reservation_service(
    monkeypatch: pytest.MonkeyPatch, *, has_active: bool
) -> None:
    import app.ai.mcp.tools.check_and_quote as cq
    from app.core.di import Container

    class _Container:
        def __init__(self) -> None:
            self.reservation_service = SimpleNamespace(
                has_active_reservation_for_date=lambda d: asyncio.Future()
            )

    container = _Container()
    fut: Any = asyncio.Future()
    fut.set_result(has_active)
    container.reservation_service.has_active_reservation_for_date = (  # type: ignore[attr-defined]
        lambda d: fut
    )
    Container.get_instance = lambda: container  # type: ignore[assignment]


def _patch_experience_resolver(
    monkeypatch: pytest.MonkeyPatch, *, found: bool
) -> None:
    from app.services.experience_catalog_resolver import (
        ExperienceCatalogResolver,
        ExperienceResolutionStatus,
    )

    class _Resolution:
        def __init__(self, status: Any, experience_id: str | None) -> None:
            self.status = status
            self.experience_id = experience_id

    class _Experience:
        def __init__(self) -> None:
            self.id = "exp-123"
            self.name = "La Montaña de Cristal"
            self.pricing = SimpleNamespace(
                tiers=[SimpleNamespace(min_participants=1, max_participants=8, price_per_person=250000)]
            )

    async def fake_resolve(self: Any, value: Any) -> Any:
        if not found:
            return _Resolution(ExperienceResolutionStatus.NOT_FOUND, None)
        return _Resolution(ExperienceResolutionStatus.FOUND, "exp-123")

    async def fake_get(experience_id: Any) -> Any:
        return _Experience() if found else None

    from beanie import PydanticObjectId

    ExperienceCatalogResolver.resolve = fake_resolve  # type: ignore[assignment]
    from app.ai.mcp.tools import check_and_quote as cq

    async def patched_get(oid: Any) -> Any:
        return _Experience() if found else None

    cq.ExperienceDocument.get = patched_get  # type: ignore[assignment]


@pytest.mark.asyncio
async def test_check_availability_and_quote_happy_path(monkeypatch: pytest.MonkeyPatch) -> None:
    """Con experiencia + cupo + tarifa, devuelve respuesta bilingüe con precio."""
    from app.ai.mcp.tools.check_and_quote import check_availability_and_quote

    _patch_log(monkeypatch)
    _patch_container_reservation_service(monkeypatch, has_active=False)
    _patch_experience_resolver(monkeypatch, found=True)

    result = await check_availability_and_quote(
        experience_query="montaña de cristal",
        requested_date=date(2026, 8, 5),
        participant_count=3,
        language="es",
    )
    assert result["available"] is True
    assert result["quoted"] is True
    assert result["unit_price"] == 250000
    assert result["subtotal"] == 750000
    assert "Montaña" in result["experience_name"] or "montaña" in result["experience_name"].lower()
    # El response en español pide nombre y correo
    assert "nombre completo" in result["response"].lower()
    assert "correo" in result["response"].lower()
    # El quote_snapshot está listo para create_reservation_draft
    assert result["quote_snapshot"]["unit_price"] == 250000
    assert result["quote_snapshot"]["subtotal"] == 750000


@pytest.mark.asyncio
async def test_check_availability_and_quote_english(monkeypatch: pytest.MonkeyPatch) -> None:
    """La respuesta en inglés mantiene el formato estructurado (sin markdown raro)."""
    from app.ai.mcp.tools.check_and_quote import check_availability_and_quote

    _patch_log(monkeypatch)
    _patch_container_reservation_service(monkeypatch, has_active=False)
    _patch_experience_resolver(monkeypatch, found=True)

    result = await check_availability_and_quote(
        experience_query="crystal mountain",
        requested_date=date(2026, 8, 5),
        participant_count=3,
        language="en",
    )
    assert result["available"] is True
    assert result["quoted"] is True
    # El response en inglés pide name y email
    assert "name" in result["response"].lower()
    assert "email" in result["response"].lower()
    # El precio se muestra igual
    assert "$750.000 COP" in result["response"] or "$750000 COP" in result["response"].replace(",", "")


@pytest.mark.asyncio
async def test_check_availability_and_quote_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
    """Si la experiencia no existe, devuelve blocking_reasons sin response vacío."""
    from app.ai.mcp.tools.check_and_quote import check_availability_and_quote

    _patch_log(monkeypatch)
    _patch_container_reservation_service(monkeypatch, has_active=False)
    _patch_experience_resolver(monkeypatch, found=False)

    result = await check_availability_and_quote(
        experience_query="inexistente",
        requested_date=date(2026, 8, 5),
        participant_count=3,
        language="es",
    )
    assert result["available"] is False
    assert result["quoted"] is False
    assert result["blocking_reasons"]
    assert result["blocking_reasons"][0]["code"] == "experience.not_found"


@pytest.mark.asyncio
async def test_check_availability_and_quote_already_booked(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Si la fecha ya está reservada, devuelve blocking_reasons."""
    from app.ai.mcp.tools.check_and_quote import check_availability_and_quote

    _patch_log(monkeypatch)
    _patch_container_reservation_service(monkeypatch, has_active=True)
    _patch_experience_resolver(monkeypatch, found=True)

    result = await check_availability_and_quote(
        experience_query="montaña de cristal",
        requested_date=date(2026, 8, 5),
        participant_count=3,
        language="es",
    )
    assert result["available"] is False
    assert result["quoted"] is True  # Aún así devolvemos el quote
    assert result["blocking_reasons"]
    assert result["blocking_reasons"][0]["code"] == "reservation.date_already_booked"


# ── Intent router: combined tool is selected for full-info messages ──────


def test_intent_router_reserve_with_full_info_uses_combined() -> None:
    """Mensaje con intención de reservar + exp + fecha + pax → combined tool."""
    from app.ai.assistant.intent_router import detect_and_build_plan

    plan = detect_and_build_plan(
        "quiero reservar la montaña de cristal para el 5 de agosto 3 personas"
    )
    assert plan is not None
    assert plan.tool_name == "check_availability_and_quote"
    assert plan.arguments.experience_query
    assert plan.arguments.requested_date == "2026-08-05"
    assert plan.arguments.participant_count == 3


def test_intent_router_full_info_no_keyword_uses_combined_fallback() -> None:
    """Mensaje con exp + fecha + pax sin keyword explícito → fallback a combined."""
    from app.ai.assistant.intent_router import detect_and_build_plan

    # Sin keyword de reservar/price/availability, pero con los 3 datos completos.
    plan = detect_and_build_plan("the mountain experience 5 agust 3 people")
    assert plan is not None
    assert plan.tool_name == "check_availability_and_quote"


def test_intent_router_just_experience_does_not_use_combined() -> None:
    """Si solo hay experiencia, NO debe usar combined (faltan datos)."""
    from app.ai.assistant.intent_router import detect_and_build_plan

    plan = detect_and_build_plan("dame información de la montaña de cristal")
    assert plan is None or plan.tool_name != "check_availability_and_quote"
