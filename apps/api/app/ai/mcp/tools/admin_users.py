"""Admin CRUD tools for users."""

from __future__ import annotations

import time
from typing import Any
from uuid import uuid4

from app.ai.mcp.tool_contracts import (
    AdminCreateUserOutput,
    AdminDeactivateUserOutput,
    AdminListUsersOutput,
    AdminUpdateUserOutput,
    ToolBlockingReason,
)
from app.core.errors import ApiError
from app.schemas.auth import UserCreateSchema, UserUpdateSchema
from app.services.user_service import UserService


def _get_service() -> UserService:
    from app.core.di import Container

    return Container.get_instance().user_service


async def admin_list_users(**kwargs: Any) -> dict[str, Any]:
    trace_id = kwargs.get("trace_id") or str(uuid4())
    conversation_turn_id = kwargs.get("conversation_turn_id")
    started = time.perf_counter()
    error_code: str | None = None
    output: AdminListUsersOutput | None = None

    try:
        docs = await _get_service().list_users()
        items = []
        for doc in docs:
            items.append(
                {
                    "user_id": str(doc.id),
                    "email": doc.email,
                    "full_name": doc.full_name,
                    "role": str(doc.role),
                    "is_active": doc.is_active,
                }
            )

        output = AdminListUsersOutput(
            trace_id=trace_id,
            total=len(items),
            users=items,
        )
        return output.model_dump(mode="json")

    except Exception as exc:
        error_code = "tool.unhandled_error"
        output = AdminListUsersOutput(
            trace_id=trace_id,
            total=0,
            users=[],
            blocking_reasons=[ToolBlockingReason(code=error_code, message=str(exc))],
        )
        return output.model_dump(mode="json")

    finally:
        from app.documents.tool_call_log_document import ToolCallLogDocument

        latency_ms = int((time.perf_counter() - started) * 1000)
        await ToolCallLogDocument(
            trace_id=trace_id,
            conversation_turn_id=conversation_turn_id,
            tool_name="admin_list_users",
            input={},
            output=output.model_dump(mode="json") if output else {},
            status="error" if error_code else "success",
            error_code=error_code,
            latency_ms=latency_ms,
        ).insert()


async def admin_create_user(**kwargs: Any) -> dict[str, Any]:
    trace_id = kwargs.get("trace_id") or str(uuid4())
    conversation_turn_id = kwargs.get("conversation_turn_id")
    started = time.perf_counter()
    error_code: str | None = None
    output: AdminCreateUserOutput | None = None

    try:
        filtered = {k: v for k, v in kwargs.items() if k in UserCreateSchema.model_fields}
        payload = UserCreateSchema.model_validate(filtered)
        doc = await _get_service().create_user(payload)

        output = AdminCreateUserOutput(
            created=True,
            trace_id=trace_id,
            user_id=str(doc.id),
            email=doc.email,
            role=str(doc.role),
            message=f"Usuario '{doc.email}' creado exitosamente con rol {doc.role}.",
        )
        return output.model_dump(mode="json")

    except ApiError as exc:
        error_code = exc.code
        output = AdminCreateUserOutput(
            created=False,
            trace_id=trace_id,
            blocking_reasons=[
                ToolBlockingReason(code=exc.code, message=exc.message, details=exc.details or {})
            ],
        )
        return output.model_dump(mode="json")

    except Exception as exc:
        error_code = "tool.unhandled_error"
        output = AdminCreateUserOutput(
            created=False,
            trace_id=trace_id,
            blocking_reasons=[ToolBlockingReason(code=error_code, message=str(exc))],
        )
        return output.model_dump(mode="json")

    finally:
        from app.documents.tool_call_log_document import ToolCallLogDocument

        latency_ms = int((time.perf_counter() - started) * 1000)
        await ToolCallLogDocument(
            trace_id=trace_id,
            conversation_turn_id=conversation_turn_id,
            tool_name="admin_create_user",
            input={
                k: v for k, v in kwargs.items() if k not in {"trace_id", "conversation_turn_id"}
            },
            output=output.model_dump(mode="json") if output else {},
            status="error" if error_code else "success",
            error_code=error_code,
            latency_ms=latency_ms,
        ).insert()


