"""Admin CRUD tools for providers."""

from __future__ import annotations

import time
from typing import Any
from uuid import uuid4

from app.ai.mcp.tool_contracts import (
    AdminCreateProviderOutput,
    AdminDeactivateProviderOutput,
    AdminGetProviderOutput,
    AdminListProvidersItem,
    AdminListProvidersOutput,
    AdminUpdateProviderOutput,
    ToolBlockingReason,
)
from app.core.errors import ApiError
from app.schemas.provider import ProviderCreateSchema, ProviderUpdateSchema
from app.services.provider_service import ProviderService


def _get_service() -> ProviderService:
    from app.core.di import Container
    return Container.get_instance().provider_service


def _format_provider_matches(matches: list[dict[str, Any]]) -> str:
    return ", ".join(
        str(item.get("label") or item.get("name") or item.get("provider_id"))
        for item in matches[:5]
        if isinstance(item, dict)
    )


async def _log(
    *,
    trace_id: str,
    conversation_turn_id: str | None,
    tool_name: str,
    input_data: dict[str, Any],
    output: dict[str, Any] | None,
    error_code: str | None,
    started: float,
) -> None:
    from app.documents.tool_call_log_document import ToolCallLogDocument

    latency_ms = int((time.perf_counter() - started) * 1000)
    await ToolCallLogDocument(
        trace_id=trace_id,
        conversation_turn_id=conversation_turn_id,
        tool_name=tool_name,
        input=input_data,
        output=output or {},
        status="error" if error_code else "success",
        error_code=error_code,
        latency_ms=latency_ms,
    ).insert()


