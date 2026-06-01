"""Dependencias de autenticacion, autorizacion e inyeccion de servicios."""

from typing import Annotated

import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.common.enums import ROLE_PERMISSIONS, Permission
from app.common.labels import ErrorCode
from app.core.di import Container
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


# ── Service injection dependencies ──────────────────────────────────


def get_reservation_service() -> object:
    return Container.get_instance().reservation_service


def get_notification_service() -> object:
    return Container.get_instance().notification_service


def get_booking_service() -> object:
    return Container.get_instance().booking_service


def get_payment_proof_service() -> object:
    return Container.get_instance().payment_proof_service


def get_config_service() -> object:
    return Container.get_instance().config_service


def get_auth_service() -> object:
    return Container.get_instance().auth_service


def get_user_service() -> object:
    return Container.get_instance().user_service


def get_experience_service() -> object:
    return Container.get_instance().experience_service


def get_equine_service() -> object:
    return Container.get_instance().equine_service


def get_saddle_service() -> object:
    return Container.get_instance().saddle_service


def get_schedule_service() -> object:
    return Container.get_instance().schedule_service


def get_participant_service() -> object:
    return Container.get_instance().participant_service


def get_file_upload_service() -> object:
    return Container.get_instance().file_upload_service


def get_sync_service() -> object:
    return Container.get_instance().sync_service


def get_policy_service() -> object:
    return Container.get_instance().policy_service


def get_provider_service() -> object:
    return Container.get_instance().provider_service


def get_reservation_draft_service() -> object:
    return Container.get_instance().reservation_draft_service


def get_assignment_service() -> object:
    return Container.get_instance().assignment_service


def get_service_log_service() -> object:
    return Container.get_instance().service_log_service


def get_participant_form_link_service() -> object:
    return Container.get_instance().participant_form_link_service


def get_whatsapp_ingestion_service() -> object:
    return Container.get_instance().whatsapp_ingestion_service
