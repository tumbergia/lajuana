"""Admin tools for system configuration."""

from __future__ import annotations

import time
from typing import Any
from uuid import uuid4

from app.ai.mcp.tool_contracts import (
    AdminEmergencyContactItem,
    AdminGetEmergencyContactsOutput,
    AdminGetPaymentInstructionsOutput,
    AdminGetSystemConfigOutput,
    AdminUpdateReservationRulesOutput,
    ToolBlockingReason,
)
from app.core.errors import ApiError
from app.schemas.config import ReservationRulesUpdateSchema
from app.services.config_service import ConfigService


def _get_service() -> ConfigService:
    from app.core.di import Container

    return Container.get_instance().config_service


async def admin_get_system_config(**kwargs: Any) -> dict[str, Any]:
    trace_id = kwargs.get("trace_id") or str(uuid4())
    conversation_turn_id = kwargs.get("conversation_turn_id")
    started = time.perf_counter()
    error_code: str | None = None
    output: AdminGetSystemConfigOutput | None = None

    try:
        rules = await _get_service().get_reservation_rules()
        payment = await _get_service().get_payment_instructions()

        output = AdminGetSystemConfigOutput(
            trace_id=trace_id,
            min_days_in_advance=rules.min_days_in_advance,
            require_payment_proof_for_confirmation=rules.require_payment_proof_for_confirmation,
            reservation_draft_ttl_minutes=rules.reservation_draft_ttl_minutes,
            account_bank=payment.account_bank,
            account_type=payment.account_type,
            account_number=payment.account_number,
            account_holder_name=payment.account_holder_name,
            transfer_note=payment.transfer_note,
        )
        return output.model_dump(mode="json")

    except Exception as exc:
        error_code = "tool.unhandled_error"
        output = AdminGetSystemConfigOutput(
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
            tool_name="admin_get_system_config",
            input={},
            output=output.model_dump(mode="json") if output else {},
            status="error" if error_code else "success",
            error_code=error_code,
            latency_ms=latency_ms,
        ).insert()


async def admin_update_reservation_rules(**kwargs: Any) -> dict[str, Any]:
    trace_id = kwargs.get("trace_id") or str(uuid4())
    conversation_turn_id = kwargs.get("conversation_turn_id")
    started = time.perf_counter()
    error_code: str | None = None
    output: AdminUpdateReservationRulesOutput | None = None

    try:
        filtered = {
            k: v
            for k, v in kwargs.items()
            if k in ReservationRulesUpdateSchema.model_fields and v is not None
        }
        payload = ReservationRulesUpdateSchema.model_validate(filtered)
        doc = await _get_service().update_reservation_rules(payload)

        output = AdminUpdateReservationRulesOutput(
            updated=True,
            trace_id=trace_id,
            min_days_in_advance=doc.min_days_in_advance,
            require_payment_proof_for_confirmation=doc.require_payment_proof_for_confirmation,
            reservation_draft_ttl_minutes=doc.reservation_draft_ttl_minutes,
            message="Reglas de reserva actualizadas exitosamente.",
        )
        return output.model_dump(mode="json")

    except ApiError as exc:
        error_code = exc.code
        output = AdminUpdateReservationRulesOutput(
            updated=False,
            trace_id=trace_id,
            blocking_reasons=[
                ToolBlockingReason(code=exc.code, message=exc.message, details=exc.details or {})
            ],
        )
        return output.model_dump(mode="json")

    except Exception as exc:
        error_code = "tool.unhandled_error"
        output = AdminUpdateReservationRulesOutput(
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
            tool_name="admin_update_reservation_rules",
            input={
                k: v for k, v in kwargs.items() if k not in {"trace_id", "conversation_turn_id"}
            },
            output=output.model_dump(mode="json") if output else {},
            status="error" if error_code else "success",
            error_code=error_code,
            latency_ms=latency_ms,
        ).insert()


async def admin_get_payment_instructions(**kwargs: Any) -> dict[str, Any]:
    trace_id = kwargs.get("trace_id") or str(uuid4())
    conversation_turn_id = kwargs.get("conversation_turn_id")
    started = time.perf_counter()
    error_code: str | None = None
    output: AdminGetPaymentInstructionsOutput | None = None

    try:
        payment = await _get_service().get_payment_instructions()

        output = AdminGetPaymentInstructionsOutput(
            trace_id=trace_id,
            account_bank=payment.account_bank,
            account_type=payment.account_type,
            account_number=payment.account_number,
            account_holder_name=payment.account_holder_name,
            account_holder_id=payment.account_holder_id,
            transfer_note=payment.transfer_note,
        )
        return output.model_dump(mode="json")

    except Exception as exc:
        error_code = "tool.unhandled_error"
        output = AdminGetPaymentInstructionsOutput(
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
            tool_name="admin_get_payment_instructions",
            input={},
            output=output.model_dump(mode="json") if output else {},
            status="error" if error_code else "success",
            error_code=error_code,
            latency_ms=latency_ms,
        ).insert()


async def admin_get_emergency_contacts(**kwargs: Any) -> dict[str, Any]:
    trace_id = kwargs.get("trace_id") or str(uuid4())
    conversation_turn_id = kwargs.get("conversation_turn_id")
    started = time.perf_counter()
    error_code: str | None = None
    output: AdminGetEmergencyContactsOutput | None = None

    try:
        catalog = await _get_service().get_emergency_contacts()
        items = [
            AdminEmergencyContactItem(
                code=item.code,
                name=item.name,
                description=item.description,
                phone_number=item.phone_number,
                category=item.category,
                is_primary=item.is_primary,
                is_national=item.is_national,
            )
            for item in catalog.items
        ]
        output = AdminGetEmergencyContactsOutput(
            trace_id=trace_id,
            total=len(items),
            contacts=items,
        )
        return output.model_dump(mode="json")

    except Exception as exc:
        error_code = "tool.unhandled_error"
        output = AdminGetEmergencyContactsOutput(
            trace_id=trace_id,
            total=0,
            blocking_reasons=[ToolBlockingReason(code=error_code, message=str(exc))],
        )
        return output.model_dump(mode="json")

    finally:
        from app.documents.tool_call_log_document import ToolCallLogDocument

        latency_ms = int((time.perf_counter() - started) * 1000)
        await ToolCallLogDocument(
            trace_id=trace_id,
            conversation_turn_id=conversation_turn_id,
            tool_name="admin_get_emergency_contacts",
            input={},
            output=output.model_dump(mode="json") if output else {},
            status="error" if error_code else "success",
            error_code=error_code,
            latency_ms=latency_ms,
        ).insert()
