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
    name: str | None = None
    full_name: str | None = None
    email: str | None = None
    password: str | None = None
    type: str | None = None
    description: str | None = None
    level: str | None = None
    duration_hours: int | None = None
    duration_days: int | None = None
    limit: int | None = None
    q: str | None = None
    provider_type: str | None = None
    event_type: str | None = None
    status: str | None = None
    notes: str | None = None
    reason: str | None = None
    enabled: bool | None = None
    is_active: bool | None = None
    # Gemini solo emite campos declarados aquí (el schema se envía sin
    # additionalProperties), así que todo parámetro de tool debe existir en ToolArgs.
    is_available: bool | None = None
    only_available: bool | None = None
    equine_ids: list[str] | None = None
    severity: str | None = None
    happened_at: str | None = None
    checkpoint_name: str | None = None
    related_participant_id: str | None = None
    related_equine_id: str | None = None
    min_days_in_advance: int | None = None
    require_payment_proof_for_confirmation: bool | None = None
    reservation_draft_ttl_minutes: int | None = None
    min_age: int | None = None
    max_age: int | None = None
    bold_requested: bool = False


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
