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
        "extracted_data": (restored or {}).get("extracted_data", {}),
        "rag_context": (restored or {}).get("rag_context", ""),
        "booking_intent": bool((restored or {}).get("booking_intent", False)),
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
