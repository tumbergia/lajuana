"""Router administrativo de usuarios internos."""

from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.deps import require_permissions
from app.api.docs import ENDPOINT_DOCS, endpoint_description, endpoint_responses
from app.common.enums import Permission
from app.documents import UserDocument
from app.schemas.auth import UserCreateSchema, UserResponseSchema, UserUpdateSchema
from app.services import UserService
from app.services.mappers import user_to_response

router = APIRouter(prefix="/users", tags=["Usuarios"])
service = UserService()


@router.post(
    "",
    summary=ENDPOINT_DOCS["users_create"]["summary"],
    description=endpoint_description("users_create"),
    response_model=UserResponseSchema,
    status_code=status.HTTP_201_CREATED,
    operation_id="createUser",
    responses=endpoint_responses("users_create"),
)
async def create_user(
    payload: UserCreateSchema,
    _: Annotated[UserDocument, Depends(require_permissions(Permission.USER_CREATE))],
) -> UserResponseSchema:
    user = await service.create_user(payload)
    return user_to_response(user)


@router.get(
    "",
    summary=ENDPOINT_DOCS["users_list"]["summary"],
    description=endpoint_description("users_list"),
    response_model=list[UserResponseSchema],
    status_code=status.HTTP_200_OK,
    operation_id="listUsers",
    responses=endpoint_responses("users_list"),
)
async def list_users(
    _: Annotated[UserDocument, Depends(require_permissions(Permission.USER_READ))],
) -> list[UserResponseSchema]:
    users = await service.list_users()
    return [user_to_response(user) for user in users]


@router.get(
    "/{user_id}",
    summary=ENDPOINT_DOCS["users_get"]["summary"],
    description=endpoint_description("users_get"),
    response_model=UserResponseSchema,
    status_code=status.HTTP_200_OK,
    operation_id="getUserById",
    responses=endpoint_responses("users_get"),
)
async def get_user(
    user_id: str,
    _: Annotated[UserDocument, Depends(require_permissions(Permission.USER_READ))],
) -> UserResponseSchema:
    user = await service.get_user(user_id)
    return user_to_response(user)


@router.patch(
    "/{user_id}",
    summary=ENDPOINT_DOCS["users_update"]["summary"],
    description=endpoint_description("users_update"),
    response_model=UserResponseSchema,
    status_code=status.HTTP_200_OK,
    operation_id="updateUserById",
    responses=endpoint_responses("users_update"),
)
async def update_user(
    user_id: str,
    payload: UserUpdateSchema,
    _: Annotated[UserDocument, Depends(require_permissions(Permission.USER_UPDATE))],
) -> UserResponseSchema:
    user = await service.update_user(user_id, payload)
    return user_to_response(user)


@router.delete(
    "/{user_id}",
    summary=ENDPOINT_DOCS["users_delete"]["summary"],
    description=endpoint_description("users_delete"),
    status_code=status.HTTP_200_OK,
    operation_id="softDeleteUserById",
    responses=endpoint_responses("users_delete"),
)
async def delete_user(
    user_id: str,
    actor: Annotated[UserDocument, Depends(require_permissions(Permission.USER_DELETE))],
) -> None:
    await service.soft_delete_user(user_id=user_id, actor_id=str(actor.id))
