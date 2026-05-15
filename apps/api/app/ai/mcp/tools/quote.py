from __future__ import annotations

import time
from typing import Any
from uuid import uuid4

from beanie import PydanticObjectId

from app.ai.mcp.tool_contracts import (
    QuoteExperienceInput,
    QuoteExperienceOutput,
    QuotePricingTier,
    ToolBlockingReason,
)
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


async def quote_experience(**kwargs: Any) -> dict[str, Any]:
    trace_id = kwargs.pop("trace_id", None) or str(uuid4())
    conversation_turn_id = kwargs.pop("conversation_turn_id", None)
    started = time.perf_counter()

    payload: QuoteExperienceInput | None = None
    output: QuoteExperienceOutput | None = None
    error_code: str | None = None

    try:
        filtered = {k: v for k, v in kwargs.items() if k in QuoteExperienceInput.model_fields}
        payload = QuoteExperienceInput.model_validate(filtered)

        resolver = ExperienceCatalogResolver()

        if payload.experience_id:
            resolution = await resolver.resolve(payload.experience_id)
        elif payload.experience_query:
            resolution = await resolver.resolve(payload.experience_query)
        else:
            output = QuoteExperienceOutput(
                quoted=False,
                trace_id=trace_id,
                requested_date=payload.requested_date,
                participant_count=payload.participant_count,
                blocking_reasons=[
                    ToolBlockingReason(
                        code="experience.not_found",
                        message="No se encontró una experiencia que coincida con la solicitud.",
                    )
                ],
            )
            return output.model_dump(mode="json")

        if resolution.status != ExperienceResolutionStatus.FOUND:
            output = QuoteExperienceOutput(
                quoted=False,
                trace_id=trace_id,
                requested_date=payload.requested_date,
                participant_count=payload.participant_count,
                blocking_reasons=[
                    ToolBlockingReason(
                        code="experience.not_found",
                        message="No se encontró una experiencia que coincida con la solicitud.",
                    )
                ],
            )
            return output.model_dump(mode="json")

        experience = await ExperienceDocument.get(PydanticObjectId(resolution.experience_id))
        if experience is None:
            output = QuoteExperienceOutput(
                quoted=False,
                trace_id=trace_id,
                requested_date=payload.requested_date,
                participant_count=payload.participant_count,
                blocking_reasons=[
                    ToolBlockingReason(
                        code="experience.not_found",
                        message="La experiencia no está disponible en este momento.",
                    )
                ],
            )
            return output.model_dump(mode="json")

        tier = _resolve_pricing_tier(
            pricing=experience.pricing,
            participant_count=payload.participant_count,
        )

        if tier is None:
            output = QuoteExperienceOutput(
                quoted=False,
                trace_id=trace_id,
                requested_date=payload.requested_date,
                participant_count=payload.participant_count,
                blocking_reasons=[
                    ToolBlockingReason(
                        code="quote.pricing_not_configured",
                        message="La experiencia no tiene tarifa configurada "
                        "para esa cantidad de participantes.",
                    )
                ],
            )
            return output.model_dump(mode="json")

        subtotal = tier.price_per_person * payload.participant_count

        exp_name = getattr(experience, "name", "la experiencia")
        output = QuoteExperienceOutput(
            quoted=True,
            trace_id=trace_id,
            requested_date=payload.requested_date,
            participant_count=payload.participant_count,
            unit_price=tier.price_per_person,
            subtotal=subtotal,
            response=(
                f"{exp_name} para {payload.participant_count} persona(s) "
                f"sale a ${subtotal} COP "
                f"(${tier.price_per_person} por persona)."
            ),
            pricing_tier=QuotePricingTier(
                min_participants=tier.min_participants,
                max_participants=tier.max_participants,
                price_per_person=tier.price_per_person,
            ),
            notes=payload.notes,
            quote_snapshot={
                "unit_price": tier.price_per_person,
                "subtotal": subtotal,
                "participant_count": payload.participant_count,
                "currency": "COP",
                "tier_min": tier.min_participants,
                "tier_max": tier.max_participants,
                "experience_id": resolution.experience_id,
                "experience_name": getattr(experience, "name", None),
            },
        )
        return output.model_dump(mode="json")

    except Exception as exc:
        error_code = "tool.unhandled_error"
        pc = payload.participant_count if payload else kwargs.get("participant_count", 0)
        rd = payload.requested_date if payload else kwargs.get("requested_date")
        output = QuoteExperienceOutput(
            quoted=False,
            trace_id=trace_id,
            requested_date=rd,
            participant_count=pc,
            blocking_reasons=[
                ToolBlockingReason(
                    code=error_code,
                    message=str(exc),
                )
            ],
        )
        return output.model_dump(mode="json")

    finally:
        latency_ms = int((time.perf_counter() - started) * 1000)
        await ToolCallLogDocument(
            trace_id=trace_id,
            conversation_turn_id=conversation_turn_id,
            tool_name="quote_experience",
            input=payload.model_dump(mode="json") if payload else {},
            output=output.model_dump(mode="json") if output else {},
            status="error" if error_code else "success",
            error_code=error_code,
            latency_ms=latency_ms,
        ).insert()
