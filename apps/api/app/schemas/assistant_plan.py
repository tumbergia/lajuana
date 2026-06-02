from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class AssistantAction(StrEnum):
    FINAL_RESPONSE = "final_response"
    TOOL_CALL = "tool_call"
    ASK_CLARIFYING_QUESTION = "ask_clarifying_question"
    HUMAN_HANDOFF = "human_handoff"


class RiskLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ToolArgs(BaseModel):
    model_config = ConfigDict(extra="allow")

    experience_query: str | None = None
    experience_id: str | None = None
    schedule_id: str | None = None
    requested_date: str | None = None
    participant_count: int | None = None
    holder_phone: str | None = None
    holder_name: str | None = None
    holder_email: str | None = None
    code: str | None = None
    reservation_code: str | None = None
    new_date: str | None = None
    new_participant_count: int | None = None
    conversation_id: str | None = None
    quote_snapshot: dict | None = None
    exclude_dates: list[str] | None = None
    search_days_before: int | None = None
    search_days_after: int | None = None
    limit: int | None = None


class AssistantPlan(BaseModel):
    action: AssistantAction
    confidence: float = Field(ge=0.0, le=1.0)

    tool_name: str | None = None
    arguments: ToolArgs = Field(default_factory=ToolArgs)

    missing_fields: list[str] = Field(default_factory=list)
    risk_level: RiskLevel = RiskLevel.LOW
    needs_human: bool = False

    user_goal: str = Field(
        min_length=1,
        max_length=300,
        description="Resumen breve de lo que el usuario parece querer.",
    )

    response: str | None = Field(
        default=None,
        max_length=1200,
        description=(
            "Respuesta directa al usuario si no hace falta tool o si faltan datos. "
            "Debe ser natural, no robótica."
        ),
    )

    response_style: str = Field(
        default="breve, claro, conversacional y profesional para WhatsApp",
        max_length=200,
    )

    audit_summary: str = Field(
        min_length=1,
        max_length=500,
        description="Resumen auditable, sin chain-of-thought.",
    )


class ToolResultResponse(BaseModel):
    response: str = Field(min_length=1, max_length=1200)
    audit_summary: str = Field(min_length=1, max_length=500)
