"""Admin CRUD tools for experiences."""

from __future__ import annotations

import time
from typing import Any
from uuid import uuid4

from app.ai.mcp.tool_contracts import (
    AdminCreateExperienceOutput,
    AdminDeactivateExperienceOutput,
    AdminListExperiencesOutput,
    AdminUpdateExperienceOutput,
    ToolBlockingReason,
)
from app.core.errors import ApiError
from app.documents import ExperienceDocument
from app.schemas.experience import ExperienceCreateSchema, ExperienceUpdateSchema
from app.services.experience_service import ExperienceService


def _get_service() -> ExperienceService:
    from app.core.di import Container
    return Container.get_instance().experience_service


def _format_experience_matches(matches: list[dict[str, Any]]) -> str:
    return ", ".join(
        str(item.get("label") or item.get("name") or item.get("experience_id"))
        for item in matches[:5]
        if isinstance(item, dict)
    )


async def admin_create_experience(**kwargs: Any) -> dict[str, Any]:
    trace_id = kwargs.get("trace_id") or str(uuid4())
    conversation_turn_id = kwargs.get("conversation_turn_id")
    started = time.perf_counter()
    error_code: str | None = None
    output: AdminCreateExperienceOutput | None = None

    try:
        filtered = {
            k: v
            for k, v in kwargs.items()
            if k in ExperienceCreateSchema.model_fields
        }
        payload = ExperienceCreateSchema.model_validate(filtered)
        doc = await _get_service().create(payload)

        output = AdminCreateExperienceOutput(
            created=True,
            trace_id=trace_id,
            experience_id=str(doc.id),
            name=doc.name,
            message=f"Experiencia '{doc.name}' creada exitosamente.",
        )
        return output.model_dump(mode="json")

    except ApiError as exc:
        error_code = exc.code
        output = AdminCreateExperienceOutput(
            created=False,
            trace_id=trace_id,
            blocking_reasons=[
                ToolBlockingReason(code=exc.code, message=exc.message, details=exc.details or {})
            ],
        )
        return output.model_dump(mode="json")

    except Exception as exc:
        error_code = "tool.unhandled_error"
        output = AdminCreateExperienceOutput(
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
            tool_name="admin_create_experience",
            input={k: v for k, v in kwargs.items() if k not in {"trace_id", "conversation_turn_id"}},
            output=output.model_dump(mode="json") if output else {},
            status="error" if error_code else "success",
            error_code=error_code,
            latency_ms=latency_ms,
        ).insert()


async def admin_update_experience(**kwargs: Any) -> dict[str, Any]:
    trace_id = kwargs.get("trace_id") or str(uuid4())
    conversation_turn_id = kwargs.get("conversation_turn_id")
    started = time.perf_counter()
    error_code: str | None = None
    output: AdminUpdateExperienceOutput | None = None

    try:
        experience_id = kwargs.get("experience_id")
        if not experience_id:
            output = AdminUpdateExperienceOutput(
                updated=False,
                trace_id=trace_id,
                blocking_reasons=[
                    ToolBlockingReason(
                        code="experience.id_required",
                        message="El campo experience_id es obligatorio.",
                    )
                ],
            )
            return output.model_dump(mode="json")

        filtered = {
            k: v
            for k, v in kwargs.items()
            if k in ExperienceUpdateSchema.model_fields and v is not None
        }
        payload = ExperienceUpdateSchema.model_validate(filtered)
        doc = await _get_service().update(experience_id, payload)

        output = AdminUpdateExperienceOutput(
            updated=True,
            trace_id=trace_id,
            experience_id=str(doc.id),
            name=doc.name,
            message=f"Experiencia '{doc.name}' actualizada exitosamente.",
        )
        return output.model_dump(mode="json")

    except ApiError as exc:
        error_code = exc.code
        output = AdminUpdateExperienceOutput(
            updated=False,
            trace_id=trace_id,
            blocking_reasons=[
                ToolBlockingReason(code=exc.code, message=exc.message, details=exc.details or {})
            ],
        )
        return output.model_dump(mode="json")

    except Exception as exc:
        error_code = "tool.unhandled_error"
        output = AdminUpdateExperienceOutput(
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
            tool_name="admin_update_experience",
            input={k: v for k, v in kwargs.items() if k not in {"trace_id", "conversation_turn_id"}},
            output=output.model_dump(mode="json") if output else {},
            status="error" if error_code else "success",
            error_code=error_code,
            latency_ms=latency_ms,
        ).insert()


