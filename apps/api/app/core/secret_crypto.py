from __future__ import annotations

import base64
import hashlib
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.core.config import settings

_AAD = b"lajuana-ai-config-v1"


def _key() -> bytes:
    if not settings.ai_config_encryption_key:
        if settings.app_env == "local":
            return hashlib.sha256(settings.auth_jwt_secret.encode()).digest()
        raise RuntimeError("AI_CONFIG_ENCRYPTION_KEY is required to store AI credentials")
    try:
        key = base64.urlsafe_b64decode(settings.ai_config_encryption_key.encode())
    except Exception as exc:
        raise RuntimeError("AI_CONFIG_ENCRYPTION_KEY must be urlsafe base64") from exc
    if len(key) != 32:
        raise RuntimeError("AI_CONFIG_ENCRYPTION_KEY must decode to 32 bytes")
    return key


def encrypt_secret(value: str) -> str:
    nonce = os.urandom(12)
    ciphertext = AESGCM(_key()).encrypt(nonce, value.encode(), _AAD)
    return base64.urlsafe_b64encode(nonce + ciphertext).decode()


def decrypt_secret(value: str) -> str:
    raw = base64.urlsafe_b64decode(value.encode())
    return AESGCM(_key()).decrypt(raw[:12], raw[12:], _AAD).decode()
