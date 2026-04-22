from datetime import UTC, datetime

from app.common.enums import UserRole
from app.common.labels import ErrorCode
from app.core.errors import ApiError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.documents import UserDocument
from app.schemas.auth import (
    TokenResponseSchema,
    UserChangePasswordSchema,
    UserCreateSchema,
    UserLoginSchema,
)


class AuthService:
    async def register(self, payload: UserCreateSchema) -> UserDocument:
        existing = await UserDocument.find_one(UserDocument.email == payload.email)
        if existing is not None:
            raise ApiError(
                status_code=409,
                code="auth.email_already_exists",
                message="Ya existe un usuario con este correo.",
            )

        user = UserDocument(
            email=payload.email,
            password_hash=hash_password(payload.password),
            full_name=payload.full_name,
            role=payload.role or UserRole.STAFF,
            is_active=True,
        )
        await user.insert()
        return user

    async def login(self, payload: UserLoginSchema) -> tuple[UserDocument, TokenResponseSchema]:
        user = await UserDocument.find_one(UserDocument.email == payload.email)
        if user is None or not verify_password(payload.password, user.password_hash):
            raise ApiError(
                status_code=401,
                code=ErrorCode.AUTH_INVALID_CREDENTIALS,
                message="Credenciales inválidas.",
            )
        if not user.is_active:
            raise ApiError(
                status_code=403,
                code=ErrorCode.AUTH_FORBIDDEN,
                message="El usuario está inactivo.",
            )

        access_token = create_access_token(str(user.id))
        refresh_token = create_refresh_token(str(user.id))
        user.last_login_at = datetime.now(UTC)
        user.refresh_token_hash = hash_password(refresh_token)
        await user.save()
        return user, TokenResponseSchema(access_token=access_token, refresh_token=refresh_token)

    async def refresh(self, refresh_token: str) -> TokenResponseSchema:
        payload = decode_token(refresh_token)
        if payload.get("type") != "refresh":
            raise ApiError(
                status_code=401,
                code=ErrorCode.AUTH_INVALID_CREDENTIALS,
                message="Token de refresco inválido.",
            )
        user = await UserDocument.get(payload.get("sub"))
        if user is None or user.refresh_token_hash is None:
            raise ApiError(
                status_code=401,
                code=ErrorCode.AUTH_INVALID_CREDENTIALS,
                message="Token de refresco inválido.",
            )
        if not verify_password(refresh_token, user.refresh_token_hash):
            raise ApiError(
                status_code=401,
                code=ErrorCode.AUTH_INVALID_CREDENTIALS,
                message="Token de refresco inválido.",
            )

        new_access = create_access_token(str(user.id))
        new_refresh = create_refresh_token(str(user.id))
        user.refresh_token_hash = hash_password(new_refresh)
        await user.save()
        return TokenResponseSchema(access_token=new_access, refresh_token=new_refresh)

    async def logout(self, user_id: str) -> None:
        user = await UserDocument.get(user_id)
        if user is None:
            return
        user.refresh_token_hash = None
        await user.save()

    async def change_password(self, user_id: str, payload: UserChangePasswordSchema) -> None:
        user = await UserDocument.get(user_id)
        if user is None:
            raise ApiError(
                status_code=404,
                code="auth.user_not_found",
                message="Usuario no encontrado.",
            )
        if not verify_password(payload.current_password, user.password_hash):
            raise ApiError(
                status_code=401,
                code=ErrorCode.AUTH_INVALID_CREDENTIALS,
                message="La contraseña actual no es válida.",
            )
        user.password_hash = hash_password(payload.new_password)
        await user.save()
