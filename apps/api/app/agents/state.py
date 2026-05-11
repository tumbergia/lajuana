from typing import Any, Literal

from langgraph.graph import MessagesState


class GraphState(MessagesState):
    role: Literal["admin", "guide", "unassigned"]
    user_id: str
    conversation_id: str
    source: str | None
    whatsapp_phone: str | None
    user_message: str | None
    intent: str | None
    experience_id: str | None
    experience_name: str | None
    experience_options: list[dict[str, Any]]
    requested_date: str | None
    people_count: int | None
    customer_name: str | None
    customer_phone: str | None
    notes: str | None
    next_question: str | None
    missing_fields: list[str]
    availability: dict[str, Any] | None
    suggested_dates: list[str]
    reservation_id: str | None
    reservation_status: str | None
    reservation_summary: str | None
    sync_knowledge_required: bool
    reservation_knowledge_synced: bool
    knowledge_context: list[dict[str, Any]]
    extracted_data: dict[str, Any]
    rag_context: str
    booking_intent: bool
    errors: list[str]
