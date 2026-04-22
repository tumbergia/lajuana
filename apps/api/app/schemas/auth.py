"""Schemas de autenticacion y gestion de usuarios."""

from pydantic import BaseModel, EmailStr, Field

from app.common.constants import TOKEN_TYPE_BEARER
from app.common.enums import UserRole

PASSWORD_MIN_LENGTH = 8


class RegisterRequest(BaseModel):
    """Contrato de registro publico. No permite asignar rol operativo."""

    email: EmailStr
    full_name: str = Field(min_length=3, max_length=120)
    password: str = Field(min_length=PASSWORD_MIN_LENGTH)


class UserCreateSchema(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=3, max_length=120)
    password: str = Field(min_length=PASSWORD_MIN_LENGTH)
    role: UserRole = UserRole.GUIDE


class UserUpdateSchema(BaseModel):
    full_name: str | None = Field(default=None, min_length=3, max_length=120)
    role: UserRole | None = None
    is_active: bool | None = None


class UserLoginSchema(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1)


class UserChangePasswordSchema(BaseModel):
    current_password: str = Field(min_length=1)
    new_password: str = Field(min_length=PASSWORD_MIN_LENGTH)


class UserResponseSchema(BaseModel):
    id: str
    email: EmailStr
    full_name: str
    role: UserRole
    is_active: bool


class TokenResponseSchema(BaseModel):
    access_token: str
    refresh_token: str | None = None
    token_type: str = TOKEN_TYPE_BEARER
    user: UserResponseSchema
