import asyncio
from types import SimpleNamespace

import pytest

from app.common.labels import ErrorCode
from app.core.errors import ApiError
from app.core.security import hash_password, verify_password
from app.schemas.auth import UserLoginSchema
from app.services.auth_service import AuthService


def test_hash_and_verify_password() -> None:
    raw = "Secreta123"
    hashed = hash_password(raw)
    assert hashed != raw
    assert verify_password(raw, hashed) is True
    assert verify_password("otra", hashed) is False


def test_login_inactive_user(monkeypatch: pytest.MonkeyPatch) -> None:
    service = AuthService()
    inactive = SimpleNamespace(
        email="inactive@example.com",
        password_hash=hash_password("password123"),
        is_active=False,
    )

    async def fake_find_one(*_args, **_kwargs):
        return inactive

    monkeypatch.setattr("app.services.auth_service.UserDocument.find_one", fake_find_one)
    with pytest.raises(ApiError) as exc:
        asyncio.run(
            service.login(
                UserLoginSchema(
                    email="inactive@example.com",
                    password="password123",
                )
            )
        )
    assert exc.value.code == ErrorCode.AUTH_INACTIVE_USER
