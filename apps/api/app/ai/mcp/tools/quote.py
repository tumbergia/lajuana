from __future__ import annotations

import time
from typing import Any
from uuid import uuid4

from app.ai.mcp.tool_contracts import (
    QuoteExperienceOutput,
    QuotePricingTier,
    ToolBlockingReason,
)
from app.documents.tool_call_log_document import ToolCallLogDocument
from app.schemas.experience import ExperienceQuoteRequestSchema
from app.services.experience_catalog_resolver import (
    ExperienceCatalogResolver,
    ExperienceResolutionStatus,
)
from app.services.experience_service import ExperienceService


def _safe_str(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


async def quote_experience(
    *,
    experience_id: str | None = None,
    experience_query: str | None = None,
    participant_count: int | None = None,
    participants_count: int | None = None,
    schedule_id: str | None = None,
    requested_date: str | None = None,
    special_conditions: dict[str, str] | None = None,
    trace_id: str | None = None,
    conversation_turn_id: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    trace_id = trace_id or str(uuid4())
    count = participants_count or participant_count
    started = time.perf_counter()

    output: QuoteExperienceOutput | None = None
    error_code: str | None = None

    try:
        if count is None or count < 1:
            output = QuoteExperienceOutput(
                quoted=False,
                trace_id=trace_id,
                participants_count=count or 0,
                blocking_reasons=[
                    ToolBlockingReason(
                        code="quote.missing_participant_count",
                        message="Falta el numero de participantes para cotizar.",
                    )
                ],
            )
            return output.model_dump()

        resolver = ExperienceCatalogResolver()

        if experience_id:
            resolution = await resolver.resolve(experience_id)
        elif experience_query:
            resolution = await resolver.resolve(experience_query)
        else:
            output = QuoteExperienceOutput(
                quoted=False,
                trace_id=trace_id,
                participants_count=count,
                blocking_reasons=[
                    ToolBlockingReason(
                        code="experience.not_found",
                        message="No encontre una experiencia que coincida con la solicitud.",
                    )
                ],
            )
            return output.model_dump()

        if resolution.status != ExperienceResolutionStatus.FOUND:
            output = QuoteExperienceOutput(
                quoted=False,
                trace_id=trace_id,
                participants_count=count,
                blocking_reasons=[
                    ToolBlockingReason(
                        code="experience.not_found",
                        message="No encontre una experiencia que coincida con la solicitud.",
                    )
                ],
            )
            return output.model_dump()

        quote = await ExperienceService().quote(
            resolution.experience_id,
            ExperienceQuoteRequestSchema(
                participants_count=count,
                schedule_id=schedule_id,
                special_conditions=(
                    list(special_conditions.values()) if special_conditions else []
                ),
            ),
        )

        output = QuoteExperienceOutput(
            quoted=True,
            trace_id=trace_id,
            experience_id=quote.experience_id,
            experience_name=resolution.experience_name,
            participants_count=quote.participants_count,
            unit_price=quote.unit_price,
            subtotal=quote.subtotal,
            currency=quote.currency,
            pricing_tier=QuotePricingTier(
                min_participants=quote.pricing_tier.min_participants,
                max_participants=quote.pricing_tier.max_participants,
                price_per_person=quote.pricing_tier.price_per_person,
            ),
            requested_date=requested_date,
            notes=quote.notes,
        )
        return output.model_dump()

    except Exception as exc:
        error_code = "tool.unhandled_error"
        output = QuoteExperienceOutput(
            quoted=False,
            trace_id=trace_id,
            participants_count=count or 0,
            blocking_reasons=[
                ToolBlockingReason(
                    code=error_code,
                    message=str(exc),
                )
            ],
        )
        return output.model_dump()

    finally:
        latency_ms = int((time.perf_counter() - started) * 1000)
        await ToolCallLogDocument(
            trace_id=trace_id,
            conversation_turn_id=conversation_turn_id,
            tool_name="quote_experience",
            input={
                "experience_id": _safe_str(experience_id),
                "experience_query": _safe_str(experience_query),
                "participants_count": count,
                "schedule_id": _safe_str(schedule_id),
            },
            output=output.model_dump(mode="json") if output else {},
            status="error" if error_code else "success",
            error_code=error_code,
            latency_ms=latency_ms,
        ).insert()
