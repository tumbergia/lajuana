from hashlib import sha256
from uuid import uuid4

import httpx

from app.core.config import settings
from app.core.logging import logger
from app.documents import PaymentProofDocument
from app.services.storage import get_storage_adapter

WHATSAPP_MEDIA_PREFIX = "whatsapp/"


def extract_media_id_from_storage_key(storage_key: str) -> str | None:
    if not storage_key.startswith(WHATSAPP_MEDIA_PREFIX):
        return None
    return storage_key.removeprefix(WHATSAPP_MEDIA_PREFIX)


def build_real_storage_key(media_id: str) -> str:
    unique_id = uuid4().hex
    return f"payment-proofs/{media_id}/{unique_id}"


async def download_and_store(proof_id: str) -> PaymentProofDocument | None:
    proof = await PaymentProofDocument.get(proof_id)
    if proof is None:
        logger.error("[whatsapp_media] Proof not found: %s", proof_id)
        return None

    if proof.size_bytes > 1:
        logger.debug("[whatsapp_media] Already downloaded: %s", proof_id)
        return proof

    media_id = extract_media_id_from_storage_key(proof.storage_key)
    if media_id is None:
        logger.warning("[whatsapp_media] Not a WhatsApp media key: %s", proof.storage_key)
        return None

    if not settings.whatsapp_access_token:
        logger.error("[whatsapp_media] No access token configured")
        return None

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            headers = {"Authorization": f"Bearer {settings.whatsapp_access_token}"}

            media_url = (
                f"https://graph.facebook.com/{settings.whatsapp_api_version}/{media_id}/"
            )
            media_resp = await client.get(media_url, headers=headers)
            media_resp.raise_for_status()
            media_info = media_resp.json()
            download_url = media_info.get("url")

            if not download_url:
                logger.error("[whatsapp_media] No download URL in media info for %s", media_id)
                return None

            file_resp = await client.get(download_url, headers=headers)
            file_resp.raise_for_status()
            file_bytes = file_resp.content

        real_storage_key = build_real_storage_key(media_id)

        adapter = get_storage_adapter()
        await adapter.write_bytes(real_storage_key, file_bytes)

        real_size = len(file_bytes)
        real_hash = sha256(file_bytes).hexdigest()

        proof.storage_key = real_storage_key
        proof.size_bytes = real_size
        proof.sha256 = real_hash
        await proof.save()

        logger.info(
            "[whatsapp_media] Stored %s | size=%d | key=%s",
            proof_id,
            real_size,
            real_storage_key,
        )
        return proof

    except httpx.HTTPStatusError as exc:
        logger.error(
            "[whatsapp_media] HTTP error for %s: %s - %s",
            media_id,
            exc.response.status_code,
            exc.response.text[:200],
        )
    except httpx.RequestError as exc:
        logger.error("[whatsapp_media] Request error for %s: %s", media_id, exc)
    except Exception as exc:
        logger.error("[whatsapp_media] Unexpected error for %s: %s", media_id, exc)

    return None


async def download_pending_media(limit: int = 10) -> list[str]:
    pending = await PaymentProofDocument.find(
        {
            "storage_key": {"$regex": f"^{WHATSAPP_MEDIA_PREFIX}"},
            "size_bytes": 1,
        }
    ).to_list()

    downloaded: list[str] = []
    for proof in pending[:limit]:
        result = await download_and_store(str(proof.id))
        if result is not None:
            downloaded.append(str(proof.id))

    return downloaded
