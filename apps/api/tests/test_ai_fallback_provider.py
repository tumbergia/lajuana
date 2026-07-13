from __future__ import annotations

import pytest
from pydantic import BaseModel

from app.ai.providers.contracts import LLMUnavailable
from app.ai.providers.fallback_provider import FallbackLLMProvider


class Result(BaseModel):
    value: str


class FakeProvider:
    def __init__(self, value: str | None) -> None:
        self.value = value
        self.calls = 0
        self.last_token_usage = None

    async def generate_structured(self, **kwargs):
        self.calls += 1
        if self.value is None:
            raise LLMUnavailable("down")
        return Result(value=self.value)


@pytest.mark.asyncio
async def test_fallback_uses_routes_in_order_once() -> None:
    first = FakeProvider(None)
    second = FakeProvider(None)
    third = FakeProvider("ok")
    provider = FallbackLLMProvider([("one", first), ("two", second), ("three", third)])
    result = await provider.generate_structured(system="s", user="u", response_model=Result)
    assert result.value == "ok"
    assert [first.calls, second.calls, third.calls] == [1, 1, 1]
