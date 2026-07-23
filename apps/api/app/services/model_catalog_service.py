"""Catálogo de modelos de IA con precios en vivo (OpenRouter + LiteLLM).

Fusiona el catálogo curado con precios públicos. Los precios son informativos,
no una fuente definitiva de facturación.
"""

from __future__ import annotations

import asyncio
import time
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

import httpx

from app.config.model_catalog import (
    CURATED_MODELS,
    PROVIDER_BRAND_COLORS,
    PROVIDER_BUY_URLS,
    CuratedModel,
)
from app.core.logging import logger
from app.schemas.config import AiModelCatalogSchema, AiModelItemSchema

OPENROUTER_MODELS_URL = "https://openrouter.ai/api/v1/models"
LITELLM_COST_MAP_URL = (
    "https://raw.githubusercontent.com/BerriAI/litellm/"
    "main/model_prices_and_context_window.json"
)

CACHE_TTL_SECONDS = 6 * 60 * 60


class _PriceEntry:
    __slots__ = (
        "input_usd_per_million",
        "output_usd_per_million",
        "cached_input_usd_per_million",
        "context_length",
        "source",
    )

    def __init__(
        self,
        *,
        input_usd_per_million: str | None,
        output_usd_per_million: str | None,
        cached_input_usd_per_million: str | None,
        context_length: int | None,
        source: str,
    ) -> None:
        self.input_usd_per_million = input_usd_per_million
        self.output_usd_per_million = output_usd_per_million
        self.cached_input_usd_per_million = cached_input_usd_per_million
        self.context_length = context_length
        self.source = source


class _PriceCache:
    def __init__(self) -> None:
        self.by_id: dict[str, _PriceEntry] = {}
        self.fetched_at: datetime | None = None
        self.expires_at_monotonic: float = 0
        self.warnings: list[str] = []
        self.lock = asyncio.Lock()


_cache = _PriceCache()


def _per_million(value: Any) -> str | None:
    """Convierte precio por token a USD por millón de tokens (como string Decimal)."""
    if value is None or value == "":
        return None
    try:
        result = Decimal(str(value)) * Decimal("1000000")
    except (InvalidOperation, ValueError, TypeError):
        return None
    # Quita ceros innecesarios pero mantiene precisión.
    normalized = format(result.normalize(), "f")
    if "." in normalized:
        normalized = normalized.rstrip("0").rstrip(".")
    return normalized or "0"


def _normalize_openrouter(payload: dict[str, Any]) -> dict[str, _PriceEntry]:
    result: dict[str, _PriceEntry] = {}
    for model in payload.get("data", []):
        if not isinstance(model, dict):
            continue
        model_id = str(model.get("id", "")).strip()
        if not model_id:
            continue
        pricing = model.get("pricing") or {}
        if not isinstance(pricing, dict):
            pricing = {}
        context = model.get("context_length")
        context_length = int(context) if isinstance(context, (int, float)) else None
        result[model_id] = _PriceEntry(
            input_usd_per_million=_per_million(pricing.get("prompt")),
            output_usd_per_million=_per_million(pricing.get("completion")),
            cached_input_usd_per_million=_per_million(pricing.get("input_cache_read")),
            context_length=context_length,
            source="openrouter",
        )
    return result


def _normalize_litellm_groq(payload: dict[str, Any]) -> dict[str, _PriceEntry]:
    result: dict[str, _PriceEntry] = {}
    for model_id, model in payload.items():
        if not isinstance(model, dict):
            continue
        is_groq = model_id.startswith("groq/") or model.get("litellm_provider") == "groq"
        if not is_groq:
            continue
        mode = model.get("mode")
        if mode not in {None, "chat", "completion"}:
            continue
        input_price = _per_million(model.get("input_cost_per_token"))
        output_price = _per_million(model.get("output_cost_per_token"))
        if input_price is None and output_price is None:
            continue
        context = model.get("max_input_tokens") or model.get("max_tokens")
        context_length = int(context) if isinstance(context, (int, float)) else None
        result[model_id] = _PriceEntry(
            input_usd_per_million=input_price,
            output_usd_per_million=output_price,
            cached_input_usd_per_million=_per_million(
                model.get("cache_read_input_token_cost")
            ),
            context_length=context_length,
            source="litellm",
        )
    return result


async def _fetch_openrouter(client: httpx.AsyncClient) -> dict[str, _PriceEntry]:
    response = await client.get(
        OPENROUTER_MODELS_URL,
        params={"output_modalities": "text"},
    )
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, dict):
        raise ValueError("OpenRouter devolvió una respuesta inesperada.")
    return _normalize_openrouter(payload)


async def _fetch_litellm_groq(client: httpx.AsyncClient) -> dict[str, _PriceEntry]:
    response = await client.get(LITELLM_COST_MAP_URL)
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, dict):
        raise ValueError("LiteLLM devolvió una respuesta inesperada.")
    return _normalize_litellm_groq(payload)


