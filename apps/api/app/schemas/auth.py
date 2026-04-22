from pydantic import BaseModel, EmailStr, Field

from app.common.enums import UserRole


class UserCreateSchema(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str
    role: UserRole = UserRole.STAFF


class UserLoginSchema(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)


class UserChangePasswordSchema(BaseModel):
    current_password: str = Field(min_length=8)
    new_password: str = Field(min_length=8)


class UserResponseSchema(BaseModel):
    id: str
    email: EmailStr
    full_name: str
    role: UserRole
    is_active: bool


class TokenResponseSchema(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
