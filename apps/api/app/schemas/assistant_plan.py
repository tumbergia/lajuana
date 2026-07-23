from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator


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


def _clip_str(value: object, max_length: int) -> object:
    """Recorta strings del LLM que exceden el schema (Gemini a veces se pasa)."""
    if not isinstance(value, str) or len(value) <= max_length:
        return value
    if max_length <= 1:
        return value[:max_length]
    return value[: max_length - 1].rstrip() + "…"


class ToolArgs(BaseModel):
    model_config = ConfigDict(extra="allow")

    experience_query: str | None = None
    experience_id: str | None = None
    user_id: str | None = None
    reservation_id: str | None = None
    participant_id: str | None = None
    payment_proof_id: str | None = None
    equine_id: str | None = None
    provider_id: str | None = None
    saddle_id: str | None = None
    assignment_id: str | None = None
    event_id: str | None = None
    schedule_id: str | None = None
    requested_date: str | None = None
    date_from: str | None = None
    date_to: str | None = None
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
    q: str | None = None
    provider_type: str | None = None
    event_type: str | None = None
    status: str | None = None
    notes: str | None = None
    reason: str | None = None
    enabled: bool | None = None
    is_active: bool | None = None
    bold_requested: bool = False
    query: str | None = None
    top_k: int | None = None


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

    @field_validator("user_goal", mode="before")
    @classmethod
    def _clip_user_goal(cls, value: object) -> object:
        return _clip_str(value, 300)

    @field_validator("response", mode="before")
    @classmethod
    def _clip_response(cls, value: object) -> object:
        return _clip_str(value, 1200)

    @field_validator("response_style", mode="before")
    @classmethod
    def _clip_response_style(cls, value: object) -> object:
        return _clip_str(value, 200)

    @field_validator("audit_summary", mode="before")
    @classmethod
    def _clip_audit_summary(cls, value: object) -> object:
        return _clip_str(value, 500)


class ToolResultResponse(BaseModel):
    response: str = Field(min_length=1, max_length=1200)
    audit_summary: str = Field(min_length=1, max_length=500)

    @field_validator("response", mode="before")
    @classmethod
    def _clip_response(cls, value: object) -> object:
        return _clip_str(value, 1200)

    @field_validator("audit_summary", mode="before")
    @classmethod
    def _clip_audit_summary(cls, value: object) -> object:
        return _clip_str(value, 500)
