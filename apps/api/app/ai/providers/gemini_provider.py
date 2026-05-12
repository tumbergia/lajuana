from __future__ import annotations

import asyncio
from typing import Any, TypeVar

from google import genai
from pydantic import BaseModel

from app.core.config import settings

TModel = TypeVar("TModel", bound=BaseModel)


class GeminiProviderError(RuntimeError):
    pass


def _strip_additional_properties(schema: Any) -> Any:
    if isinstance(schema, dict):
        return {
            k: _strip_additional_properties(v)
            for k, v in schema.items()
            if k != "additionalProperties"
        }
    if isinstance(schema, list):
        return [_strip_additional_properties(item) for item in schema]
    return schema


class GeminiProvider:
    def __init__(self) -> None:
        if not settings.gemini_api_key:
            raise GeminiProviderError("GEMINI_API_KEY is not configured.")

        self._client = genai.Client(api_key=settings.gemini_api_key)
        self._model = settings.gemini_model

    async def generate_structured(
        self,
        *,
        system: str,
        user: str,
        response_model: type[TModel],
        temperature: float | None = None,
    ) -> TModel:
        prompt = f"{system.strip()}\n\nMensaje / contexto:\n{user.strip()}"
        schema = _strip_additional_properties(response_model.model_json_schema())

        def _call() -> TModel:
            response = self._client.models.generate_content(
                model=self._model,
                contents=prompt,
                config={
                    "temperature": (
                        settings.gemini_temperature if temperature is None else temperature
                    ),
                    "response_mime_type": "application/json",
                    "response_schema": schema,
                },
            )

            if not response.text:
                raise GeminiProviderError("Gemini returned an empty response.")

            return response_model.model_validate_json(response.text)

        try:
            return await asyncio.wait_for(
                asyncio.to_thread(_call),
                timeout=settings.gemini_timeout_seconds,
            )
        except TimeoutError as exc:
            raise GeminiProviderError("Gemini request timed out.") from exc
        except Exception as exc:
            raise GeminiProviderError(f"Gemini structured generation failed: {exc}") from exc
