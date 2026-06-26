from typing import Any, Literal

from pydantic import BaseModel, Field

from app.schemas.assistant_plan import AssistantAction


class AskRequest(BaseModel):
    message: str = Field(min_length=1)
    channel: Literal["test", "whatsapp", "admin_api", "mobile_api"] = "test"
    from_phone: str | None = None
    conversation_id: str | None = None
    trace_id: str | None = None
    conversation_turn_id: str | None = None


class OutboundDocumentRef(BaseModel):
    """Referencia a un documento que el canal debe enviar junto con la respuesta.

    El asistente no envía binarios; solo señala (con la clave del storage y los
    metadatos) qué archivo adjuntar. El canal correspondiente (p. ej. WhatsApp)
    lee el binario del storage y lo envía.
    """

    storage_key: str
    filename: str
    mime_type: str = "application/pdf"
    caption: str | None = None


class AskResponse(BaseModel):
    trace_id: str
    action: AssistantAction
    tool_name: str | None = None
    planner_output: dict[str, Any] = Field(default_factory=dict)
    tool_output: dict[str, Any] = Field(default_factory=dict)
    response: str
    document: OutboundDocumentRef | None = Field(
        default=None,
        description="Documento adjunto que el canal debe enviar junto con la respuesta.",
    )
    token_usage: dict[str, int] | None = Field(
        default=None,
        description="Tokens consumidos: prompt_tokens, completion_tokens, total_tokens",
    )
