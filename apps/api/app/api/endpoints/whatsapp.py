from typing import Any

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import PlainTextResponse

from app.ai.assistant.orchestrator import AssistantOrchestrator
from app.channels.whatsapp.normalizer import normalize_whatsapp_payload
from app.channels.whatsapp.sender import WhatsAppSender
from app.core.config import settings
from app.schemas.ask import AskRequest

router = APIRouter(prefix="/whatsapp", tags=["WhatsApp"])


@router.get("/webhook", response_class=PlainTextResponse)
async def verify_webhook(
    hub_mode: str | None = Query(default=None, alias="hub.mode"),
    hub_verify_token: str | None = Query(default=None, alias="hub.verify_token"),
    hub_challenge: str | None = Query(default=None, alias="hub.challenge"),
) -> str:
    if hub_mode == "subscribe" and hub_verify_token == settings.whatsapp_verify_token:
        return hub_challenge or ""

    raise HTTPException(status_code=403, detail="Invalid WhatsApp webhook verification token")


@router.post("/webhook")
async def receive_webhook(request: Request) -> dict[str, Any]:
    payload = await request.json()
    messages = normalize_whatsapp_payload(payload)

    orchestrator = AssistantOrchestrator()
    sender = WhatsAppSender()

    processed = 0

    for message in messages:
        result = await orchestrator.ask(
            AskRequest(
                message=message.text,
                channel="whatsapp",
                from_phone=message.from_phone,
                conversation_id=message.from_phone,
            )
        )

        if message.from_phone:
            await sender.send_text(
                to_phone=message.from_phone,
                text=result.response,
            )

        processed += 1

    return {"received": True, "processed_messages": processed}
