from typing import Annotated

import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.common.enums import UserRole
from app.common.labels import ErrorCode
from app.core.errors import ApiError
from app.core.security import decode_token
from app.documents import UserDocument

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> UserDocument:
    if credentials is None:
        raise ApiError(status_code=401, code=ErrorCode.AUTH_FORBIDDEN, message="Token requerido.")
    try:
        payload = decode_token(credentials.credentials)
    except jwt.PyJWTError as exc:
        raise ApiError(
            status_code=401,
            code=ErrorCode.AUTH_INVALID_CREDENTIALS,
            message="Token inválido.",
        ) from exc
    if payload.get("type") != "access":
        raise ApiError(
            status_code=401,
            code=ErrorCode.AUTH_INVALID_CREDENTIALS,
            message="Token inválido.",
        )

    user = await UserDocument.get(payload.get("sub"))
    if user is None:
        raise ApiError(
            status_code=401,
            code=ErrorCode.AUTH_INVALID_CREDENTIALS,
            message="Usuario inválido.",
        )
    return user


def require_roles(*roles: UserRole):
    async def dependency(user: Annotated[UserDocument, Depends(get_current_user)]) -> UserDocument:
        if user.role not in roles:
            raise ApiError(
                status_code=403,
                code=ErrorCode.AUTH_FORBIDDEN,
                message="No tienes permisos para esta operación.",
            )
        return user

    return dependency
