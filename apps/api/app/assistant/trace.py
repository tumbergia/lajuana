from typing import Any

from app.documents.conversation_turn_document import ConversationTurnDocument


async def create_inbound_turn(
    *,
    channel: str,
    message: str,
    from_phone: str | None = None,
    external_message_id: str | None = None,
    raw_payload: dict[str, Any] | None = None,
    trace_id: str | None = None,
) -> ConversationTurnDocument:
    kwargs: dict[str, Any] = dict(
        channel=channel,
        external_message_id=external_message_id,
        from_phone=from_phone,
        direction="inbound",
        raw_payload=raw_payload or {},
        normalized_text=message,
        status="received",
    )
    if trace_id:
        kwargs["trace_id"] = trace_id

    turn = ConversationTurnDocument(**kwargs)
    await turn.insert()
    return turn


async def complete_turn(
    turn: ConversationTurnDocument,
    *,
    detected_intent: str,
    response_text: str,
    status: str = "completed",
    error_code: str | None = None,
) -> ConversationTurnDocument:
    turn.detected_intent = detected_intent
    turn.response_text = response_text
    turn.status = status
    turn.error_code = error_code
    await turn.save()
    return turn
