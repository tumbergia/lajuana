"""Router de autenticación y control de acceso."""

from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.deps import get_current_user, require_permissions
from app.api.docs import COMMON_AUTH_RESPONSES
from app.common.enums import Permission
from app.documents import UserDocument
from app.schemas.auth import (
    RegisterRequest,
    TokenResponseSchema,
    UserChangePasswordSchema,
    UserLoginSchema,
    UserResponseSchema,
)
from app.schemas.common import ApiErrorResponse
from app.services import AuthService
from app.services.mappers import user_to_response

router = APIRouter(prefix="/auth", tags=["Authentication"])
service = AuthService()


@router.post(
    "/register",
    summary="Registrar usuario público",
    description="Registra una cuenta pública en estado unassigned, sin rol operativo.",
    response_model=UserResponseSchema,
    status_code=status.HTTP_201_CREATED,
    operation_id="registerPublicUser",
    responses={
        409: {"model": ApiErrorResponse, "description": "El correo ya existe."},
        422: COMMON_AUTH_RESPONSES[422],
    },
)
async def register(payload: RegisterRequest) -> UserResponseSchema:
    user = await service.register(payload)
    return user_to_response(user)


@router.post(
    "/login",
    summary="Iniciar sesión",
    description="Autentica un usuario activo y retorna token de acceso.",
    response_model=TokenResponseSchema,
    status_code=status.HTTP_200_OK,
    operation_id="loginUser",
    responses={
        401: {
            "model": ApiErrorResponse,
            "description": "Credenciales inválidas o usuario inactivo.",
        },
        422: COMMON_AUTH_RESPONSES[422],
    },
)
async def login(payload: UserLoginSchema) -> TokenResponseSchema:
    _, token = await service.login(payload)
    return token


@router.post(
    "/refresh",
    summary="Refrescar token",
    description="Renueva el token de acceso utilizando un refresh token válido.",
    response_model=TokenResponseSchema,
    status_code=status.HTTP_200_OK,
    operation_id="refreshToken",
)
async def refresh(refresh_token: str) -> TokenResponseSchema:
    return await service.refresh(refresh_token)


@router.post(
    "/logout",
    summary="Cerrar sesión",
    description="Cierra la sesión actual invalidando el refresh token almacenado.",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="logoutUser",
    responses=COMMON_AUTH_RESPONSES,
)
async def logout(
    current_user: Annotated[UserDocument, Depends(get_current_user)],
) -> None:
    await service.logout(str(current_user.id))


@router.post(
    "/change-password",
    summary="Cambiar contraseña",
    description="Permite al usuario autenticado cambiar su contraseña actual.",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="changePassword",
    responses={
        **COMMON_AUTH_RESPONSES,
        400: {"model": ApiErrorResponse, "description": "La contraseña actual no coincide."},
    },
)
async def change_password(
    payload: UserChangePasswordSchema,
    current_user: Annotated[
        UserDocument,
        Depends(require_permissions(Permission.AUTH_SELF_UPDATE_PASSWORD)),
    ],
) -> None:
    await service.change_password(str(current_user.id), payload)


@router.get(
    "/me",
    summary="Consultar sesión actual",
    description="Retorna identidad y rol del usuario autenticado.",
    response_model=UserResponseSchema,
    status_code=status.HTTP_200_OK,
    operation_id="getCurrentUser",
    responses=COMMON_AUTH_RESPONSES,
)
async def me(
    current_user: Annotated[
        UserDocument,
        Depends(require_permissions(Permission.AUTH_SELF_READ)),
    ],
) -> UserResponseSchema:
    return user_to_response(current_user)
