from typing import Any

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import PlainTextResponse

from app.ai.assistant.orchestrator import AssistantOrchestrator
from app.channels.whatsapp.normalizer import normalize_whatsapp_payload
from app.channels.whatsapp.sender import WhatsAppSender
from app.core.config import settings
from app.core.logging import logger
from app.schemas.ask import AskRequest

router = APIRouter(prefix="/whatsapp", tags=["WhatsApp"])
bare_router = APIRouter(tags=["WhatsApp"])


async def _verify_webhook(
    hub_mode: str | None,
    hub_verify_token: str | None,
    hub_challenge: str | None,
) -> str:
    if hub_mode == "subscribe" and hub_verify_token == settings.whatsapp_verify_token:
        return hub_challenge or ""
    raise HTTPException(status_code=403, detail="Invalid WhatsApp webhook verification token")


async def _receive_webhook(request: Request) -> dict[str, Any]:
    payload = await request.json()
    messages = normalize_whatsapp_payload(payload)

    logger.info(
        "[webhook] WhatsApp webhook received | entry_count=%d | message_count=%d",
        len(payload.get("entry", [])),
        len(messages),
    )

    orchestrator = AssistantOrchestrator()
    sender = WhatsAppSender()

    processed = 0

    for message in messages:
        logger.info(
            "[webhook] Processing message | from=%s | text=%.120s",
            message.from_phone,
            message.text,
        )

        result = await orchestrator.ask(
            AskRequest(
                message=message.text,
                channel="whatsapp",
                from_phone=message.from_phone,
                conversation_id=message.from_phone,
            )
        )

        if message.from_phone:
            logger.info(
                "[webhook] Sending response | to=%s | response=%.200s",
                message.from_phone,
                result.response,
            )
            await sender.send_text(
                to_phone=message.from_phone,
                text=result.response,
            )

        processed += 1

    logger.info(
        "[webhook] Webhook processed | total_processed=%d",
        processed,
    )

    return {"received": True, "processed_messages": processed}


@router.get("/webhook", response_class=PlainTextResponse)
async def verify_webhook(
    hub_mode: str | None = Query(default=None, alias="hub.mode"),
    hub_verify_token: str | None = Query(default=None, alias="hub.verify_token"),
    hub_challenge: str | None = Query(default=None, alias="hub.challenge"),
) -> str:
    return await _verify_webhook(hub_mode, hub_verify_token, hub_challenge)


@router.post("/webhook")
async def receive_webhook(request: Request) -> dict[str, Any]:
    return await _receive_webhook(request)


@bare_router.get("/webhook", response_class=PlainTextResponse)
async def bare_verify_webhook(
    hub_mode: str | None = Query(default=None, alias="hub.mode"),
    hub_verify_token: str | None = Query(default=None, alias="hub.verify_token"),
    hub_challenge: str | None = Query(default=None, alias="hub.challenge"),
) -> str:
    return await _verify_webhook(hub_mode, hub_verify_token, hub_challenge)


@bare_router.post("/webhook")
async def bare_receive_webhook(request: Request) -> dict[str, Any]:
    return await _receive_webhook(request)
