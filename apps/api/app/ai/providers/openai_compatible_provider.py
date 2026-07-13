from __future__ import annotations

from typing import TypeVar

import httpx
from pydantic import BaseModel

from app.ai.providers.contracts import LLMProviderError, LLMResourceExhausted, LLMUnavailable

TModel = TypeVar("TModel", bound=BaseModel)

BASE_URLS = {
    "openai": "https://api.openai.com/v1",
    "groq": "https://api.groq.com/openai/v1",
    "openrouter": "https://openrouter.ai/api/v1",
}


class OpenAICompatibleProvider:
    def __init__(
        self, *, service: str, api_key: str, model: str, timeout_seconds: int = 60
    ) -> None:
        if service not in BASE_URLS:
            raise LLMProviderError(f"Servicio OpenAI-compatible no soportado: {service}")
        self._service = service
        self._api_key = api_key
        self._model = model
        self._timeout = timeout_seconds
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
        schema = response_model.model_json_schema()
        payload = {
            "model": self._model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        f"{system}\nResponde únicamente JSON válido para este esquema: {schema}"
                    ),
                },
                {"role": "user", "content": user},
            ],
            "temperature": 0.2 if temperature is None else temperature,
            "response_format": {"type": "json_object"},
        }
        try:
            async with httpx.AsyncClient(timeout=self._timeout, follow_redirects=False) as client:
                response = await client.post(
                    f"{BASE_URLS[self._service]}/chat/completions",
                    headers={"Authorization": f"Bearer {self._api_key}"},
                    json=payload,
                )
        except httpx.TimeoutException as exc:
            raise LLMUnavailable(f"{self._service} agotó el tiempo de espera") from exc
        except httpx.HTTPError as exc:
            raise LLMUnavailable(f"No se pudo conectar con {self._service}") from exc
        if response.status_code == 429:
            raise LLMResourceExhausted(f"{self._service} excedió su cuota")
        if response.status_code in {401, 403}:
            raise LLMProviderError(f"La clave de {self._service} es inválida")
        if response.status_code >= 500:
            raise LLMUnavailable(f"{self._service} no está disponible")
        if response.status_code >= 400:
            raise LLMProviderError(f"{self._service} rechazó la solicitud ({response.status_code})")
        try:
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            usage = data.get("usage") or {}
            self.last_token_usage = {
                "prompt_tokens": int(usage.get("prompt_tokens") or 0),
                "completion_tokens": int(usage.get("completion_tokens") or 0),
                "total_tokens": int(usage.get("total_tokens") or 0),
            }
            return response_model.model_validate_json(content)
        except Exception as exc:
            raise LLMProviderError(f"Respuesta inválida de {self._service}") from exc
