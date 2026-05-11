from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends
from langchain_core.messages import BaseMessage, HumanMessage

from app.agents import BeanieConversationCheckpointer, get_chat_graph, map_role_for_graph
from app.api.deps import get_current_user
from app.api.docs import ENDPOINT_DOCS, endpoint_description, endpoint_responses
from app.documents import UserDocument
from app.schemas.chat import ChatRequestSchema, ChatResponseSchema

router = APIRouter(prefix="/chat", tags=["Chat"])
checkpointer = BeanieConversationCheckpointer()
graph = get_chat_graph()


def _latest_ai_reply(messages: list[BaseMessage]) -> str:
    for message in reversed(messages):
        if message.type == "ai":
            return str(message.content)
    return "No tengo una respuesta disponible en este momento."


@router.post(
    "",
    response_model=ChatResponseSchema,
    summary=ENDPOINT_DOCS["chat_create"]["summary"],
    description=endpoint_description("chat_create"),
    operation_id="chatWithAgent",
    responses=endpoint_responses("chat_create"),
)
async def post_chat_message(
    payload: ChatRequestSchema,
    current_user: Annotated[UserDocument, Depends(get_current_user)],
) -> ChatResponseSchema:
    graph_role = map_role_for_graph(current_user.role)
    user_id = str(current_user.id)

    restored = await checkpointer.load(
        conversation_id=payload.conversation_id,
        user_id=user_id,
    )
    messages = list((restored or {}).get("messages", []))
    messages.append(HumanMessage(content=payload.message))

    initial_state = {
        "messages": messages,
        "role": graph_role,
        "user_id": user_id,
        "conversation_id": payload.conversation_id,
        "source": "chat",
        "whatsapp_phone": None,
        "user_message": payload.message,
        "intent": (restored or {}).get("intent"),
        "experience_id": (restored or {}).get("experience_id"),
        "experience_name": (restored or {}).get("experience_name"),
        "experience_options": (restored or {}).get("experience_options", []),
        "requested_date": (restored or {}).get("requested_date"),
        "people_count": (restored or {}).get("people_count"),
        "customer_name": (restored or {}).get("customer_name"),
        "customer_phone": (restored or {}).get("customer_phone"),
        "notes": (restored or {}).get("notes"),
        "next_question": (restored or {}).get("next_question"),
        "missing_fields": (restored or {}).get("missing_fields", []),
        "availability": (restored or {}).get("availability"),
        "suggested_dates": (restored or {}).get("suggested_dates", []),
        "reservation_id": (restored or {}).get("reservation_id"),
        "reservation_status": (restored or {}).get("reservation_status"),
        "reservation_summary": (restored or {}).get("reservation_summary"),
        "sync_knowledge_required": bool((restored or {}).get("sync_knowledge_required", False)),
        "reservation_knowledge_synced": bool((restored or {}).get("reservation_knowledge_synced", False)),
        "knowledge_context": (restored or {}).get("knowledge_context", []),
        "extracted_data": (restored or {}).get("extracted_data", {}),
        "rag_context": (restored or {}).get("rag_context", ""),
        "booking_intent": bool((restored or {}).get("booking_intent", False)),
        "errors": (restored or {}).get("errors", []),
    }

    result = await graph.ainvoke(initial_state)
    reply = _latest_ai_reply(result.get("messages", []))

    await checkpointer.save(
        conversation_id=payload.conversation_id,
        user_id=user_id,
        role=graph_role,
        state=result,
    )

    return ChatResponseSchema(
        conversation_id=payload.conversation_id,
        role=graph_role,
        reply=reply,
        booking_intent=bool(result.get("booking_intent", False)),
        rag_context=result.get("rag_context"),
        processed_at=datetime.now(UTC),
    )
