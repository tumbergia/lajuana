from datetime import UTC, datetime, timedelta

import bcrypt
import jwt

from app.common.constants import BCRYPT_ROUNDS
from app.core.config import settings


def hash_password(raw_password: str) -> str:
    salt = bcrypt.gensalt(rounds=BCRYPT_ROUNDS)
    return bcrypt.hashpw(raw_password.encode("utf-8"), salt).decode("utf-8")


def verify_password(raw_password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(raw_password.encode("utf-8"), password_hash.encode("utf-8"))


def _encode_token(subject: str, token_type: str, expires_delta: timedelta) -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": subject,
        "type": token_type,
        "iat": int(now.timestamp()),
        "exp": int((now + expires_delta).timestamp()),
    }
    return jwt.encode(payload, settings.auth_jwt_secret, algorithm=settings.auth_jwt_algorithm)


def create_access_token(subject: str) -> str:
    return _encode_token(
        subject=subject,
        token_type="access",
        expires_delta=timedelta(minutes=settings.auth_access_token_minutes),
    )


def create_refresh_token(subject: str) -> str:
    return _encode_token(
        subject=subject,
        token_type="refresh",
        expires_delta=timedelta(days=settings.auth_refresh_token_days),
    )


def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.auth_jwt_secret, algorithms=[settings.auth_jwt_algorithm])
