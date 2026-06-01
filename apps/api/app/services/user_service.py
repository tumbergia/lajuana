"""Servicios administrativos para usuarios internos."""

from app.common.enums import UserRole
from app.common.labels import ErrorCode
from app.core.errors import ApiError
from app.core.security import hash_password
from app.documents import UserDocument
from app.schemas.auth import UserCreateSchema, UserUpdateSchema


class UserService:
    """CRUD administrativo de usuarios."""

    async def create_user(self, payload: UserCreateSchema) -> UserDocument:
        existing = await UserDocument.find_one({"email": payload.email})
        if existing is not None:
            raise ApiError(
                status_code=409,
                code=ErrorCode.USER_EMAIL_ALREADY_EXISTS,
                message="Ya existe un usuario con este correo.",
            )
        if payload.role not in {UserRole.ADMIN, UserRole.GUIDE, UserRole.UNASSIGNED}:
            raise ApiError(
                status_code=400,
                code=ErrorCode.USER_ROLE_INVALID,
                message="Rol inválido para creación de usuario.",
            )
        user = UserDocument(
            email=payload.email,
            full_name=payload.full_name,
            password_hash=hash_password(payload.password),
            role=payload.role,
        )
        await user.insert()
        return user

    async def list_users(self, limit: int = 200, skip: int = 0) -> list[UserDocument]:
        return await UserDocument.find_all().skip(skip).limit(limit).to_list()

    async def count_users(self) -> int:
        return await UserDocument.find_all().count()

    async def get_user(self, user_id: str) -> UserDocument:
        user = await UserDocument.get(user_id)
        if user is None:
            raise ApiError(
                status_code=404,
                code=ErrorCode.USER_NOT_FOUND,
                message="Usuario no encontrado.",
            )
        return user

    async def update_user(self, user_id: str, payload: UserUpdateSchema) -> UserDocument:
        user = await self.get_user(user_id)
        updates = payload.model_dump(exclude_none=True)
        if "role" in updates and updates["role"] not in {
            UserRole.ADMIN,
            UserRole.GUIDE,
            UserRole.UNASSIGNED,
        }:
            raise ApiError(
                status_code=400,
                code=ErrorCode.USER_ROLE_INVALID,
                message="Rol inválido.",
            )
        for field, value in updates.items():
            setattr(user, field, value)
        await user.save()
        return user

    async def soft_delete_user(self, user_id: str, actor_id: str) -> None:
        if actor_id == user_id:
            raise ApiError(
                status_code=409,
                code=ErrorCode.USER_SELF_DELETE_FORBIDDEN,
                message="No puedes desactivar tu propia cuenta.",
            )
        user = await self.get_user(user_id)
        user.is_active = False
        await user.save()
