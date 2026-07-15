"""Red de seguridad de traducción para mensajes pre-construidos.

Cuando un tool devuelve un `response` o `blocking_reasons[].message` en
español y la conversación está en otro idioma, esta capa lo traduce con
un LLM antes de enviar al usuario.

Estrategia:
- LRU cache en memoria para no traducir 2 veces el mismo mensaje.
- Si el texto ya está en el idioma destino → no traduce.
- Si la traducción falla → devuelve el texto original (fail-safe).
- Solo traduce si el idioma destino está en RESPONSE_LANGUAGES (es, en).
"""

from __future__ import annotations

import logging
import time
from collections import OrderedDict
from typing import Any

from app.ai.language.detector import RESPONSE_LANGUAGES

logger = logging.getLogger("lajuana.translator")

# Tamaño máximo del LRU cache.
_LRU_MAX_SIZE = 500

# TTL del cache: 1 hora. Los mensajes traducidos pueden cambiar si se
# actualizan los templates, así que no los cacheamos para siempre.
_CACHE_TTL_SECONDS = 3600


class _TTLCache:
    """LRU cache con TTL por entrada.

    Key: (text, target_language)
    Value: (translated_text, expires_at)
    """

    def __init__(self, max_size: int = _LRU_MAX_SIZE) -> None:
        self._max_size = max_size
        self._data: OrderedDict[tuple[str, str], tuple[str, float]] = OrderedDict()

    def get(self, key: tuple[str, str]) -> str | None:
        entry = self._data.get(key)
        if entry is None:
            return None
        value, expires_at = entry
        if time.monotonic() > expires_at:
            self._data.pop(key, None)
            return None
        # Mover al final (LRU).
        self._data.move_to_end(key)
        return value

    def set(self, key: tuple[str, str], value: str) -> None:
        # Si ya existe, actualizar y mover al final.
        if key in self._data:
            self._data.move_to_end(key)
        self._data[key] = (value, time.monotonic() + _CACHE_TTL_SECONDS)
        # Evict LRU si excedemos.
        while len(self._data) > self._max_size:
            self._data.popitem(last=False)

    def clear(self) -> None:
        self._data.clear()

    def stats(self) -> dict[str, int]:
        return {"size": len(self._data), "max_size": self._max_size}


_cache = _TTLCache()


def clear_cache() -> None:
    """Limpia el cache (útil para tests)."""
    _cache.clear()


def cache_stats() -> dict[str, int]:
    """Devuelve estadísticas del cache (útil para tests / observabilidad)."""
    return _cache.stats()


async def localize_message(text: str, target_language: str) -> str:
    """Traduce text al target_language si es necesario.

    Comportamiento:
    - Si text está vacío → retorna "".
    - Si target_language no está en RESPONSE_LANGUAGES → retorna texto original.
    - Si hay hit en cache → retorna la traducción cacheada.
    - Si el LLM falla → retorna texto original (nunca se rompe el flujo).
    - Si la traducción es idéntica al original → cachea y retorna el original
      (evita re-traducir).
    """
    if not text or not text.strip():
        return text
    if target_language not in RESPONSE_LANGUAGES:
        return text

    cache_key = (text, target_language)
    cached = _cache.get(cache_key)
    if cached is not None:
        return cached

    try:
        translated = await _translate_with_llm(text, target_language)
    except Exception as exc:
        logger.warning(
            "Translation failed for target=%s (len=%d): %s. Returning original.",
            target_language,
            len(text),
            exc,
        )
        return text

    if translated == text:
        # No se tradujo (ya estaba en el idioma destino). Cachear igual.
        _cache.set(cache_key, translated)
        return translated

    _cache.set(cache_key, translated)
    return translated


async def localize_tool_output(
    tool_output: dict[str, Any],
    target_language: str,
    *,
    skip_response: bool = False,
) -> dict[str, Any]:
    """Localiza los campos user-facing de un tool_output.

    - Localiza `response` si existe (salvo que `skip_response=True`).
    - Localiza `blocking_reasons[].message` si existen.
    - No toca códigos (`code`), ids, ni campos técnicos.
    - Si el target_language es 'es' (idioma por defecto) → no hace nada.

    `skip_response=True` se usa para tools que ya entregan su `response`
    pre-localizado vía `t()` (ver LITERAL_RESPONSE_TOOLS del orchestrator):
    re-pasar el texto por el LLM puede romper el formato (viñetas,
    alineación, secciones numeradas) y degradar la legibilidad.
    """
    if target_language not in RESPONSE_LANGUAGES or target_language == "es":
        return tool_output

    result = dict(tool_output)
    if result.get("response") and not skip_response:
        result["response"] = await localize_message(
            str(result["response"]), target_language
        )

    blocking = result.get("blocking_reasons")
    if isinstance(blocking, list):
        new_blocking = []
        for reason in blocking:
            if isinstance(reason, dict) and reason.get("message"):
                new_reason = dict(reason)
                new_reason["message"] = await localize_message(
                    str(reason["message"]), target_language
                )
                new_blocking.append(new_reason)
            else:
                new_blocking.append(reason)
        result["blocking_reasons"] = new_blocking

    return result


async def _translate_with_llm(text: str, target_language: str) -> str:
    """Llama al LLM para traducir.

    Usa el modelo más barato disponible (gemini-2.5-flash-lite) para
    minimizar costo y latencia. Temperature baja para traducciones estables.
    """
    from pydantic import BaseModel, Field

    from app.ai.providers.contracts import StructuredLLMProvider
    from app.ai.providers.factory import get_llm_provider

    class TranslationResult(BaseModel):
        translated: str = Field(..., description="Texto traducido al idioma destino")

    lang_name = {"es": "español", "en": "inglés"}.get(target_language, target_language)

    system_prompt = (
        "Eres un traductor profesional. Tu única tarea es traducir el texto "
        f"proporcionado al {lang_name}. "
        "Reglas estrictas:\n"
        "- NO cambies nombres propios (Bancolombia, La Juana, PR-XXXX, etc).\n"
        "- NO traduzcas códigos, IDs, ni campos técnicos.\n"
        "- NO agregues explicaciones ni notas.\n"
        "- NO cambies el significado ni el tono.\n"
        "- Mantén el formato (saltos de línea, bullets, etc).\n"
        "- Si el texto ya está en el idioma destino, devuélvelo tal cual.\n"
        "- Devuelve SOLO el texto traducido, sin comillas ni marcado JSON."
    )

    provider: StructuredLLMProvider = await get_llm_provider()
    result = await provider.generate_structured(
        system=system_prompt,
        user=text,
        response_model=TranslationResult,
        temperature=0.1,
        telemetry_context={"channel": "translation"},
    )
    return result.translated.strip()
