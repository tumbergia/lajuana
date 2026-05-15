import time
from collections.abc import Awaitable, Callable
from typing import Any

from app.core.logging import logger

ToolCallable = Callable[..., Awaitable[dict[str, Any]]]


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, ToolCallable] = {}

    def register(self, name: str, tool: ToolCallable) -> None:
        if name in self._tools:
            raise RuntimeError(f"Tool already registered: {name}")
        self._tools[name] = tool

    async def call(
        self,
        name: str,
        conversation_id_for_log: str | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        tool = self._tools.get(name)
        if tool is None:
            raise RuntimeError(f"Unknown tool: {name}")

        logger.info(
            "[conversation_id=%s] Tool called | tool=%s",
            conversation_id_for_log,
            name,
        )

        started = time.perf_counter()
        result = await tool(**kwargs)
        elapsed_ms = int((time.perf_counter() - started) * 1000)

        logger.info(
            "[conversation_id=%s] Tool result | tool=%s | elapsed_ms=%d | available=%s",
            conversation_id_for_log,
            name,
            elapsed_ms,
            result.get("available") if isinstance(result, dict) else "N/A",
        )

        return result

    def names(self) -> list[str]:
        return sorted(self._tools)


registry = ToolRegistry()
