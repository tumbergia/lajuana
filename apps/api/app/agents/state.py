from typing import Any, Literal

from langgraph.graph import MessagesState


class GraphState(MessagesState):
    role: Literal["admin", "guide", "customer"]
    user_id: str
    conversation_id: str
    extracted_data: dict[str, Any]
    rag_context: str
    booking_intent: bool
