from __future__ import annotations

from typing import Any

from app.ai.mcp.tool_contracts import (
    ExperienceSummaryItem,
    ListExperiencesOutput,
    OutboundDocumentAttachment,
    SendExperiencesCatalogOutput,
    ToolBlockingReason,
)
from app.core.config import settings
from app.documents.experience_document import ExperienceDocument
from app.services.storage import get_storage_adapter


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


async def send_experiences_catalog(
    trace_id: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """Resuelve el documento PDF del catálogo de experiencias para enviarlo por chat.

    La tool no envía el archivo directamente (es agnóstica del canal): solo verifica
    que el PDF configurado exista en el storage y devuelve una referencia
    (``attachment``). El canal (p. ej. el worker de WhatsApp) se encarga del envío
    real del binario. Si el catálogo no está disponible, devuelve
    ``catalog_available=False`` para que el asistente ofrezca una alternativa.
    """
    if not settings.whatsapp_experiences_catalog_enabled:
        return SendExperiencesCatalogOutput(
            trace_id=trace_id or "",
            catalog_available=False,
            blocking_reasons=[
                ToolBlockingReason(
                    code="catalog_disabled",
                    message="El envío del catálogo en PDF está deshabilitado.",
                )
            ],
        ).model_dump()

    storage_key = settings.whatsapp_experiences_catalog_storage_key
    adapter = get_storage_adapter()
    if not await adapter.exists(storage_key):
        return SendExperiencesCatalogOutput(
            trace_id=trace_id or "",
            catalog_available=False,
            blocking_reasons=[
                ToolBlockingReason(
                    code="catalog_not_found",
                    message="El documento del catálogo no está disponible en el storage.",
                    details={"storage_key": storage_key},
                )
            ],
        ).model_dump()

    attachment = OutboundDocumentAttachment(
        storage_key=storage_key,
        filename=settings.whatsapp_experiences_catalog_filename,
        mime_type=settings.whatsapp_experiences_catalog_mime_type,
        caption=settings.whatsapp_experiences_catalog_caption,
    )
    return SendExperiencesCatalogOutput(
        trace_id=trace_id or "",
        catalog_available=True,
        attachment=attachment,
        response="Te comparto el catálogo de experiencias en PDF.",
    ).model_dump()
