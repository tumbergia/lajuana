from datetime import datetime

from beanie import Indexed
from pydantic import EmailStr

from app.common.collections import Collections
from app.common.enums import UserRole
from app.documents.base import AuditDocument


class UserDocument(AuditDocument):
    email: Indexed(EmailStr, unique=True)  # type: ignore[valid-type]
    password_hash: str
    full_name: str
    role: UserRole
    is_active: bool = True
    last_login_at: datetime | None = None
    refresh_token_hash: str | None = None

    class Settings:
        name = Collections.USERS
