import hashlib
import hmac
import json
from typing import Annotated, Any
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field

from app.api.deps import (
    get_current_user,
    get_whatsapp_ingestion_service,
    get_whatsapp_outbound_service,
)
from app.channels.whatsapp.ingestion_service import WhatsAppIngestionService
from app.channels.whatsapp.normalizer import build_conversation_id, normalize_phone
from app.channels.whatsapp.outbound_service import WhatsAppOutboundService
from app.core.config import settings
from app.core.logging import logger
from app.documents import UserDocument
from app.documents.conversation_turn_document import ConversationTurnDocument

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
    raw_body = await request.body()
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


class SendWhatsAppRequest(BaseModel):
    to_phone: str = Field(..., description="Número de teléfono destino (ej. +573001234567)")
    message: str = Field(..., min_length=1, description="Texto del mensaje a enviar")


@router.post("/send", operation_id="sendWhatsAppMessage")
async def send_whatsapp_message(
    body: SendWhatsAppRequest,
    current_user: Annotated[UserDocument, Depends(get_current_user)],
    outbound_service: WhatsAppOutboundService = Depends(get_whatsapp_outbound_service),
) -> dict[str, Any]:
    """Envía un mensaje de WhatsApp directamente desde el panel de administración.

    Crea un turno de conversación outbound y lo envía a través del servicio
    de salida de WhatsApp (WhatsApp Cloud API). Requiere autenticación.
    """
    try:
        normalized = normalize_phone(body.to_phone)
    except ValueError:
        raise HTTPException(status_code=400, detail="Número de teléfono inválido.")

    conversation_id = build_conversation_id("whatsapp", normalized)

    turn = ConversationTurnDocument(
        trace_id=str(uuid4()),
        channel="whatsapp",
        to_phone=normalized,
        direction="outbound",
        user_message="(admin reply)",
        response_text=body.message,
        conversation_id=conversation_id,
        status="processing",
    )
    await turn.insert()

    result = await outbound_service.send(
        turn=turn,
        to_phone=normalized,
        text=body.message,
    )

    turn.status = "responded"
    turn.responded_at = result.sent_at
    await turn.save()

    if result.status == "failed":
        raise HTTPException(
            status_code=502,
            detail=f"Error al enviar mensaje: {result.error or 'desconocido'}",
        )

    return {
        "success": True,
        "outbound_id": result.outbound_id,
        "provider_message_id": result.provider_message_id,
    }
