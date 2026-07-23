from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.ai.providers.contracts import LLMProviderError
from app.ai.providers.factory import get_llm_provider


@pytest.mark.asyncio
async def test_provider_factory_does_not_fallback_to_env_when_db_disables_ai(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config_doc = SimpleNamespace(ai_configuration=SimpleNamespace(enabled=False))
    config_service = SimpleNamespace(
        get_ai_configuration_document=AsyncMock(return_value=config_doc)
    )

    monkeypatch.setattr("app.ai.providers.factory.ConfigService", lambda: config_service)
    monkeypatch.setattr(
        "app.ai.providers.factory.GeminiProvider",
        lambda: (_ for _ in ()).throw(AssertionError("env fallback used")),
    )
    monkeypatch.setattr("app.ai.providers.factory.settings.llm_provider", "gemini")
    monkeypatch.setattr("app.ai.providers.factory.settings.gemini_api_key", "test-key")

    with pytest.raises(LLMProviderError, match="No hay una configuración de IA activa"):
        await get_llm_provider()
