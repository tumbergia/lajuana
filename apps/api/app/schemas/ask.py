from typing import Any, Literal

from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    message: str = Field(min_length=1)
    channel: Literal["test", "whatsapp"] = "test"
    from_phone: str | None = None
    trace_id: str | None = None


class AskResponse(BaseModel):
    trace_id: str
    intent: str
    requires_tool: bool
    tool_name: str | None = None
    tool_input: dict[str, Any] = Field(default_factory=dict)
    tool_output: dict[str, Any] = Field(default_factory=dict)
    response: str
