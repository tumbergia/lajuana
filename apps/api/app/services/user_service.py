"""Servicios administrativos para usuarios internos."""

from __future__ import annotations

import re
import unicodedata
from typing import Any

from app.common.enums import UserRole
from app.common.labels import ErrorCode
from app.core.errors import ApiError
from app.core.security import hash_password
from app.documents import UserDocument
from app.schemas.auth import UserCreateSchema, UserUpdateSchema


def _normalize_lookup_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_text = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    cleaned = re.sub(r"[^a-z0-9@._-]+", " ", ascii_text.lower()).strip()
    return re.sub(r"\s+", " ", cleaned)


def _build_user_label(user: UserDocument) -> str:
    return f"{user.full_name} <{user.email}>"


class UserService:
    """CRUD administrativo de usuarios."""

    async def resolve_user_reference(self, reference: str) -> dict[str, Any]:
        query = reference.strip()
        if not query:
            return {"status": "missing"}

        normalized_query = _normalize_lookup_text(query)
        query_has_email = "@" in normalized_query
        query_has_multiple_tokens = " " in normalized_query
        users = await self.list_users(limit=200)
        candidates: list[dict[str, Any]] = []

        for user in users:
            email = _normalize_lookup_text(user.email)
            email_local = email.split("@", 1)[0]
            full_name = _normalize_lookup_text(user.full_name)
            tokens = [token for token in full_name.split(" ") if token]
            score = 0

            if query_has_email and normalized_query == email:
                score = 100
            elif query_has_multiple_tokens and normalized_query == full_name:
                score = 95
            elif normalized_query == email_local:
                score = 88 if not query_has_email and not query_has_multiple_tokens else 92
            elif normalized_query in tokens:
                score = 88
            elif any(token.startswith(normalized_query) for token in tokens):
                score = 78
            elif full_name.startswith(normalized_query) or email_local.startswith(normalized_query):
                score = 72
            elif normalized_query in full_name or normalized_query in email_local:
                score = 60

            if score == 0:
                continue

            candidates.append(
                {
                    "score": score,
                    "user": user,
                    "summary": {
                        "user_id": str(user.id),
                        "email": user.email,
                        "full_name": user.full_name,
                        "is_active": user.is_active,
                    },
                }
            )

        if not candidates:
            return {"status": "not_found", "reference": query, "matches": []}

        candidates.sort(
            key=lambda item: (
                -item["score"],
                not item["user"].is_active,
                len(item["user"].full_name),
            )
        )
        top_score = candidates[0]["score"]
        top_candidates = [item for item in candidates if item["score"] == top_score]

        if len(top_candidates) == 1 and top_score >= 72:
            user = top_candidates[0]["user"]
            return {
                "status": "resolved",
                "reference": query,
                "user_id": str(user.id),
                "label": _build_user_label(user),
                "match_score": top_score,
            }

        return {
            "status": "ambiguous",
            "reference": query,
            "matches": [item["summary"] for item in top_candidates[:5]],
        }

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
