"""Tests para la red de seguridad de traducción (Capa 2)."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from app.ai.assistant.translator import (
    _cache,
    cache_stats,
    clear_cache,
    localize_message,
    localize_tool_output,
)


@pytest.fixture(autouse=True)
def _reset_cache() -> None:
    """Limpia el cache antes de cada test."""
    clear_cache()
    yield
    clear_cache()


# ── localize_message ────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_localize_message_empty_returns_empty() -> None:
    assert await localize_message("", "en") == ""
    assert await localize_message("   ", "en") == "   "


@pytest.mark.asyncio
async def test_localize_message_spanish_target_returns_original() -> None:
    """Si el destino es 'es' (o no soportado), no traduce."""
    text = "Recibimos tu comprobante para la reserva PR-001."
    assert await localize_message(text, "es") == text
    assert await localize_message(text, "fr") == text  # no soportado
    assert await localize_message(text, "xx") == text


@pytest.mark.asyncio
async def test_localize_message_caches_translation() -> None:
    """La segunda llamada a localize_message con el mismo texto usa cache."""
    with patch(
        "app.ai.assistant.translator._translate_with_llm",
        AsyncMock(return_value="Translated text"),
    ) as mock_translate:
        first = await localize_message("Hola mundo", "en")
        second = await localize_message("Hola mundo", "en")
        assert first == "Translated text"
        assert second == "Translated text"
        # Solo se llama al LLM una vez gracias al cache.
        assert mock_translate.call_count == 1


@pytest.mark.asyncio
async def test_localize_message_returns_original_on_llm_failure() -> None:
    """Si el LLM falla, retorna el texto original (fail-safe)."""
    with patch(
        "app.ai.assistant.translator._translate_with_llm",
        AsyncMock(side_effect=RuntimeError("LLM down")),
    ):
        text = "Texto original en español"
        result = await localize_message(text, "en")
        assert result == text


@pytest.mark.asyncio
async def test_localize_message_caches_identical_translation() -> None:
    """Si la traducción es idéntica al original (ya estaba en destino),
    cachea para no re-intentar."""
    with patch(
        "app.ai.assistant.translator._translate_with_llm",
        AsyncMock(return_value="Already in English"),
    ) as mock_translate:
        await localize_message("Already in English", "en")
        await localize_message("Already in English", "en")
        assert mock_translate.call_count == 1


# ── localize_tool_output ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_localize_tool_output_spanish_returns_unchanged() -> None:
    """Si el target es 'es', no hace nada."""
    output = {
        "response": "Recibimos tu comprobante",
        "blocking_reasons": [{"code": "x", "message": "Error"}],
    }
    result = await localize_tool_output(output, "es")
    assert result == output


@pytest.mark.asyncio
async def test_localize_tool_output_localizes_response() -> None:
    """Localiza el campo `response` al target language."""
    with patch(
        "app.ai.assistant.translator._translate_with_llm",
        AsyncMock(return_value="We received your proof"),
    ):
        output = {"response": "Recibimos tu comprobante"}
        result = await localize_tool_output(output, "en")
        assert result["response"] == "We received your proof"


@pytest.mark.asyncio
async def test_localize_tool_output_localizes_blocking_reasons() -> None:
    """Localiza los `message` dentro de `blocking_reasons`."""
    with patch(
        "app.ai.assistant.translator._translate_with_llm",
        AsyncMock(side_effect=["Translated response", "Translated error 1", "Translated error 2"]),
    ):
        output = {
            "response": "Respuesta original",
            "blocking_reasons": [
                {"code": "x", "message": "Error 1"},
                {"code": "y", "message": "Error 2"},
            ],
        }
        result = await localize_tool_output(output, "en")
        assert result["response"] == "Translated response"
        assert result["blocking_reasons"][0]["message"] == "Translated error 1"
        assert result["blocking_reasons"][1]["message"] == "Translated error 2"
        # Los códigos NO se traducen.
        assert result["blocking_reasons"][0]["code"] == "x"
        assert result["blocking_reasons"][1]["code"] == "y"


@pytest.mark.asyncio
async def test_localize_tool_output_preserves_keys() -> None:
    """No debe perder ni renombrar keys."""
    with patch(
        "app.ai.assistant.translator._translate_with_llm",
        AsyncMock(return_value="translated"),
    ):
        output = {
            "response": "Hola",
            "reservation_code": "PR-001",
            "status": "pending",
            "blocking_reasons": [],
        }
        result = await localize_tool_output(output, "en")
        assert "response" in result
        assert "reservation_code" in result
        assert "status" in result
        assert "blocking_reasons" in result
        assert result["reservation_code"] == "PR-001"
        assert result["status"] == "pending"


@pytest.mark.asyncio
async def test_localize_tool_output_handles_empty_response() -> None:
    """Si no hay `response`, no falla."""
    output = {"reservation_code": "PR-001"}
    result = await localize_tool_output(output, "en")
    assert result == output


@pytest.mark.asyncio
async def test_localize_tool_output_handles_missing_blocking_reasons() -> None:
    output = {"response": "Hola"}
    result = await localize_tool_output(output, "en")
    assert "blocking_reasons" not in result


@pytest.mark.asyncio
async def test_localize_tool_output_skip_response_preserves_response() -> None:
    """Cuando `skip_response=True`, la `response` no se traduce (ya viene
    pre-localizada por la tool vía `t()`). Solo se traducen `blocking_reasons`.

    Esto preserva el formato (viñetas, alineación, secciones numeradas)
    que el LLM-based translation tiende a romper.
    """
    with patch(
        "app.ai.assistant.translator._translate_with_llm",
        AsyncMock(return_value="Translated text"),
    ):
        output = {
            "response": (
                "PASO 1. Hacer pago.\n"
                "Medios:\n"
                "1. CUENTA AHORROS BANCOLOMBIA\n"
                "   No. 7165 1544 758\n"
                "PASO 2. Enviar comprobante."
            ),
            "blocking_reasons": [{"code": "x", "message": "mensaje error"}],
        }
        result = await localize_tool_output(output, "en", skip_response=True)
        # Response preservado carácter por carácter
        assert result["response"] == output["response"]
        # Pero blocking_reasons SÍ se traducen
        assert result["blocking_reasons"][0]["message"] == "Translated text"


@pytest.mark.asyncio
async def test_localize_tool_output_translates_response_by_default() -> None:
    """Por defecto (skip_response=False), la `response` SI se traduce."""
    with patch(
        "app.ai.assistant.translator._translate_with_llm",
        AsyncMock(return_value="Translated response"),
    ):
        output = {"response": "Hola mundo"}
        result = await localize_tool_output(output, "en")
        assert result["response"] == "Translated response"


# ── Cache ──────────────────────────────────────────────────────────────


def test_cache_starts_empty() -> None:
    clear_cache()
    assert cache_stats() == {"size": 0, "max_size": 500}


@pytest.mark.asyncio
async def test_cache_grows_on_translation() -> None:
    with patch(
        "app.ai.assistant.translator._translate_with_llm",
        AsyncMock(return_value="translated"),
    ):
        await localize_message("text 1", "en")
        await localize_message("text 2", "en")
        assert cache_stats()["size"] == 2


@pytest.mark.asyncio
async def test_cache_lru_eviction() -> None:
    """El cache no debe crecer más allá del max_size."""
    from app.ai.assistant.translator import _TTLCache

    small_cache = _TTLCache(max_size=3)
    small_cache.set(("k1", "en"), "v1")
    small_cache.set(("k2", "en"), "v2")
    small_cache.set(("k3", "en"), "v3")
    small_cache.set(("k4", "en"), "v4")
    assert small_cache.stats()["size"] == 3
    # k1 debe haber sido evictado (LRU).
    assert small_cache.get(("k1", "en")) is None
    assert small_cache.get(("k4", "en")) == "v4"


def test_cache_clear() -> None:
    _cache.set(("test", "en"), "value")
    assert cache_stats()["size"] == 1
    clear_cache()
    assert cache_stats()["size"] == 0
