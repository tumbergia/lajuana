from datetime import UTC, datetime

import httpx

from app.conversations.documents import OutboundMessageDocument
from app.core.config import settings
from app.core.logging import logger
from app.documents.conversation_turn_document import ConversationTurnDocument


class WhatsAppOutboundService:
    async def send(
        self,
        *,
        turn: ConversationTurnDocument,
        to_phone: str,
        text: str,
    ) -> OutboundMessageDocument:
        outbound = OutboundMessageDocument(
            conversation_id=turn.conversation_id or "",
            turn_id=str(turn.id),
            to_phone=to_phone,
            body=text,
            status="queued",
        )
        await outbound.insert()

        if not settings.whatsapp_send_enabled:
            return outbound

        if not settings.whatsapp_access_token or not settings.whatsapp_phone_number_id:
            outbound.status = "failed"
            outbound.error = "missing_credentials"
            await outbound.save()
            return outbound

        clean_phone = to_phone.lstrip("+")
        url = (
            f"https://graph.facebook.com/{settings.whatsapp_api_version}/"
            f"{settings.whatsapp_phone_number_id}/messages"
        )

        payload = {
            "messaging_product": "whatsapp",
            "to": clean_phone,
            "type": "text",
            "text": {"body": text},
        }

        headers = {
            "Authorization": f"Bearer {settings.whatsapp_access_token}",
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=15) as client:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                data = response.json()
                provider_id = (
                    (data.get("messages") or [{}])[0].get("id") if data.get("messages") else None
                )
                outbound.provider_message_id = provider_id
                outbound.status = "sent"
                outbound.sent_at = datetime.now(UTC)
                await outbound.save()
                logger.info(
                    "[outbound] Sent | to=%s | outbound_id=%s",
                    to_phone,
                    outbound.outbound_id,
                )
        except Exception as exc:
            outbound.status = "failed"
            outbound.error = str(exc)
            await outbound.save()
            logger.error("[outbound] Send failed | to=%s | error=%s", to_phone, exc)

        return outbound

    async def send_document(
        self,
        *,
        turn: ConversationTurnDocument,
        to_phone: str,
        content: bytes,
        filename: str,
        mime_type: str = "application/pdf",
        caption: str | None = None,
    ) -> OutboundMessageDocument:
        """Envía un documento (PDF u otro) por WhatsApp.

        El flujo de la Cloud API requiere dos pasos: primero subir el binario al
        endpoint ``/media`` para obtener un ``media_id``, y luego enviar el mensaje
        de tipo ``document`` referenciando ese id. Así no se depende de una URL
        pública del archivo (el storage puede ser local).
        """
        outbound = OutboundMessageDocument(
            conversation_id=turn.conversation_id or "",
            turn_id=str(turn.id),
            to_phone=to_phone,
            body=f"[documento] {filename}",
            status="queued",
        )
        await outbound.insert()

        if not settings.whatsapp_send_enabled:
            return outbound

        if not settings.whatsapp_access_token or not settings.whatsapp_phone_number_id:
            outbound.status = "failed"
            outbound.error = "missing_credentials"
            await outbound.save()
            return outbound

        clean_phone = to_phone.lstrip("+")
        base_url = (
            f"https://graph.facebook.com/{settings.whatsapp_api_version}/"
            f"{settings.whatsapp_phone_number_id}"
        )
        auth_headers = {"Authorization": f"Bearer {settings.whatsapp_access_token}"}

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                # Paso 1: subir el binario y obtener media_id.
                upload_resp = await client.post(
                    f"{base_url}/media",
                    headers=auth_headers,
                    data={"messaging_product": "whatsapp", "type": mime_type},
                    files={"file": (filename, content, mime_type)},
                )
                upload_resp.raise_for_status()
                media_id = upload_resp.json().get("id")
                if not media_id:
                    raise RuntimeError("media_upload_missing_id")

                # Paso 2: enviar el mensaje de documento referenciando el media_id.
                document: dict[str, str] = {"id": media_id, "filename": filename}
                if caption:
                    document["caption"] = caption
                message_resp = await client.post(
                    f"{base_url}/messages",
                    headers={**auth_headers, "Content-Type": "application/json"},
                    json={
                        "messaging_product": "whatsapp",
                        "to": clean_phone,
                        "type": "document",
                        "document": document,
                    },
                )
                message_resp.raise_for_status()
                data = message_resp.json()
                provider_id = (
                    (data.get("messages") or [{}])[0].get("id") if data.get("messages") else None
                )
                outbound.provider_message_id = provider_id
                outbound.status = "sent"
                outbound.sent_at = datetime.now(UTC)
                await outbound.save()
                logger.info(
                    "[outbound] Document sent | to=%s | outbound_id=%s | filename=%s",
                    to_phone,
                    outbound.outbound_id,
                    filename,
                )
        except Exception as exc:
            outbound.status = "failed"
            outbound.error = str(exc)
            await outbound.save()
            logger.error(
                "[outbound] Document send failed | to=%s | filename=%s | error=%s",
                to_phone,
                filename,
                exc,
            )

        return outbound
