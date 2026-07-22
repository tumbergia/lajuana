import hashlib
import hmac
import json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import PlainTextResponse

from app.api.deps import get_whatsapp_ingestion_service
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


async def _receive_webhook(
    request: Request,
    ingestion: WhatsAppIngestionService,
) -> dict[str, Any]:
    try:
        raw_body = await request.body()
    except Exception as exc:
        # Meta/ngrok a veces corta el body (ClientDisconnect); no tumbar el worker.
        from starlette.requests import ClientDisconnect

        if isinstance(exc, ClientDisconnect) or exc.__class__.__name__ == "ClientDisconnect":
            logger.warning("[webhook] ClientDisconnect reading body; ignoring")
            return {"received": True, "ingested_messages": 0, "disconnected": True}
        raise
    if settings.whatsapp_app_secret:
        supplied = request.headers.get("X-Hub-Signature-256", "")
        expected = (
            "sha256="
            + hmac.new(settings.whatsapp_app_secret.encode(), raw_body, hashlib.sha256).hexdigest()
        )
        if not hmac.compare_digest(supplied, expected):
            raise HTTPException(status_code=403, detail="Invalid WhatsApp webhook signature")
    payload = json.loads(raw_body)
    ingested = await ingestion.ingest(payload)
    logger.info("[webhook] Ingested %d message(s)", ingested)
    return {"received": True, "ingested_messages": ingested}


@router.get("/webhook", response_class=PlainTextResponse)
async def verify_webhook(
    hub_mode: str | None = Query(default=None, alias="hub.mode"),
    hub_verify_token: str | None = Query(default=None, alias="hub.verify_token"),
    hub_challenge: str | None = Query(default=None, alias="hub.challenge"),
) -> str:
    return await _verify_webhook(hub_mode, hub_verify_token, hub_challenge)


@router.post("/webhook")
async def receive_webhook(
    request: Request,
    ingestion: WhatsAppIngestionService = Depends(get_whatsapp_ingestion_service),
) -> dict[str, Any]:
    return await _receive_webhook(request, ingestion)


@bare_router.get("/webhook", response_class=PlainTextResponse)
async def bare_verify_webhook(
    hub_mode: str | None = Query(default=None, alias="hub.mode"),
    hub_verify_token: str | None = Query(default=None, alias="hub.verify_token"),
    hub_challenge: str | None = Query(default=None, alias="hub.challenge"),
) -> str:
    return await _verify_webhook(hub_mode, hub_verify_token, hub_challenge)


@bare_router.post("/webhook")
async def bare_receive_webhook(
    request: Request,
    ingestion: WhatsAppIngestionService = Depends(get_whatsapp_ingestion_service),
) -> dict[str, Any]:
    return await _receive_webhook(request, ingestion)
