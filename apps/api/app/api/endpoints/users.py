"""Router administrativo de usuarios internos."""

from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.deps import require_permissions
from app.api.docs import COMMON_AUTH_RESPONSES
from app.common.enums import Permission
from app.documents import UserDocument
from app.schemas.auth import UserCreateSchema, UserResponseSchema, UserUpdateSchema
from app.schemas.common import ApiErrorResponse
from app.services import UserService
from app.services.mappers import user_to_response

router = APIRouter(prefix="/users", tags=["Users"])
service = UserService()


@router.post(
    "",
    summary="Crear usuario interno",
    description="Crea un usuario interno con rol operativo asignado por administrador.",
    response_model=UserResponseSchema,
    status_code=status.HTTP_201_CREATED,
    operation_id="createUser",
    responses={
        **COMMON_AUTH_RESPONSES,
        409: {"model": ApiErrorResponse, "description": "El correo ya existe."},
    },
)
async def create_user(
    payload: UserCreateSchema,
    _: Annotated[UserDocument, Depends(require_permissions(Permission.USER_CREATE))],
) -> UserResponseSchema:
    user = await service.create_user(payload)
    return user_to_response(user)


@router.get(
    "",
    summary="Listar usuarios internos",
    description="Lista usuarios internos del sistema. Solo administración.",
    response_model=list[UserResponseSchema],
    status_code=status.HTTP_200_OK,
    operation_id="listUsers",
    responses=COMMON_AUTH_RESPONSES,
)
async def list_users(
    _: Annotated[UserDocument, Depends(require_permissions(Permission.USER_READ))],
) -> list[UserResponseSchema]:
    users = await service.list_users()
    return [user_to_response(user) for user in users]


@router.get(
    "/{user_id}",
    summary="Consultar usuario",
    description="Obtiene el detalle de un usuario interno por identificador.",
    response_model=UserResponseSchema,
    status_code=status.HTTP_200_OK,
    operation_id="getUserById",
    responses={
        **COMMON_AUTH_RESPONSES,
        404: {"model": ApiErrorResponse, "description": "Usuario no encontrado."},
    },
)
async def get_user(
    user_id: str,
    _: Annotated[UserDocument, Depends(require_permissions(Permission.USER_READ))],
) -> UserResponseSchema:
    user = await service.get_user(user_id)
    return user_to_response(user)


@router.patch(
    "/{user_id}",
    summary="Actualizar usuario",
    description="Actualiza datos de usuario y asignación de rol (admin-only).",
    response_model=UserResponseSchema,
    status_code=status.HTTP_200_OK,
    operation_id="updateUserById",
    responses={
        **COMMON_AUTH_RESPONSES,
        404: {"model": ApiErrorResponse, "description": "Usuario no encontrado."},
    },
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
    summary="Desactivar usuario",
    description="Realiza baja lógica de usuario (`is_active=false`).",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="softDeleteUserById",
    responses={
        **COMMON_AUTH_RESPONSES,
        404: {"model": ApiErrorResponse, "description": "Usuario no encontrado."},
        409: {"model": ApiErrorResponse, "description": "No se permite auto-desactivación."},
    },
)
async def delete_user(
    user_id: str,
    actor: Annotated[UserDocument, Depends(require_permissions(Permission.USER_DELETE))],
) -> None:
    await service.soft_delete_user(user_id=user_id, actor_id=str(actor.id))