async def admin_update_user(**kwargs: Any) -> dict[str, Any]:
    trace_id = kwargs.get("trace_id") or str(uuid4())
    conversation_turn_id = kwargs.get("conversation_turn_id")
    started = time.perf_counter()
    error_code: str | None = None
    output: AdminUpdateUserOutput | None = None

    try:
        user_id = kwargs.get("user_id")
        if not user_id:
            output = AdminUpdateUserOutput(
                updated=False,
                trace_id=trace_id,
                blocking_reasons=[
                    ToolBlockingReason(
                        code="user.id_required",
                        message="El campo user_id es obligatorio.",
                    )
                ],
            )
            return output.model_dump(mode="json")

        filtered = {
            k: v for k, v in kwargs.items() if k in UserUpdateSchema.model_fields and v is not None
        }
        payload = UserUpdateSchema.model_validate(filtered)
        doc = await _get_service().update_user(user_id, payload)

        output = AdminUpdateUserOutput(
            updated=True,
            trace_id=trace_id,
            user_id=str(doc.id),
            email=doc.email,
            role=str(doc.role),
            message=f"Usuario '{doc.email}' actualizado exitosamente.",
        )
        return output.model_dump(mode="json")

    except ApiError as exc:
        error_code = exc.code
        output = AdminUpdateUserOutput(
            updated=False,
            trace_id=trace_id,
            blocking_reasons=[
                ToolBlockingReason(code=exc.code, message=exc.message, details=exc.details or {})
            ],
        )
        return output.model_dump(mode="json")

    except Exception as exc:
        error_code = "tool.unhandled_error"
        output = AdminUpdateUserOutput(
            updated=False,
            trace_id=trace_id,
            blocking_reasons=[ToolBlockingReason(code=error_code, message=str(exc))],
        )
        return output.model_dump(mode="json")

    finally:
        from app.documents.tool_call_log_document import ToolCallLogDocument

        latency_ms = int((time.perf_counter() - started) * 1000)
        await ToolCallLogDocument(
            trace_id=trace_id,
            conversation_turn_id=conversation_turn_id,
            tool_name="admin_update_user",
            input={
                k: v for k, v in kwargs.items() if k not in {"trace_id", "conversation_turn_id"}
            },
            output=output.model_dump(mode="json") if output else {},
            status="error" if error_code else "success",
            error_code=error_code,
            latency_ms=latency_ms,
        ).insert()


async def admin_deactivate_user(**kwargs: Any) -> dict[str, Any]:
    trace_id = kwargs.get("trace_id") or str(uuid4())
    conversation_turn_id = kwargs.get("conversation_turn_id")
    started = time.perf_counter()
    error_code: str | None = None
    output: AdminDeactivateUserOutput | None = None

    try:
        user_id = kwargs.get("user_id")
        actor_id = kwargs.get("actor_id", "system")
        if not user_id and kwargs.get("q"):
            resolution = await _get_service().resolve_user_reference(str(kwargs["q"]))
            if resolution.get("status") == "resolved":
                user_id = resolution.get("user_id")
            elif resolution.get("status") == "ambiguous":
                matches = resolution.get("matches", [])
                match_list = ", ".join(
                    f"{item.get('full_name')} <{item.get('email')}>"
                    for item in matches
                    if isinstance(item, dict)
                )
                message = (
                    f"Encontré varios usuarios para '{resolution.get('reference', kwargs['q'])}': "
                    f"{match_list}. Indícame el correo o el user_id exacto."
                )
                output = AdminDeactivateUserOutput(
                    deactivated=False,
                    trace_id=trace_id,
                    message=message,
                    blocking_reasons=[
                        ToolBlockingReason(
                            code="user.reference_ambiguous",
                            message=message,
                            details={"matches": matches},
                        )
                    ],
                )
                return output.model_dump(mode="json")
            else:
                message = (
                    f"No encontré un usuario que coincida con '{resolution.get('reference', kwargs['q'])}'. "
                    "Indícame el correo o el user_id exacto."
                )
                output = AdminDeactivateUserOutput(
                    deactivated=False,
                    trace_id=trace_id,
                    message=message,
                    blocking_reasons=[
                        ToolBlockingReason(
                            code="user.reference_not_found",
                            message=message,
                        )
                    ],
                )
                return output.model_dump(mode="json")

        if not user_id:
            output = AdminDeactivateUserOutput(
                deactivated=False,
                trace_id=trace_id,
                message="El campo user_id es obligatorio.",
                blocking_reasons=[
                    ToolBlockingReason(
                        code="user.id_required",
                        message="El campo user_id es obligatorio.",
                    )
                ],
            )
            return output.model_dump(mode="json")

        await _get_service().soft_delete_user(user_id, actor_id)
        output = AdminDeactivateUserOutput(
            deactivated=True,
            trace_id=trace_id,
            user_id=user_id,
            message="Usuario desactivado exitosamente.",
        )
        return output.model_dump(mode="json")

    except ApiError as exc:
        error_code = exc.code
        output = AdminDeactivateUserOutput(
            deactivated=False,
            trace_id=trace_id,
            message=exc.message,
            blocking_reasons=[
                ToolBlockingReason(code=exc.code, message=exc.message, details=exc.details or {})
            ],
        )
        return output.model_dump(mode="json")

    except Exception as exc:
        error_code = "tool.unhandled_error"
        output = AdminDeactivateUserOutput(
            deactivated=False,
            trace_id=trace_id,
            message=str(exc),
            blocking_reasons=[ToolBlockingReason(code=error_code, message=str(exc))],
        )
        return output.model_dump(mode="json")

    finally:
        from app.documents.tool_call_log_document import ToolCallLogDocument

        latency_ms = int((time.perf_counter() - started) * 1000)
        await ToolCallLogDocument(
            trace_id=trace_id,
            conversation_turn_id=conversation_turn_id,
            tool_name="admin_deactivate_user",
            input={
                k: v for k, v in kwargs.items() if k not in {"trace_id", "conversation_turn_id"}
            },
            output=output.model_dump(mode="json") if output else {},
            status="error" if error_code else "success",
            error_code=error_code,
            latency_ms=latency_ms,
        ).insert()