async def _load_live_prices() -> tuple[dict[str, _PriceEntry], datetime | None, bool, list[str]]:
    now_monotonic = time.monotonic()
    if (
        _cache.by_id
        and now_monotonic < _cache.expires_at_monotonic
        and _cache.fetched_at is not None
    ):
        return _cache.by_id, _cache.fetched_at, False, list(_cache.warnings)

    async with _cache.lock:
        now_monotonic = time.monotonic()
        if (
            _cache.by_id
            and now_monotonic < _cache.expires_at_monotonic
            and _cache.fetched_at is not None
        ):
            return _cache.by_id, _cache.fetched_at, False, list(_cache.warnings)

        timeout = httpx.Timeout(timeout=15.0, connect=5.0)
        async with httpx.AsyncClient(
            timeout=timeout,
            follow_redirects=True,
            headers={
                "Accept": "application/json",
                "User-Agent": "la-juana-api/model-catalog",
            },
        ) as client:
            results = await asyncio.gather(
                _fetch_openrouter(client),
                _fetch_litellm_groq(client),
                return_exceptions=True,
            )

        warnings: list[str] = []
        combined: dict[str, _PriceEntry] = {}
        source_names = ["OpenRouter", "LiteLLM"]

        for source_name, result in zip(source_names, results, strict=True):
            if isinstance(result, BaseException):
                logger.warning(
                    "[model_catalog] Failed to refresh %s: %s",
                    source_name,
                    type(result).__name__,
                )
                warnings.append(
                    f"No se pudo actualizar {source_name}: {type(result).__name__}"
                )
                continue
            combined.update(result)

        if not combined:
            if _cache.by_id and _cache.fetched_at is not None:
                warnings.append("Se están devolviendo datos vencidos de la caché.")
                return _cache.by_id, _cache.fetched_at, True, warnings
            return {}, None, False, warnings

        _cache.by_id = combined
        _cache.fetched_at = datetime.now(UTC)
        _cache.expires_at_monotonic = time.monotonic() + CACHE_TTL_SECONDS
        _cache.warnings = warnings
        return _cache.by_id, _cache.fetched_at, False, warnings


def _lookup_price(
    curated: CuratedModel,
    live: dict[str, _PriceEntry],
) -> _PriceEntry | None:
    openrouter_id = curated["openrouter_model_id"]
    if openrouter_id in live:
        return live[openrouter_id]
    litellm_id = curated.get("litellm_id")
    if litellm_id and litellm_id in live:
        return live[litellm_id]
    # Variantes frecuentes: sin prefijo groq/ o con prefijo distinto.
    bare = openrouter_id.removeprefix("groq/")
    for key, entry in live.items():
        if key == bare or key.endswith(f"/{bare}") or key.removeprefix("groq/") == bare:
            return entry
    return None


def _combined_usd(
    input_usd: str | None,
    output_usd: str | None,
) -> str | None:
    if input_usd is None and output_usd is None:
        return None
    try:
        total = Decimal(input_usd or "0") + Decimal(output_usd or "0")
    except (InvalidOperation, ValueError, TypeError):
        return None
    normalized = format(total.normalize(), "f")
    if "." in normalized:
        normalized = normalized.rstrip("0").rstrip(".")
    return normalized or "0"


class ModelCatalogService:
    async def get_catalog(self) -> AiModelCatalogSchema:
        live, fetched_at, stale, warnings = await _load_live_prices()
        response_warnings = list(warnings)
        response_warnings.append(
            "Estos precios son informativos y pueden diferir de los reales. "
            "Valídalos siempre contra el proveedor antes de facturar o presupuestar."
        )

        items: list[AiModelItemSchema] = []
        for curated in CURATED_MODELS:
            price = _lookup_price(curated, live)
            if price is not None:
                input_usd = price.input_usd_per_million
                output_usd = price.output_usd_per_million
                cached_usd = price.cached_input_usd_per_million
                context_length = price.context_length
                source: str = price.source
                # Si la fuente viva no trae precio, cae al catálogo curado.
                if input_usd is None:
                    input_usd = curated["catalog_input_usd_per_million"]
                if output_usd is None:
                    output_usd = curated["catalog_output_usd_per_million"]
            else:
                input_usd = curated["catalog_input_usd_per_million"]
                output_usd = curated["catalog_output_usd_per_million"]
                cached_usd = None
                context_length = None
                source = "catalog"

            items.append(
                AiModelItemSchema(
                    provider=curated["provider"],
                    model_id=curated["openrouter_model_id"],
                    display_name=curated["display_name"],
                    intelligence=curated["intelligence"],
                    speed=curated["speed"],
                    recommended=curated["recommended"],
                    value_note=curated["value_note"],
                    brand_color=PROVIDER_BRAND_COLORS.get(
                        curated["provider"], "#5B5B5B"
                    ),
                    input_usd_per_million=input_usd,
                    output_usd_per_million=output_usd,
                    cached_input_usd_per_million=cached_usd,
                    combined_usd_per_million=_combined_usd(input_usd, output_usd),
                    context_length=context_length,
                    buy_key_url=curated["buy_key_url"],
                    source=source,  # type: ignore[arg-type]
                    sort_order=curated["sort_order"],
                )
            )

        # Precio combinado ascendente (tabla de referencia).
        items.sort(key=lambda item: (item.sort_order, item.display_name.casefold()))

        return AiModelCatalogSchema(
            fetched_at=fetched_at,
            stale=stale,
            warnings=response_warnings,
            items=items,
            provider_buy_urls=dict(PROVIDER_BUY_URLS),
            provider_brand_colors=dict(PROVIDER_BRAND_COLORS),
        )