async def admin_list_experiences_admin(**kwargs: Any) -> dict[str, Any]:
    trace_id = kwargs.get("trace_id") or str(uuid4())
    conversation_turn_id = kwargs.get("conversation_turn_id")
    started = time.perf_counter()
    error_code: str | None = None
    output: AdminListExperiencesOutput | None = None

    try:
        is_active = kwargs.get("is_active")
        limit = kwargs.get("limit", 50)

        docs = await _get_service().list(is_active=is_active)
        docs = docs[:limit]

        items = []
        for doc in docs:
            pricing = getattr(doc, "pricing", None)
            min_price = None
            if pricing and pricing.tiers:
                min_price = min(
                    (t.price_per_person for t in pricing.tiers if hasattr(t, "price_per_person")),
                    default=None,
                )
            items.append(
                {
                    "experience_id": str(doc.id),
                    "name": doc.name,
                    "slug": doc.slug,
                    "is_active": doc.is_active,
                    "status": str(getattr(doc, "status", "")),
                    "starting_price": min_price,
                }
            )

        output = AdminListExperiencesOutput(
            trace_id=trace_id,
            total=len(items),
            experiences=items,
        )
        return output.model_dump(mode="json")

    except Exception as exc:
        error_code = "tool.unhandled_error"
        output = AdminListExperiencesOutput(
            trace_id=trace_id,
            total=0,
            experiences=[],
            blocking_reasons=[ToolBlockingReason(code=error_code, message=str(exc))],
        )
        return output.model_dump(mode="json")

    finally:
        from app.documents.tool_call_log_document import ToolCallLogDocument

        latency_ms = int((time.perf_counter() - started) * 1000)
        await ToolCallLogDocument(
            trace_id=trace_id,
            conversation_turn_id=conversation_turn_id,
            tool_name="admin_list_experiences_admin",
            input={k: v for k, v in kwargs.items() if k not in {"trace_id", "conversation_turn_id"}},
            output=output.model_dump(mode="json") if output else {},
            status="error" if error_code else "success",
            error_code=error_code,
            latency_ms=latency_ms,
        ).insert()


async def admin_deactivate_experience(**kwargs: Any) -> dict[str, Any]:
    trace_id = kwargs.get("trace_id") or str(uuid4())
    conversation_turn_id = kwargs.get("conversation_turn_id")
    started = time.perf_counter()
    error_code: str | None = None
    output: AdminDeactivateExperienceOutput | None = None

    try:
        experience_id = kwargs.get("experience_id")
        if not experience_id and kwargs.get("q"):
            resolution = await _get_service().resolve_experience_reference(str(kwargs["q"]))
            if resolution.get("status") == "resolved":
                experience_id = str(resolution.get("experience_id"))
            elif resolution.get("matches"):
                matches = resolution.get("matches", [])
                message = (
                    f"Encontré estas coincidencias para experiencia '{resolution.get('reference', kwargs['q'])}': "
                    f"{_format_experience_matches(matches)}. Indícame el experience_id exacto o copia una de estas opciones."
                )
                output = AdminDeactivateExperienceOutput(
                    deactivated=False,
                    trace_id=trace_id,
                    blocking_reasons=[
                        ToolBlockingReason(
                            code="experience.reference_ambiguous",
                            message=message,
                            details={"matches": matches},
                        )
                    ],
                )
                return output.model_dump(mode="json")
            else:
                message = (
                    f"No encontré coincidencias para experiencia '{resolution.get('reference', kwargs['q'])}'. "
                    "Indícame el experience_id exacto o el nombre/slug exacto."
                )
                output = AdminDeactivateExperienceOutput(
                    deactivated=False,
                    trace_id=trace_id,
                    blocking_reasons=[
                        ToolBlockingReason(code="experience.reference_not_found", message=message)
                    ],
                )
                return output.model_dump(mode="json")

        if not experience_id:
            output = AdminDeactivateExperienceOutput(
                deactivated=False,
                trace_id=trace_id,
                blocking_reasons=[
                    ToolBlockingReason(
                        code="experience.id_required",
                        message="El campo experience_id es obligatorio.",
                    )
                ],
            )
            return output.model_dump(mode="json")

        doc = await _get_service().deactivate(experience_id)
        output = AdminDeactivateExperienceOutput(
            deactivated=True,
            trace_id=trace_id,
            experience_id=str(doc.id),
            name=doc.name,
            message=f"Experiencia '{doc.name}' desactivada exitosamente.",
        )
        return output.model_dump(mode="json")

    except ApiError as exc:
        error_code = exc.code
        output = AdminDeactivateExperienceOutput(
            deactivated=False,
            trace_id=trace_id,
            blocking_reasons=[
                ToolBlockingReason(code=exc.code, message=exc.message, details=exc.details or {})
            ],
        )
        return output.model_dump(mode="json")

    except Exception as exc:
        error_code = "tool.unhandled_error"
        output = AdminDeactivateExperienceOutput(
            deactivated=False,
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
            tool_name="admin_deactivate_experience",
            input={k: v for k, v in kwargs.items() if k not in {"trace_id", "conversation_turn_id"}},
            output=output.model_dump(mode="json") if output else {},
            status="error" if error_code else "success",
            error_code=error_code,
            latency_ms=latency_ms,
        ).insert()
