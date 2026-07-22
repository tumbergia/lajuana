from __future__ import annotations

from typing import Any

from app.ai.language.messages import t as _t
from app.ai.mcp.tool_contracts import ExperienceSummaryItem, ListExperiencesOutput
from app.documents.experience_document import ExperienceDocument


def _safe_str(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


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


def _build_list_response(items: list[dict[str, Any]], language: str) -> str:
    if not items:
        return _t("list_experiences_empty", language)
    lines = [_t("list_experiences_header", language)]
    for item in items:
        name = item.get("name") or ""
        price = item.get("starting_price")
        if price is not None:
            lines.append(
                _t(
                    "list_experiences_item",
                    language,
                    name=name,
                    price=f"{price:,.0f}",
                )
            )
        else:
            lines.append(_t("list_experiences_item_no_price", language, name=name))
    return "\n".join(lines) + _t("list_experiences_footer", language)


async def list_experiences(
    is_active: bool | None = True,
    limit: int = 20,
    trace_id: str | None = None,
    language: str = "es",
    **kwargs: Any,
) -> dict[str, Any]:
    language = kwargs.pop("language", language) or "es"
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
        response=_build_list_response(result, language),
    ).model_dump()
