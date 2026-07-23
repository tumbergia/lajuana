"""Catálogo curado de modelos de IA destacados para el chatbot público.

Ordenado por costo combinado ascendente:
  combinado = 1M tokens entrada + 1M tokens salida

Inteligencia / velocidad: valoración comparativa para chatbots generales
con herramientas (no métrica oficial entre proveedores).

Los precios en vivo se fusionan en el servicio; aquí viven ratings,
recomendaciones, colores de marca e IDs (OpenRouter / LiteLLM).
"""

from __future__ import annotations

from typing import TypedDict


class CuratedModel(TypedDict):
    openrouter_model_id: str
    display_name: str
    provider: str
    intelligence: int  # 1-5
    speed: int  # 1-5
    recommended: bool
    value_note: str
    litellm_id: str | None
    buy_key_url: str
    # Fallback informativo (USD / 1M) si la fuente en vivo no responde.
    catalog_input_usd_per_million: str
    catalog_output_usd_per_million: str
    sort_order: int  # costo combinado ascendente


PROVIDER_BUY_URLS: dict[str, str] = {
    "openrouter": "https://openrouter.ai/keys",
    "google": "https://aistudio.google.com/apikey",
    "anthropic": "https://console.anthropic.com/settings/keys",
    "openai": "https://platform.openai.com/api-keys",
    "groq": "https://console.groq.com/keys",
}

# Colores de marca (hex) para badges / acentos en la app.
PROVIDER_BRAND_COLORS: dict[str, str] = {
    "groq": "#E85D04",
    "google": "#1A73E8",
    "anthropic": "#CC785C",
    "openai": "#0D9373",
    "openrouter": "#5B5B5B",
}


