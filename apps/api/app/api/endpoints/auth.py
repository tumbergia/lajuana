from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.documents import UserDocument
from app.schemas.auth import (
    TokenResponseSchema,
    UserChangePasswordSchema,
    UserCreateSchema,
    UserLoginSchema,
    UserResponseSchema,
)
from app.services import AuthService
from app.services.mappers import user_to_response

router = APIRouter(prefix="/auth", tags=["auth"])
service = AuthService()


@router.post("/register", response_model=UserResponseSchema)
async def register(payload: UserCreateSchema) -> UserResponseSchema:
    user = await service.register(payload)
    return user_to_response(user)


@router.post("/login", response_model=TokenResponseSchema)
async def login(payload: UserLoginSchema) -> TokenResponseSchema:
    _, token = await service.login(payload)
    return token


@router.post("/refresh", response_model=TokenResponseSchema)
async def refresh(refresh_token: str) -> TokenResponseSchema:
    return await service.refresh(refresh_token)


@router.post("/logout", status_code=204)
async def logout(current_user: Annotated[UserDocument, Depends(get_current_user)]) -> None:
    await service.logout(str(current_user.id))


@router.post("/change-password", status_code=204)
async def change_password(
    payload: UserChangePasswordSchema,
    current_user: Annotated[UserDocument, Depends(get_current_user)],
) -> None:
    await service.change_password(str(current_user.id), payload)


@router.get("/me", response_model=UserResponseSchema)
async def me(
    current_user: Annotated[UserDocument, Depends(get_current_user)],
) -> UserResponseSchema:
    return user_to_response(current_user)
