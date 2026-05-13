from __future__ import annotations

import asyncio
from typing import Any, TypeVar

from google import genai
from google.genai import errors as genai_errors
from pydantic import BaseModel

from app.core.config import settings
from app.core.logging import logger

TModel = TypeVar("TModel", bound=BaseModel)


class GeminiProviderError(RuntimeError):
    pass


class GeminiResourceExhausted(GeminiProviderError):
    pass


class GeminiModelUnavailable(GeminiProviderError):
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
        keys = [settings.gemini_api_key, settings.gemini_api_key_2]
        keys = [k for k in keys if k]

        if not keys:
            raise GeminiProviderError(
                "No Gemini API keys configured. Set GEMINI_API_KEY or GEMINI_API_KEY_2."
            )

        self._clients = [genai.Client(api_key=k) for k in keys]
        self._model = settings.gemini_model
        self._current_index = 0

    @property
    def _current_client(self) -> genai.Client:
        return self._clients[self._current_index]

    def _rotate_key(self) -> bool:
        if self._current_index < len(self._clients) - 1:
            self._current_index += 1
            logger.warning(
                "Rotating to fallback Gemini API key (index %d)", self._current_index
            )
            return True
        return False

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
            try:
                response = self._current_client.models.generate_content(
                    model=self._model,
                    contents=prompt,
                    config={
                        "temperature": (
                            settings.gemini_temperature
                            if temperature is None
                            else temperature
                        ),
                        "response_mime_type": "application/json",
                        "response_schema": schema,
                    },
                )
            except genai_errors.ClientError as exc:
                if exc.code == 429:
                    if self._rotate_key():
                        return _call()
                    raise GeminiResourceExhausted(
                        "Todos los API keys de Gemini excedieron su cuota. "
                        "Espera unos minutos o configura una clave con más capacidad."
                    ) from exc

                if exc.code == 404:
                    raise GeminiModelUnavailable(
                        f"El modelo '{self._model}' no está disponible "
                        "con las API keys configuradas."
                    ) from exc

                if exc.code in (401, 403):
                    raise GeminiProviderError(
                        "API key de Gemini inválida o sin permisos."
                    ) from exc

                raise GeminiProviderError(
                    f"Gemini API error ({exc.code}): {exc}"
                ) from exc

            except Exception as exc:
                raise GeminiProviderError(
                    f"Gemini structured generation failed: {exc}"
                ) from exc

            if not response.text:
                raise GeminiProviderError("Gemini returned an empty response.")

            try:
                return response_model.model_validate_json(response.text)
            except Exception as exc:
                logger.warning(
                    "Gemini response validation failed: %s | text=%.200s",
                    exc, response.text,
                )
                raise GeminiProviderError(
                    f"Failed to parse Gemini response: {exc}"
                ) from exc

        try:
            return await asyncio.wait_for(
                asyncio.to_thread(_call),
                timeout=settings.gemini_timeout_seconds,
            )
        except TimeoutError as exc:
            raise GeminiProviderError("Gemini request timed out.") from exc
