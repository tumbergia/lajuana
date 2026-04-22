"""Dependencias de autenticacion y autorizacion basadas en permisos."""

from typing import Annotated

import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.common.enums import ROLE_PERMISSIONS, Permission
from app.common.labels import ErrorCode
from app.core.errors import ApiError
from app.core.security import decode_token
from app.documents import UserDocument

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> UserDocument:
    """Resuelve el usuario autenticado desde el bearer token."""
    if credentials is None:
        raise ApiError(
            status_code=401,
            code=ErrorCode.AUTH_UNAUTHORIZED,
            message="Token requerido.",
        )
    try:
        payload = decode_token(credentials.credentials)
    except jwt.ExpiredSignatureError as exc:
        raise ApiError(
            status_code=401,
            code=ErrorCode.AUTH_EXPIRED_TOKEN,
            message="El token ha expirado.",
        ) from exc
    except jwt.PyJWTError as exc:
        raise ApiError(
            status_code=401,
            code=ErrorCode.AUTH_INVALID_TOKEN,
            message="Token inválido.",
        ) from exc
    if payload.get("type") != "access":
        raise ApiError(
            status_code=401,
            code=ErrorCode.AUTH_INVALID_TOKEN,
            message="Token inválido.",
        )

    user = await UserDocument.get(payload.get("sub"))
    if user is None:
        raise ApiError(
            status_code=401,
            code=ErrorCode.AUTH_INVALID_TOKEN,
            message="Token inválido.",
        )
    if not user.is_active:
        raise ApiError(
            status_code=401,
            code=ErrorCode.AUTH_INACTIVE_USER,
            message="Usuario inactivo.",
        )
    return user


def require_permissions(*required: Permission):
    """Dependency de autorización por permisos explícitos."""

    async def dependency(
        current_user: Annotated[UserDocument, Depends(get_current_user)],
    ) -> UserDocument:
        user_permissions = ROLE_PERMISSIONS[current_user.role]
        missing = [perm.value for perm in required if perm not in user_permissions]
        if missing:
            raise ApiError(
                status_code=403,
                code=ErrorCode.AUTH_FORBIDDEN,
                message="No tiene permisos para realizar esta acción.",
                details={"missing_permissions": missing},
            )
        return current_user

    return dependency
