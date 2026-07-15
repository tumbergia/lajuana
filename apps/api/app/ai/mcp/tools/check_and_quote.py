"""Combined tool: check availability AND quote in a single call.

This is the streamlined path for the WhatsApp bot. When the user provides
experience + date + participant_count in one message, this tool returns
availability + price quote in a single response, asking for name and email
to continue. This replaces the previous 3-step flow (check → confirm → quote
→ confirm → ask for name/email) with a single tool call when possible.

Why a combined tool?
- The bot must respond in one WhatsApp message to reduce token usage and
  avoid back-and-forth on the client.
- A single tool call avoids the LLM having to chain two tool results.
- The response includes a `quote_snapshot` ready for `create_reservation_draft`.
"""

from __future__ import annotations

import time
from datetime import UTC, date, datetime
from typing import Any
from uuid import uuid4

from beanie import PydanticObjectId

from app.ai.language.messages import t
from app.ai.mcp.tool_contracts import (
    CheckAvailabilityAndQuoteInput,
    CheckAvailabilityAndQuoteOutput,
    ToolBlockingReason,
)
from app.core.config import settings
from app.core.di import Container
from app.documents.experience_document import ExperienceDocument
from app.documents.tool_call_log_document import ToolCallLogDocument
from app.services.experience_catalog_resolver import (
    ExperienceCatalogResolver,
    ExperienceResolutionStatus,
)


def _safe_str(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


def _field(obj: Any, *names: str, default: Any = None) -> Any:
    for name in names:
        if hasattr(obj, name):
            value = getattr(obj, name)
            if value is not None:
                return value
    return default


def _violates_min_notice(requested_date: date, min_notice_days: int) -> bool:
    today = datetime.now(UTC).date()
    delta_days = (requested_date - today).days
    return delta_days < min_notice_days


def _format_currency(amount: Any, currency: str) -> str:
    if isinstance(amount, (int, float)):
        return f"${float(amount):,.0f} {currency}".replace(",", ".")
    return f"${amount} {currency}"


def _format_date_for_user(d: date) -> str:
    """Formato humano para mostrar al usuario: 5 de agosto de 2026 / August 5, 2026."""
    months_es = [
        "enero", "febrero", "marzo", "abril", "mayo", "junio",
        "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
    ]
    months_en = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December",
    ]
    return d.strftime("%Y-%m-%d")


async def _find_experience(
    experience_id: str | None,
    experience_query: str | None,
) -> Any | None:
    resolver = ExperienceCatalogResolver()
    if experience_id:
        result = await resolver.resolve(experience_id)
        if result.status == ExperienceResolutionStatus.FOUND:
            return await ExperienceDocument.get(result.experience_id), result.experience_id
        return None, None
    if not experience_query:
        return None, None
    result = await resolver.resolve(experience_query)
    if result.status == ExperienceResolutionStatus.FOUND:
        return await ExperienceDocument.get(result.experience_id), result.experience_id
    return None, None


def _resolve_pricing_tier(pricing: Any, participant_count: int) -> Any | None:
    if pricing is None:
        return None
    tiers = getattr(pricing, "tiers", None)
    if not tiers:
        return None
    for tier in tiers:
        min_p = getattr(tier, "min_participants", 0)
        max_p = getattr(tier, "max_participants", 0)
        if min_p <= participant_count <= max_p:
            return tier
    return None


