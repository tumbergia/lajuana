from __future__ import annotations

from typing import Any

from app.ai.mcp.tool_contracts import ExperienceSummaryItem, ListExperiencesOutput
from app.documents.experience_document import ExperienceDocument


def _safe_str(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


def _safe_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _get_min_price(pricing: Any) -> int | None:
    if pricing is None:
        return None
    tiers = getattr(pricing, "tiers", None)
    if not tiers:
        return None
    prices = [getattr(t, "price_per_person", None) for t in tiers if hasattr(t, "price_per_person")]
    if not prices:
        return None
    return min(p for p in prices if p is not None)


async def list_experiences(
    is_active: bool | None = True,
    limit: int = 20,
    trace_id: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    query = {}
    if is_active is not None:
        query["is_active"] = is_active

    experiences = await ExperienceDocument.find(query).to_list()
    experiences = experiences[:limit]

    result = []
    for exp in experiences:
        pricing = getattr(exp, "pricing", None)
        duration = getattr(exp, "duration", None)
        duration_text = (
            getattr(duration, "display_text", None)
            or _safe_str(getattr(exp, "duration_hours", None))
            or _safe_str(getattr(exp, "duration_days", None))
        )

        result.append(
            {
                "experience_id": _safe_str(exp.id),
                "name": exp.name,
                "slug": exp.slug,
                "short_description": getattr(exp, "subtitle", None)
                or (exp.description or "")[:120],  # noqa: E501
                "duration": duration_text,
                "difficulty": _safe_str(getattr(exp, "difficulty", None)),
                "level": _safe_str(getattr(exp, "level", None)),
                "starting_price": _get_min_price(pricing),
                "tags": getattr(exp, "tags", []) or [],
            }
        )

    return ListExperiencesOutput(
        trace_id=trace_id or "",
        experiences=[ExperienceSummaryItem(**e) for e in result],
        total=len(result),
    ).model_dump()