CURATED_MODELS: list[CuratedModel] = [
    # ── Groq ────────────────────────────────────────────────────────────
    {
        "openrouter_model_id": "meta-llama/llama-3.1-8b-instruct",
        "display_name": "Llama 3.1 8B — Groq",
        "provider": "groq",
        "intelligence": 2,
        "speed": 5,
        "recommended": True,
        "value_note": "Máxima economía · ultra rápido",
        "litellm_id": "groq/llama-3.1-8b-instant",
        "buy_key_url": PROVIDER_BUY_URLS["groq"],
        "catalog_input_usd_per_million": "0.05",
        "catalog_output_usd_per_million": "0.08",
        "sort_order": 1,
    },
    {
        "openrouter_model_id": "openai/gpt-oss-20b",
        "display_name": "GPT-OSS 20B — Groq",
        "provider": "groq",
        "intelligence": 3,
        "speed": 5,
        "recommended": False,
        "value_note": "Barato y muy rápido en Groq",
        "litellm_id": "groq/openai/gpt-oss-20b",
        "buy_key_url": PROVIDER_BUY_URLS["groq"],
        "catalog_input_usd_per_million": "0.075",
        "catalog_output_usd_per_million": "0.3",
        "sort_order": 2,
    },
    {
        "openrouter_model_id": "openai/gpt-oss-120b",
        "display_name": "GPT-OSS 120B — Groq",
        "provider": "groq",
        "intelligence": 4,
        "speed": 5,
        "recommended": False,
        "value_note": "Más capaz dentro de Groq; sigue barato",
        "litellm_id": "groq/openai/gpt-oss-120b",
        "buy_key_url": PROVIDER_BUY_URLS["groq"],
        "catalog_input_usd_per_million": "0.15",
        "catalog_output_usd_per_million": "0.6",
        "sort_order": 3,
    },
    {
        "openrouter_model_id": "meta-llama/llama-3.3-70b-instruct",
        "display_name": "Llama 3.3 70B — Groq",
        "provider": "groq",
        "intelligence": 3,
        "speed": 5,
        "recommended": False,
        "value_note": "Llama grande con latencia Groq",
        "litellm_id": "groq/llama-3.3-70b-versatile",
        "buy_key_url": PROVIDER_BUY_URLS["groq"],
        "catalog_input_usd_per_million": "0.59",
        "catalog_output_usd_per_million": "0.79",
        "sort_order": 4,
    },
    # ── Google ──────────────────────────────────────────────────────────
    {
        "openrouter_model_id": "google/gemini-3.1-flash-lite",
        "display_name": "Gemini 3.1 Flash-Lite",
        "provider": "google",
        "intelligence": 3,
        "speed": 5,
        "recommended": True,
        "value_note": "Mejor calidad/precio para chatbot público",
        "litellm_id": None,
        "buy_key_url": PROVIDER_BUY_URLS["google"],
        "catalog_input_usd_per_million": "0.25",
        "catalog_output_usd_per_million": "1.5",
        "sort_order": 5,
    },
    {
        "openrouter_model_id": "google/gemini-3.5-flash-lite",
        "display_name": "Gemini 3.5 Flash-Lite",
        "provider": "google",
        "intelligence": 3,
        "speed": 5,
        "recommended": False,
        "value_note": "Flash-Lite más reciente; sigue económico",
        "litellm_id": None,
        "buy_key_url": PROVIDER_BUY_URLS["google"],
        "catalog_input_usd_per_million": "0.3",
        "catalog_output_usd_per_million": "2.5",
        "sort_order": 6,
    },
    {
        "openrouter_model_id": "google/gemini-3.5-flash",
        "display_name": "Gemini 3.5 Flash",
        "provider": "google",
        "intelligence": 4,
        "speed": 4,
        "recommended": False,
        "value_note": "Más capaz que Lite; costo medio",
        "litellm_id": None,
        "buy_key_url": PROVIDER_BUY_URLS["google"],
        "catalog_input_usd_per_million": "1.5",
        "catalog_output_usd_per_million": "9",
        "sort_order": 9,
    },
    # ── Anthropic ───────────────────────────────────────────────────────
    {
        "openrouter_model_id": "anthropic/claude-haiku-4.5",
        "display_name": "Claude Haiku 4.5",
        "provider": "anthropic",
        "intelligence": 4,
        "speed": 5,
        "recommended": True,
        "value_note": "Velocidad y calidad altas · precio más elevado",
        "litellm_id": None,
        "buy_key_url": PROVIDER_BUY_URLS["anthropic"],
        "catalog_input_usd_per_million": "1",
        "catalog_output_usd_per_million": "5",
        "sort_order": 7,
    },
    {
        "openrouter_model_id": "anthropic/claude-sonnet-5",
        "display_name": "Claude Sonnet 5",
        "provider": "anthropic",
        "intelligence": 5,
        "speed": 4,
        "recommended": False,
        "value_note": "Excelente razonamiento; costo medio-alto",
        "litellm_id": None,
        "buy_key_url": PROVIDER_BUY_URLS["anthropic"],
        "catalog_input_usd_per_million": "2",
        "catalog_output_usd_per_million": "10",
        "sort_order": 10,
    },
    {
        "openrouter_model_id": "anthropic/claude-opus-4.8",
        "display_name": "Claude Opus 4.8",
        "provider": "anthropic",
        "intelligence": 5,
        "speed": 3,
        "recommended": False,
        "value_note": "Máxima inteligencia Anthropic; premium",
        "litellm_id": None,
        "buy_key_url": PROVIDER_BUY_URLS["anthropic"],
        "catalog_input_usd_per_million": "5",
        "catalog_output_usd_per_million": "25",
        "sort_order": 12,
    },
    # ── OpenAI ──────────────────────────────────────────────────────────
    {
        "openrouter_model_id": "openai/gpt-5.6-luna",
        "display_name": "GPT-5.6 Luna",
        "provider": "openai",
        "intelligence": 4,
        "speed": 4,
        "recommended": False,
        "value_note": "Buen equilibrio OpenAI en rango medio",
        "litellm_id": None,
        "buy_key_url": PROVIDER_BUY_URLS["openai"],
        "catalog_input_usd_per_million": "1",
        "catalog_output_usd_per_million": "6",
        "sort_order": 8,
    },
    {
        "openrouter_model_id": "openai/gpt-5.6-terra",
        "display_name": "GPT-5.6 Terra",
        "provider": "openai",
        "intelligence": 5,
        "speed": 4,
        "recommended": False,
        "value_note": "Alta inteligencia; costo alto",
        "litellm_id": None,
        "buy_key_url": PROVIDER_BUY_URLS["openai"],
        "catalog_input_usd_per_million": "2.5",
        "catalog_output_usd_per_million": "15",
        "sort_order": 11,
    },
    {
        "openrouter_model_id": "openai/gpt-5.6-sol",
        "display_name": "GPT-5.6 Sol",
        "provider": "openai",
        "intelligence": 5,
        "speed": 4,
        "recommended": False,
        "value_note": "Tope de gama OpenAI; el más costoso",
        "litellm_id": None,
        "buy_key_url": PROVIDER_BUY_URLS["openai"],
        "catalog_input_usd_per_million": "5",
        "catalog_output_usd_per_million": "30",
        "sort_order": 13,
    },
]
