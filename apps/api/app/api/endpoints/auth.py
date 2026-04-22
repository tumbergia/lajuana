"""Router de autenticación y control de acceso."""

from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.deps import get_current_user, require_permissions
from app.api.docs import ENDPOINT_DOCS, endpoint_description, endpoint_responses
from app.common.enums import Permission
from app.documents import UserDocument
from app.schemas.auth import (
    RegisterRequest,
    TokenResponseSchema,
    UserChangePasswordSchema,
    UserLoginSchema,
    UserResponseSchema,
)
from app.services import AuthService
from app.services.mappers import user_to_response

router = APIRouter(prefix="/auth", tags=["Autenticacion"])
service = AuthService()


@router.post(
    "/register",
    summary=ENDPOINT_DOCS["auth_register"]["summary"],
    description=endpoint_description("auth_register"),
    response_model=UserResponseSchema,
    status_code=status.HTTP_201_CREATED,
    operation_id="registerPublicUser",
    responses=endpoint_responses("auth_register"),
)
async def register(payload: RegisterRequest) -> UserResponseSchema:
    user = await service.register(payload)
    return user_to_response(user)


@router.post(
    "/login",
    summary=ENDPOINT_DOCS["auth_login"]["summary"],
    description=endpoint_description("auth_login"),
    response_model=TokenResponseSchema,
    status_code=status.HTTP_200_OK,
    operation_id="loginUser",
    responses=endpoint_responses("auth_login"),
)
async def login(payload: UserLoginSchema) -> TokenResponseSchema:
    _, token = await service.login(payload)
    return token


@router.post(
    "/refresh",
    summary=ENDPOINT_DOCS["auth_refresh"]["summary"],
    description=endpoint_description("auth_refresh"),
    response_model=TokenResponseSchema,
    status_code=status.HTTP_200_OK,
    operation_id="refreshToken",
    responses=endpoint_responses("auth_refresh"),
)
async def refresh(refresh_token: str) -> TokenResponseSchema:
    return await service.refresh(refresh_token)


@router.post(
    "/logout",
    summary=ENDPOINT_DOCS["auth_logout"]["summary"],
    description=endpoint_description("auth_logout"),
    status_code=status.HTTP_200_OK,
    operation_id="logoutUser",
    responses=endpoint_responses("auth_logout"),
)
async def logout(
    current_user: Annotated[UserDocument, Depends(get_current_user)],
) -> None:
    await service.logout(str(current_user.id))


@router.post(
    "/change-password",
    summary=ENDPOINT_DOCS["auth_change_password"]["summary"],
    description=endpoint_description("auth_change_password"),
    status_code=status.HTTP_200_OK,
    operation_id="changePassword",
    responses=endpoint_responses("auth_change_password"),
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
    summary=ENDPOINT_DOCS["auth_me"]["summary"],
    description=endpoint_description("auth_me"),
    response_model=UserResponseSchema,
    status_code=status.HTTP_200_OK,
    operation_id="getCurrentUser",
    responses=endpoint_responses("auth_me"),
)
async def me(
    current_user: Annotated[
        UserDocument,
        Depends(require_permissions(Permission.AUTH_SELF_READ)),
    ],
) -> UserResponseSchema:
    return user_to_response(current_user)
