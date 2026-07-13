from __future__ import annotations

from typing import Protocol, TypeVar

from pydantic import BaseModel

TModel = TypeVar("TModel", bound=BaseModel)


class LLMProviderError(RuntimeError):
    pass


class LLMResourceExhausted(LLMProviderError):
    pass


class LLMUnavailable(LLMProviderError):
    pass


class StructuredLLMProvider(Protocol):
    last_token_usage: dict[str, int] | None

    async def generate_structured(
        self,
        *,
        system: str,
        user: str,
        response_model: type[TModel],
        temperature: float | None = None,
        telemetry_context: dict | None = None,
    ) -> TModel: ...