async def admin_list_providers(
    q: str | None = None,
    provider_type: str | None = None,
    is_active: bool | None = None,
    limit: int = 200,
    trace_id: str | None = None,
    conversation_turn_id: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    trace_id = trace_id or str(uuid4())
    started = time.perf_counter()
    error_code: str | None = None
    output: AdminListProvidersOutput | None = None

    try:
        from app.documents.provider_document import ProviderType

        ptype = ProviderType(provider_type) if provider_type else None
        docs = await _get_service().list(
            provider_type=ptype,
            q=q,
            is_active=is_active,
            limit=limit,
        )
        items = [
            AdminListProvidersItem(
                provider_id=str(doc.id),
                name=doc.name,
                slug=doc.slug,
                type=str(doc.type),
                status=str(doc.status),
                is_active=doc.is_active,
                contact_name=doc.contact_name,
                whatsapp_phone=doc.whatsapp_phone,
            )
            for doc in docs
        ]
        output = AdminListProvidersOutput(trace_id=trace_id, total=len(items), providers=items)
        return output.model_dump(mode="json")

    except Exception as exc:
        error_code = "tool.unhandled_error"
        output = AdminListProvidersOutput(
            trace_id=trace_id,
            total=0,
            blocking_reasons=[ToolBlockingReason(code=error_code, message=str(exc))],
        )
        return output.model_dump(mode="json")

    finally:
        await _log(
            trace_id=trace_id,
            conversation_turn_id=conversation_turn_id,
            tool_name="admin_list_providers",
            input_data={"q": q, "provider_type": provider_type, "is_active": is_active, "limit": limit},
            output=output.model_dump(mode="json") if output else None,
            error_code=error_code,
            started=started,
        )


async def admin_get_provider(
    provider_id: str,
    trace_id: str | None = None,
    conversation_turn_id: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    trace_id = trace_id or str(uuid4())
    started = time.perf_counter()
    error_code: str | None = None
    output: AdminGetProviderOutput | None = None

    try:
        doc = await _get_service().get(provider_id)
        output = AdminGetProviderOutput(
            trace_id=trace_id,
            found=True,
            provider_id=str(doc.id),
            name=doc.name,
            slug=doc.slug,
            type=str(doc.type),
            status=str(doc.status),
            is_active=doc.is_active,
            contact_name=doc.contact_name,
            email=str(doc.email) if doc.email else None,
            whatsapp_phone=doc.whatsapp_phone,
            location_label=doc.location_label,
        )
        return output.model_dump(mode="json")

    except ApiError as exc:
        error_code = exc.code
        output = AdminGetProviderOutput(
            trace_id=trace_id,
            found=False,
            blocking_reasons=[
                ToolBlockingReason(code=exc.code, message=exc.message, details=exc.details or {})
            ],
        )
        return output.model_dump(mode="json")

    except Exception as exc:
        error_code = "tool.unhandled_error"
        output = AdminGetProviderOutput(
            trace_id=trace_id,
            found=False,
            blocking_reasons=[ToolBlockingReason(code=error_code, message=str(exc))],
        )
        return output.model_dump(mode="json")

    finally:
        await _log(
            trace_id=trace_id,
            conversation_turn_id=conversation_turn_id,
            tool_name="admin_get_provider",
            input_data={"provider_id": provider_id},
            output=output.model_dump(mode="json") if output else None,
            error_code=error_code,
            started=started,
        )


async def admin_create_provider(
    trace_id: str | None = None,
    conversation_turn_id: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    trace_id = trace_id or str(uuid4())
    started = time.perf_counter()
    error_code: str | None = None
    output: AdminCreateProviderOutput | None = None

    try:
        filtered = {k: v for k, v in kwargs.items() if k in ProviderCreateSchema.model_fields}
        payload = ProviderCreateSchema.model_validate(filtered)
        doc = await _get_service().create(payload)
        output = AdminCreateProviderOutput(
            created=True,
            trace_id=trace_id,
            provider_id=str(doc.id),
            name=doc.name,
            message=f"Proveedor '{doc.name}' creado exitosamente.",
        )
        return output.model_dump(mode="json")

    except ApiError as exc:
        error_code = exc.code
        output = AdminCreateProviderOutput(
            created=False,
            trace_id=trace_id,
            blocking_reasons=[
                ToolBlockingReason(code=exc.code, message=exc.message, details=exc.details or {})
            ],
        )
        return output.model_dump(mode="json")

    except Exception as exc:
        error_code = "tool.unhandled_error"
        output = AdminCreateProviderOutput(
            created=False,
            trace_id=trace_id,
            blocking_reasons=[ToolBlockingReason(code=error_code, message=str(exc))],
        )
        return output.model_dump(mode="json")

    finally:
        await _log(
            trace_id=trace_id,
            conversation_turn_id=conversation_turn_id,
            tool_name="admin_create_provider",
            input_data={k: v for k, v in kwargs.items() if k not in {"trace_id", "conversation_turn_id"}},
            output=output.model_dump(mode="json") if output else None,
            error_code=error_code,
            started=started,
        )


async def admin_update_provider(
    provider_id: str,
    trace_id: str | None = None,
    conversation_turn_id: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    trace_id = trace_id or str(uuid4())
    started = time.perf_counter()
    error_code: str | None = None
    output: AdminUpdateProviderOutput | None = None

    try:
        filtered = {k: v for k, v in kwargs.items() if k in ProviderUpdateSchema.model_fields}
        payload = ProviderUpdateSchema.model_validate(filtered)
        doc = await _get_service().update(provider_id, payload)
        output = AdminUpdateProviderOutput(
            updated=True,
            trace_id=trace_id,
            provider_id=str(doc.id),
            name=doc.name,
            message=f"Proveedor '{doc.name}' actualizado exitosamente.",
        )
        return output.model_dump(mode="json")

    except ApiError as exc:
        error_code = exc.code
        output = AdminUpdateProviderOutput(
            updated=False,
            trace_id=trace_id,
            blocking_reasons=[
                ToolBlockingReason(code=exc.code, message=exc.message, details=exc.details or {})
            ],
        )
        return output.model_dump(mode="json")

    except Exception as exc:
        error_code = "tool.unhandled_error"
        output = AdminUpdateProviderOutput(
            updated=False,
            trace_id=trace_id,
            blocking_reasons=[ToolBlockingReason(code=error_code, message=str(exc))],
        )
        return output.model_dump(mode="json")

    finally:
        await _log(
            trace_id=trace_id,
            conversation_turn_id=conversation_turn_id,
            tool_name="admin_update_provider",
            input_data={"provider_id": provider_id, **{k: v for k, v in kwargs.items() if k in ProviderUpdateSchema.model_fields}},
            output=output.model_dump(mode="json") if output else None,
            error_code=error_code,
            started=started,
        )


async def admin_deactivate_provider(
    provider_id: str | None = None,
    trace_id: str | None = None,
    conversation_turn_id: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    trace_id = trace_id or str(uuid4())
    started = time.perf_counter()
    error_code: str | None = None
    output: AdminDeactivateProviderOutput | None = None

    try:
        if not provider_id and kwargs.get("q"):
            resolution = await _get_service().resolve_provider_reference(str(kwargs["q"]))
            if resolution.get("status") == "resolved":
                provider_id = str(resolution.get("provider_id"))
            elif resolution.get("matches"):
                matches = resolution.get("matches", [])
                message = (
                    f"Encontré estas coincidencias para proveedor '{resolution.get('reference', kwargs['q'])}': "
                    f"{_format_provider_matches(matches)}. Indícame el provider_id exacto o copia una de estas opciones."
                )
                output = AdminDeactivateProviderOutput(
                    deactivated=False,
                    trace_id=trace_id,
                    blocking_reasons=[
                        ToolBlockingReason(
                            code="provider.reference_ambiguous",
                            message=message,
                            details={"matches": matches},
                        )
                    ],
                )
                return output.model_dump(mode="json")
            else:
                message = (
                    f"No encontré coincidencias para proveedor '{resolution.get('reference', kwargs['q'])}'. "
                    "Indícame el provider_id exacto o el nombre/slug exacto."
                )
                output = AdminDeactivateProviderOutput(
                    deactivated=False,
                    trace_id=trace_id,
                    blocking_reasons=[
                        ToolBlockingReason(code="provider.reference_not_found", message=message)
                    ],
                )
                return output.model_dump(mode="json")

        if not provider_id:
            output = AdminDeactivateProviderOutput(
                deactivated=False,
                trace_id=trace_id,
                blocking_reasons=[
                    ToolBlockingReason(
                        code="provider.id_required",
                        message="El campo provider_id es obligatorio.",
                    )
                ],
            )
            return output.model_dump(mode="json")

        doc = await _get_service().get(provider_id)
        name = doc.name
        await _get_service().delete(provider_id)
        output = AdminDeactivateProviderOutput(
            deactivated=True,
            trace_id=trace_id,
            provider_id=provider_id,
            name=name,
            message=f"Proveedor '{name}' desactivado exitosamente.",
        )
        return output.model_dump(mode="json")

    except ApiError as exc:
        error_code = exc.code
        output = AdminDeactivateProviderOutput(
            deactivated=False,
            trace_id=trace_id,
            blocking_reasons=[
                ToolBlockingReason(code=exc.code, message=exc.message, details=exc.details or {})
            ],
        )
        return output.model_dump(mode="json")

    except Exception as exc:
        error_code = "tool.unhandled_error"
        output = AdminDeactivateProviderOutput(
            deactivated=False,
            trace_id=trace_id,
            blocking_reasons=[ToolBlockingReason(code=error_code, message=str(exc))],
        )
        return output.model_dump(mode="json")

    finally:
        await _log(
            trace_id=trace_id,
            conversation_turn_id=conversation_turn_id,
            tool_name="admin_deactivate_provider",
            input_data={"provider_id": provider_id, "q": kwargs.get("q")},
            output=output.model_dump(mode="json") if output else None,
            error_code=error_code,
            started=started,
        )
