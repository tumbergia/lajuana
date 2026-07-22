from __future__ import annotations

import time
from typing import Any

from app.ai.mcp.tool_contracts import ExperienceDetailItem, ExperienceDetailOutput, ToolBlockingReason
from app.documents.experience_document import ExperienceDocument
from app.documents.tool_call_log_document import ToolCallLogDocument
from app.services.experience_catalog_resolver import ExperienceCatalogResolver


def _safe_str(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


def _get_min_price(pricing: Any) -> int | None:
    if pricing is None:
        return None
    tiers = getattr(pricing, "tiers", None) or []
    prices = [
        getattr(t, "price_per_person", None)
        for t in tiers
        if getattr(t, "price_per_person", None) is not None
    ]
    if not prices:
        return None
    return min(prices)


def _serialize_pricing(pricing: Any) -> dict[str, Any] | None:
    if pricing is None:
        return None
    tiers_out = []
    for tier in getattr(pricing, "tiers", None) or []:
        tiers_out.append(
            {
                "min_participants": getattr(tier, "min_participants", None),
                "max_participants": getattr(tier, "max_participants", None),
                "price_per_person": getattr(tier, "price_per_person", None),
            }
        )
    return {
        "currency": getattr(pricing, "currency", None) or "COP",
        "prices_are_net": getattr(pricing, "prices_are_net", True),
        "pricing_notes": getattr(pricing, "pricing_notes", None),
        "tiers": tiers_out,
    }


def _serialize_route(route: Any) -> dict[str, Any] | None:
    if route is None:
        return None
    return {
        "distance_km": getattr(route, "distance_km", None),
        "terrain": getattr(route, "terrain", None),
        "terrain_notes": getattr(route, "terrain_notes", None),
    }


def _doc_to_detail_item(experience: Any) -> ExperienceDetailItem:
    pricing = getattr(experience, "pricing", None)
    duration = getattr(experience, "duration", None)
    duration_text = (
        getattr(duration, "display_text", None)
        or _safe_str(getattr(experience, "duration_hours", None))
        or _safe_str(getattr(experience, "duration_days", None))
    )
    inclusions_data = getattr(experience, "inclusions", None)
    includes = list(getattr(inclusions_data, "items", None) or []) if inclusions_data else []
    inclusions_display = (
        getattr(inclusions_data, "display_text", None) if inclusions_data else None
    )
    subtitle = getattr(experience, "subtitle", None)
    description = getattr(experience, "description", None) or ""

    return ExperienceDetailItem(
        found=True,
        experience_id=_safe_str(getattr(experience, "id", None)),
        name=getattr(experience, "name", None),
        slug=getattr(experience, "slug", None),
        subtitle=subtitle,
        description=description or None,
        short_description=subtitle or (description[:120] if description else None),
        image_url=getattr(experience, "image_url", None),
        level=_safe_str(getattr(experience, "level", None)),
        difficulty=_safe_str(getattr(experience, "difficulty", None)),
        category=_safe_str(getattr(experience, "category", None)),
        status=_safe_str(getattr(experience, "status", None)),
        is_active=bool(getattr(experience, "is_active", True)),
        duration=duration_text or None,
        duration_hours=getattr(experience, "duration_hours", None),
        duration_days=getattr(experience, "duration_days", None),
        base_capacity=getattr(experience, "base_capacity", None),
        min_participants=getattr(experience, "min_participants", None),
        standard_max_participants=getattr(experience, "standard_max_participants", None),
        includes=includes,
        inclusions_display_text=inclusions_display,
        restrictions=[],
        starting_price=_get_min_price(pricing),
        currency=(getattr(pricing, "currency", None) if pricing else None) or "COP",
        pricing=_serialize_pricing(pricing),
        route_details=_serialize_route(getattr(experience, "route_details", None)),
        tags=list(getattr(experience, "tags", None) or []),
        aliases=list(getattr(experience, "aliases", None) or []),
    )


async def get_experience_detail(**kwargs: Any) -> dict[str, Any]:
    """Load the full active catalog, match mentioned experience(s), return full details.

    Does not build a WhatsApp template ``response``: the response composer narrates
    the structured fields so the reply stays conversational and in-session language.
    """
    trace_id = kwargs.get("trace_id", "")
    conversation_turn_id = kwargs.get("conversation_turn_id")
    started = time.perf_counter()

    experience_id = kwargs.get("experience_id")
    experience_query = kwargs.get("experience_query")

    resolver = ExperienceCatalogResolver()
    matched: list[Any] = []

    if experience_id:
        by_id = await ExperienceDocument.get(experience_id)
        if by_id is not None:
            matched = [by_id]

    if not matched and experience_query:
        matched = await resolver.resolve_many(str(experience_query))

    if not matched:
        output = ExperienceDetailOutput(
            found=False,
            trace_id=trace_id,
            experiences=[],
            response=None,
            blocking_reasons=[
                ToolBlockingReason(
                    code="experience.not_found",
                    message="No encontré la experiencia solicitada.",
                )
            ],
        )
        latency_ms = int((time.perf_counter() - started) * 1000)
        await ToolCallLogDocument(
            trace_id=trace_id,
            conversation_turn_id=conversation_turn_id,
            tool_name="get_experience_detail",
            input={"experience_id": experience_id, "experience_query": experience_query},
            output=output.model_dump(mode="json"),
            status="success",
            latency_ms=latency_ms,
        ).insert()
        return output.model_dump(mode="json")

    items = [_doc_to_detail_item(exp) for exp in matched]
    primary = items[0]

    output = ExperienceDetailOutput(
        found=True,
        trace_id=trace_id,
        experiences=items,
        response=None,
        experience_id=primary.experience_id,
        name=primary.name,
        slug=primary.slug,
        subtitle=primary.subtitle,
        description=primary.description,
        short_description=primary.short_description,
        image_url=primary.image_url,
        level=primary.level,
        difficulty=primary.difficulty,
        category=primary.category,
        status=primary.status,
        is_active=primary.is_active,
        duration=primary.duration,
        duration_hours=primary.duration_hours,
        duration_days=primary.duration_days,
        base_capacity=primary.base_capacity,
        min_participants=primary.min_participants,
        standard_max_participants=primary.standard_max_participants,
        includes=primary.includes,
        inclusions_display_text=primary.inclusions_display_text,
        restrictions=primary.restrictions,
        starting_price=primary.starting_price,
        currency=primary.currency,
        pricing=primary.pricing,
        route_details=primary.route_details,
        tags=primary.tags,
        aliases=primary.aliases,
        blocking_reasons=[],
    )

    latency_ms = int((time.perf_counter() - started) * 1000)
    await ToolCallLogDocument(
        trace_id=trace_id,
        conversation_turn_id=conversation_turn_id,
        tool_name="get_experience_detail",
        input={"experience_id": experience_id, "experience_query": experience_query},
        output=output.model_dump(mode="json"),
        status="success",
        latency_ms=latency_ms,
    ).insert()

    return output.model_dump(mode="json")
