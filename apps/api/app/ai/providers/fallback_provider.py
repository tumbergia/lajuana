from __future__ import annotations

from typing import TypeVar

from pydantic import BaseModel

from app.ai.providers.contracts import (
    LLMProviderError,
    LLMResourceExhausted,
    LLMUnavailable,
    StructuredLLMProvider,
)
from app.core.logging import logger

TModel = TypeVar("TModel", bound=BaseModel)


class FallbackLLMProvider:
    def __init__(self, providers: list[tuple[str, StructuredLLMProvider]]) -> None:
        if len(providers) != 3:
            raise LLMProviderError("La configuración activa requiere exactamente tres rutas.")
        self._providers = providers
        self.last_token_usage: dict[str, int] | None = None

    async def generate_structured(
        self,
        *,
        system: str,
        user: str,
        response_model: type[TModel],
        temperature: float | None = None,
        telemetry_context: dict | None = None,
    ) -> TModel:
        last_error: LLMProviderError | None = None
        for index, (label, provider) in enumerate(self._providers, start=1):
            try:
                result = await provider.generate_structured(
                    system=system,
                    user=user,
                    response_model=response_model,
                    temperature=temperature,
                    telemetry_context=telemetry_context,
                )
                self.last_token_usage = provider.last_token_usage
                return result
            except (LLMResourceExhausted, LLMUnavailable, LLMProviderError) as exc:
                last_error = exc
                logger.warning("AI route %d/3 failed (%s): %s", index, label, type(exc).__name__)
        raise LLMUnavailable("Las tres rutas de IA configuradas fallaron.") from last_error
