import inspect
import time
from collections.abc import Awaitable, Callable
from typing import Any

from app.core.logging import logger

ToolCallable = Callable[..., Awaitable[dict[str, Any]]]

# El planner solo conoce los nombres de ToolArgs; algunas tools usan otro nombre para
# el mismo dato. Se renombra únicamente si la tool acepta el destino y no el origen.
_ARG_ALIASES: dict[str, str] = {"notes": "note"}


def _apply_arg_aliases(tool: ToolCallable, kwargs: dict[str, Any]) -> dict[str, Any]:
    params = inspect.signature(tool).parameters
    for source, target in _ARG_ALIASES.items():
        if source in kwargs and source not in params and target in params:
            kwargs.setdefault(target, kwargs.pop(source))
    return kwargs


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, ToolCallable] = {}

    def register(self, name: str, tool: ToolCallable) -> None:
        if name in self._tools:
            raise RuntimeError(f"Tool already registered: {name}")
        self._tools[name] = tool

    async def call(
        self,
        tool_name: str,
        /,
        conversation_id_for_log: str | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        # `tool_name` es posicional-only para que nunca colisione con un
        # argumento de tool legítimo llamado "name" (p.ej. admin_create_equine).
        tool = self._tools.get(tool_name)
        if tool is None:
            raise RuntimeError(f"Unknown tool: {tool_name}")

        logger.info(
            "[conversation_id=%s] Tool called | tool=%s",
            conversation_id_for_log,
            tool_name,
        )

        started = time.perf_counter()
        result = await tool(**_apply_arg_aliases(tool, kwargs))
        elapsed_ms = int((time.perf_counter() - started) * 1000)

        logger.info(
            "[conversation_id=%s] Tool result | tool=%s | elapsed_ms=%d | available=%s",
            conversation_id_for_log,
            tool_name,
            elapsed_ms,
            result.get("available") if isinstance(result, dict) else "N/A",
        )

        return result

    def get(self, tool_name: str) -> ToolCallable | None:
        return self._tools.get(tool_name)

    def names(self) -> list[str]:
        return sorted(self._tools)


registry = ToolRegistry()
