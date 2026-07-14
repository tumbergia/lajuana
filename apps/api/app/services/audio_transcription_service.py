import asyncio

import httpx

from app.ai.providers.stt_provider import transcribe_audio
from app.core.config import settings
from app.core.logging import logger


async def download_and_transcribe(media_id: str) -> str:
    if not settings.whatsapp_access_token:
        raise RuntimeError("WhatsApp access token not configured")

    logger.info(
        "[transcription] Processing audio | media_id=%s",
        media_id,
    )

    async with httpx.AsyncClient(timeout=30) as client:
        headers = {"Authorization": f"Bearer {settings.whatsapp_access_token}"}

        media_url = (
            f"https://graph.facebook.com/{settings.whatsapp_api_version}/{media_id}/"
        )
        media_resp = await client.get(media_url, headers=headers)
        media_resp.raise_for_status()
        media_info = media_resp.json()

        download_url = media_info.get("url")
        mime_type = media_info.get("mime_type", "audio/ogg")

        if not download_url:
            raise RuntimeError(f"No download URL for media_id={media_id}")

        file_resp = await client.get(download_url, headers=headers)
        file_resp.raise_for_status()
        audio_bytes = file_resp.content

    logger.info(
        "[transcription] Downloaded %dB | mime=%s | media_id=%s",
        len(audio_bytes),
        mime_type,
        media_id,
    )

    text = await asyncio.to_thread(transcribe_audio, audio_bytes, mime_type)

    if not text.strip():
        logger.warning(
            "[transcription] Empty result | media_id=%s",
            media_id,
        )
        text = "[transcripción vacía]"

    logger.info(
        "[transcription] Result: %.200s | media_id=%s",
        text,
        media_id,
    )

    return text
