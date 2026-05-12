import httpx

from app.core.config import settings


class WhatsAppSender:
    async def send_text(self, *, to_phone: str, text: str) -> bool:
        if not settings.whatsapp_send_enabled:
            return False

        if not settings.whatsapp_access_token or not settings.whatsapp_phone_number_id:
            return False

        url = (
            f"https://graph.facebook.com/{settings.whatsapp_api_version}/"
            f"{settings.whatsapp_phone_number_id}/messages"
        )

        payload = {
            "messaging_product": "whatsapp",
            "to": to_phone,
            "type": "text",
            "text": {"body": text},
        }

        headers = {
            "Authorization": f"Bearer {settings.whatsapp_access_token}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()

        return True