async def check_availability_and_quote(**kwargs: Any) -> dict[str, Any]:
    """Consulta disponibilidad y cotiza en una sola llamada.

    Devuelve un `response` listo para enviar al usuario. Si hay disponibilidad
    Y tarifa configurada, pregunta por nombre y correo en el mismo mensaje
    para avanzar directamente a la pre-reserva.
    """
    trace_id = kwargs.pop("trace_id", None) or str(uuid4())
    conversation_turn_id = kwargs.pop("conversation_turn_id", None)
    language: str = kwargs.pop("language", "es")
    started = time.perf_counter()

    payload: CheckAvailabilityAndQuoteInput | None = None
    output: CheckAvailabilityAndQuoteOutput | None = None
    error_code: str | None = None

    try:
        filtered = {
            k: v for k, v in kwargs.items()
            if k in CheckAvailabilityAndQuoteInput.model_fields
        }
        payload = CheckAvailabilityAndQuoteInput.model_validate(filtered)

        min_notice_days = settings.assistant_default_min_notice_days
        reasons: list[ToolBlockingReason] = []

        experience, experience_id = await _find_experience(
            payload.experience_id, payload.experience_query
        )
        if experience is None:
            reasons.append(
                ToolBlockingReason(
                    code="experience.not_found",
                    message=t("check_quote_not_found", language),
                )
            )
            output = CheckAvailabilityAndQuoteOutput(
                available=False,
                quoted=False,
                trace_id=trace_id,
                experience_id=None,
                experience_name=None,
                requested_date=payload.requested_date,
                participant_count=payload.participant_count,
                response=t("check_quote_not_found", language),
                blocking_reasons=reasons,
            )
            return output.model_dump(mode="json")

        experience_name = _safe_str(
            _field(experience, "name", "title", "label")
        )

        if _violates_min_notice(payload.requested_date, min_notice_days):
            reasons.append(
                ToolBlockingReason(
                    code="reservation.min_notice_violation",
                    message=t(
                        "check_quote_min_notice", language, min_notice_days=min_notice_days
                    ),
                )
            )
            output = CheckAvailabilityAndQuoteOutput(
                available=False,
                quoted=False,
                trace_id=trace_id,
                experience_id=experience_id,
                experience_name=experience_name,
                requested_date=payload.requested_date,
                participant_count=payload.participant_count,
                response=t(
                    "check_quote_min_notice", language, min_notice_days=min_notice_days
                ),
                blocking_reasons=reasons,
            )
            return output.model_dump(mode="json")

        reservation_service = Container.get_instance().reservation_service
        has_active = await reservation_service.has_active_reservation_for_date(
            payload.requested_date
        )
        available = not has_active
        if has_active:
            reasons.append(
                ToolBlockingReason(
                    code="reservation.date_already_booked",
                    message=t("check_quote_already_booked", language),
                )
            )

        tier = _resolve_pricing_tier(
            pricing=getattr(experience, "pricing", None),
            participant_count=payload.participant_count,
        )

        if tier is None:
            reasons.append(
                ToolBlockingReason(
                    code="quote.pricing_not_configured",
                    message=t("check_quote_pricing_missing", language),
                )
            )
            output = CheckAvailabilityAndQuoteOutput(
                available=available,
                quoted=False,
                trace_id=trace_id,
                experience_id=experience_id,
                experience_name=experience_name,
                requested_date=payload.requested_date,
                participant_count=payload.participant_count,
                response=t("check_quote_pricing_missing", language),
                blocking_reasons=reasons,
            )
            return output.model_dump(mode="json")

        unit_price = tier.price_per_person
        subtotal = unit_price * payload.participant_count
        quote_snapshot = {
            "unit_price": unit_price,
            "subtotal": subtotal,
            "participant_count": payload.participant_count,
            "currency": "COP",
            "tier_min": tier.min_participants,
            "tier_max": tier.max_participants,
            "experience_id": experience_id,
            "experience_name": experience_name,
        }

        if not available:
            output = CheckAvailabilityAndQuoteOutput(
                available=False,
                quoted=True,
                trace_id=trace_id,
                experience_id=experience_id,
                experience_name=experience_name,
                requested_date=payload.requested_date,
                participant_count=payload.participant_count,
                unit_price=unit_price,
                subtotal=subtotal,
                currency="COP",
                quote_snapshot=quote_snapshot,
                response=t("check_quote_already_booked", language),
                blocking_reasons=reasons,
            )
            return output.model_dump(mode="json")

        response = t(
            "check_quote_available_with_quote",
            language,
            experience_name=experience_name or "La experiencia",
            participants=payload.participant_count,
            date=_format_date_for_user(payload.requested_date),
            subtotal=f"{subtotal:,.0f}".replace(",", "."),
            unit_price=f"{unit_price:,.0f}".replace(",", "."),
        )

        output = CheckAvailabilityAndQuoteOutput(
            available=True,
            quoted=True,
            trace_id=trace_id,
            experience_id=experience_id,
            experience_name=experience_name,
            requested_date=payload.requested_date,
            participant_count=payload.participant_count,
            unit_price=unit_price,
            subtotal=subtotal,
            currency="COP",
            quote_snapshot=quote_snapshot,
            response=response,
            blocking_reasons=[],
        )
        return output.model_dump(mode="json")

    except Exception as exc:
        error_code = "tool.unhandled_error"
        if payload is not None:
            requested_date_obj = payload.requested_date
            participant_count = payload.participant_count
        else:
            requested_date_obj = kwargs.get("requested_date") or datetime.now(UTC).date()
            participant_count = int(kwargs.get("participant_count") or 1)
        output = CheckAvailabilityAndQuoteOutput(
            available=False,
            quoted=False,
            trace_id=trace_id,
            experience_id=None,
            experience_name=None,
            requested_date=requested_date_obj,
            participant_count=participant_count,
            response=str(exc),
            blocking_reasons=[
                ToolBlockingReason(code=error_code, message=str(exc))
            ],
        )
        return output.model_dump(mode="json")

    finally:
        latency_ms = int((time.perf_counter() - started) * 1000)
        await ToolCallLogDocument(
            trace_id=trace_id,
            conversation_turn_id=conversation_turn_id,
            tool_name="check_availability_and_quote",
            input=payload.model_dump(mode="json") if payload else {},
            output=output.model_dump(mode="json") if output else {},
            status="error" if error_code else "success",
            error_code=error_code,
            latency_ms=latency_ms,
        ).insert()
