from __future__ import annotations

from app.ai.providers.contracts import LLMProviderError, StructuredLLMProvider
from app.ai.providers.fallback_provider import FallbackLLMProvider
from app.ai.providers.gemini_provider import GeminiProvider
from app.ai.providers.openai_compatible_provider import OpenAICompatibleProvider
from app.core.config import settings
from app.core.secret_crypto import decrypt_secret
from app.services.config_service import ConfigService


async def get_llm_provider() -> StructuredLLMProvider:
    config = await ConfigService().get_ai_configuration_document()
    ai = config.ai_configuration if config else None
    if ai is not None:
        if not ai.enabled:
            raise LLMProviderError("No hay una configuración de IA activa.")

        mode = getattr(ai, "provider_mode", None) or "env"
        if mode == "env":
            if settings.llm_provider == "gemini" and settings.gemini_api_key:
                return GeminiProvider()
            raise LLMProviderError(
                "El modo recomendado está activo pero no hay GEMINI_API_KEY en el servidor."
            )

        routes = sorted(ai.routes, key=lambda item: item.position)
        providers: list[tuple[str, StructuredLLMProvider]] = []
        for route in routes:
            if not route.service or not route.model or not route.encrypted_api_key:
                continue
            api_key = decrypt_secret(route.encrypted_api_key)
            provider: StructuredLLMProvider
            if route.service == "gemini":
                provider = GeminiProvider(api_key=api_key, model=route.model)
            else:
                provider = OpenAICompatibleProvider(
                    service=route.service,
                    api_key=api_key,
                    model=route.model,
                    timeout_seconds=settings.gemini_timeout_seconds,
                )
            providers.append((f"{route.service}:{route.model}", provider))
        if not providers:
            raise LLMProviderError("La configuración activa de IA está incompleta.")
        return FallbackLLMProvider(providers)

    if settings.llm_provider == "gemini" and settings.gemini_api_key:
        return GeminiProvider()
    raise LLMProviderError("No hay una configuración de IA activa.")
