from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from google.genai import errors as genai_errors
from pydantic import BaseModel

from app.ai.providers.gemini_provider import GeminiModelUnavailable, GeminiProvider
from app.core.config import settings


class _DummyModel(BaseModel):
    answer: str


@pytest.fixture
def _patch_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "gemini_api_key", "key1")
    monkeypatch.setattr(settings, "gemini_api_key_2", "key2")
    monkeypatch.setattr(settings, "gemini_api_key_3", "")
    monkeypatch.setattr(settings, "gemini_model", "model-a")
    monkeypatch.setattr(settings, "gemini_fallback_models", "model-b")
    monkeypatch.setattr(settings, "gemini_timeout_seconds", 5)
    monkeypatch.setattr(settings, "gemini_temperature", 0.2)


@pytest.mark.asyncio
async def test_503_triggers_model_rotation_then_key_rotation(
    monkeypatch: pytest.MonkeyPatch, _patch_settings: None
) -> None:
    """A 503 error must rotate fallback models, then fallback keys, before giving up."""

    call_log: list[tuple[str, str]] = []

    def _fake_generate_content(*, model: str, contents: str, config: Any) -> Any:
        call_log.append((model, contents))
        # First 3 calls fail with 503 (model-a key1, model-b key1, model-a key2)
        if len(call_log) <= 3:
            raise genai_errors.ServerError(
                503,
                {"error": {"code": 503, "status": "UNAVAILABLE", "message": "high demand"}},
            )
        # 4th call succeeds
        response = MagicMock()
        response.text = '{"answer": "ok"}'
        response.usage_metadata = MagicMock()
        response.usage_metadata.prompt_token_count = 10
        response.usage_metadata.candidates_token_count = 5
        response.usage_metadata.total_token_count = 15
        return response

    with patch("app.ai.providers.gemini_provider.genai.Client") as mock_client_cls:
        instance = MagicMock()
        instance.models.generate_content = _fake_generate_content
        mock_client_cls.return_value = instance

        provider = GeminiProvider()
        result = await provider.generate_structured(
            system="sys",
            user="usr",
            response_model=_DummyModel,
        )

    assert result.answer == "ok"
    assert call_log == [
        ("model-a", "sys\n\nMensaje / contexto:\nusr"),
        ("model-b", "sys\n\nMensaje / contexto:\nusr"),
        ("model-a", "sys\n\nMensaje / contexto:\nusr"),
        ("model-b", "sys\n\nMensaje / contexto:\nusr"),
    ]


@pytest.mark.asyncio
async def test_503_exhausts_all_models_and_keys(
    monkeypatch: pytest.MonkeyPatch, _patch_settings: None
) -> None:
    """When every model/key returns 503, GeminiModelUnavailable must be raised."""

    def _fake_generate_content(*, model: str, contents: str, config: Any) -> Any:
        raise genai_errors.ServerError(
            503,
            {"error": {"code": 503, "status": "UNAVAILABLE", "message": "high demand"}},
        )

    with patch("app.ai.providers.gemini_provider.genai.Client") as mock_client_cls:
        instance = MagicMock()
        instance.models.generate_content = _fake_generate_content
        mock_client_cls.return_value = instance

        provider = GeminiProvider()
        with pytest.raises(GeminiModelUnavailable):
            await provider.generate_structured(
                system="sys",
                user="usr",
                response_model=_DummyModel,
            )
