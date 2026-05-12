from collections.abc import Awaitable, Callable
from typing import Any

ToolCallable = Callable[..., Awaitable[dict[str, Any]]]


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, ToolCallable] = {}

    def register(self, name: str, tool: ToolCallable) -> None:
        if name in self._tools:
            raise RuntimeError(f"Tool already registered: {name}")
        self._tools[name] = tool

    async def call(self, name: str, **kwargs: Any) -> dict[str, Any]:
        tool = self._tools.get(name)
        if tool is None:
            raise RuntimeError(f"Unknown tool: {name}")
        return await tool(**kwargs)

    def names(self) -> list[str]:
        return sorted(self._tools)


registry = ToolRegistry()
