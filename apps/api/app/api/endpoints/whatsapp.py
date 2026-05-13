from typing import Any
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import PlainTextResponse

from app.channels.whatsapp.ingestion_service import WhatsAppIngestionService
from app.core.config import settings
from app.core.logging import logger

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
    trace_id = str(uuid4())
    payload = await request.json()
    messages = normalize_whatsapp_payload(payload)

    logger.info(
        "whatsapp.webhook.received",
        extra={
            "trace_id": trace_id,
            "channel": "whatsapp",
            "endpoint": "/webhook",
            "entry_count": len(payload.get("entry", [])),
            "message_count": len(messages),
        },
    )

    orchestrator = AssistantOrchestrator()
    sender = WhatsAppSender()

    processed = 0

    for message in messages:
        logger.info(
            "whatsapp.message.normalized",
            extra={
                "trace_id": trace_id,
                "channel": "whatsapp",
                "from_phone": message.from_phone[-4:] if message.from_phone else "unknown",
            },
        )

        logger.info(
            "assistant.ask.start",
            extra={
                "trace_id": trace_id,
                "channel": "whatsapp",
                "conversation_id": message.from_phone,
            },
        )

        result = await orchestrator.ask(
            AskRequest(
                message=message.text,
                channel="whatsapp",
                from_phone=message.from_phone,
                conversation_id=message.from_phone,
                trace_id=trace_id,
            )
        )

        logger.info(
            "assistant.ask.completed",
            extra={
                "trace_id": trace_id,
                "channel": "whatsapp",
                "conversation_id": message.from_phone,
                "status": "success",
            },
        )

        if message.from_phone:
            await sender.send_text(
                to_phone=message.from_phone,
                text=result.response,
            )

        processed += 1

    logger.info(
        "whatsapp.webhook.processed",
        extra={
            "trace_id": trace_id,
            "channel": "whatsapp",
            "total_processed": processed,
        },
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
