"""Admin tools for payment proof lifecycle management."""

from __future__ import annotations

import time
from typing import Any
from uuid import uuid4

from app.ai.mcp.tool_contracts import (
    AdminApprovePaymentOutput,
    AdminGetPaymentProofOutput,
    AdminRejectPaymentProofOutput,
    AdminUnrejectPaymentProofOutput,
    AdminUnverifyPaymentProofOutput,
    ToolBlockingReason,
)
from app.common.enums import UserRole
from app.core.errors import ApiError
from app.documents import PaymentProofDocument, ReservationDocument
from app.schemas.payment_proof import (
    PaymentProofApproveSchema,
    PaymentProofRejectSchema,
    PaymentProofUnrejectSchema,
    PaymentProofUnverifySchema,
    PaymentProofVerifySchema,
)
from app.services.payment_proof_service import PaymentProofService


def _get_service() -> PaymentProofService:
    from app.core.di import Container
    return Container.get_instance().payment_proof_service


def _safe_str(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


async def admin_get_payment_proof(
    payment_proof_id: str | None = None,
    reservation_id: str | None = None,
    trace_id: str | None = None,
    conversation_turn_id: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    started = time.perf_counter()
    trace_id = trace_id or str(uuid4())
    error_code: str | None = None
    output: AdminGetPaymentProofOutput | None = None

    try:
        proof = None
        if payment_proof_id:
            proof = await PaymentProofDocument.get(payment_proof_id)
        elif reservation_id:
            # Get the latest proof for this reservation
            proofs = await PaymentProofDocument.find(
                {"reservation_id": reservation_id}
            ).to_list()
            if proofs:
                proof = max(proofs, key=lambda p: p.uploaded_at)
        else:
            output = AdminGetPaymentProofOutput(
                trace_id=trace_id,
                found=False,
                blocking_reasons=[
                    ToolBlockingReason(
                        code="payment_proof.id_required",
                        message="Se requiere payment_proof_id o reservation_id.",
                    )
                ],
            )
            return output.model_dump(mode="json")

        if proof is None:
            output = AdminGetPaymentProofOutput(
                trace_id=trace_id,
                found=False,
                blocking_reasons=[
                    ToolBlockingReason(
                        code="payment_proof.not_found",
                        message="Comprobante no encontrado.",
                    )
                ],
            )
            return output.model_dump(mode="json")

        reservation = await ReservationDocument.get(proof.reservation_id)
        reservation_code = reservation.code if reservation else None

        output = AdminGetPaymentProofOutput(
            trace_id=trace_id,
            found=True,
            payment_proof_id=_safe_str(proof.id),
            reservation_id=_safe_str(proof.reservation_id),
            reservation_code=reservation_code,
            filename=proof.filename,
            content_type=proof.content_type,
            size_bytes=proof.size_bytes,
            status=str(proof.status.value) if proof.status else None,
            uploaded_at=proof.uploaded_at.isoformat() if proof.uploaded_at else None,
        )
        return output.model_dump(mode="json")

    except Exception as exc:
        error_code = "tool.unhandled_error"
        output = AdminGetPaymentProofOutput(
            trace_id=trace_id,
            found=False,
            blocking_reasons=[ToolBlockingReason(code=error_code, message=str(exc))],
        )
        return output.model_dump(mode="json")

    finally:
        from app.documents.tool_call_log_document import ToolCallLogDocument

        latency_ms = int((time.perf_counter() - started) * 1000)
        await ToolCallLogDocument(
            trace_id=trace_id,
            conversation_turn_id=conversation_turn_id,
            tool_name="admin_get_payment_proof",
            input={
                "payment_proof_id": payment_proof_id,
                "reservation_id": reservation_id,
            },
            output=output.model_dump(mode="json") if output else {},
            status="error" if error_code else "success",
            error_code=error_code,
            latency_ms=latency_ms,
        ).insert()


async def admin_approve_payment(
    payment_proof_id: str,
    note: str | None = None,
    trace_id: str | None = None,
    conversation_turn_id: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    started = time.perf_counter()
    trace_id = trace_id or str(uuid4())
    error_code: str | None = None
    output: AdminApprovePaymentOutput | None = None

    try:
        payload = PaymentProofApproveSchema(
            confirmation_token="APPROVE_PAYMENT",
            note=note,
        )
        doc = await _get_service().approve_payment(
            payment_proof_id=payment_proof_id,
            payload=payload,
            actor_id=None,
            actor_role=UserRole.ADMIN,
        )

        output = AdminApprovePaymentOutput(
            trace_id=trace_id,
            approved=True,
            payment_proof_id=_safe_str(doc.id),
            new_status=str(doc.status.value) if doc.status else None,
            message="Comprobante aprobado. Reserva actualizada a pago recibido.",
        )
        return output.model_dump(mode="json")

    except ApiError as exc:
        error_code = exc.code
        output = AdminApprovePaymentOutput(
            trace_id=trace_id,
            approved=False,
            blocking_reasons=[
                ToolBlockingReason(code=exc.code, message=exc.message, details=exc.details or {})
            ],
        )
        return output.model_dump(mode="json")

    except Exception as exc:
        error_code = "tool.unhandled_error"
        output = AdminApprovePaymentOutput(
            trace_id=trace_id,
            approved=False,
            blocking_reasons=[ToolBlockingReason(code=error_code, message=str(exc))],
        )
        return output.model_dump(mode="json")

    finally:
        from app.documents.tool_call_log_document import ToolCallLogDocument

        latency_ms = int((time.perf_counter() - started) * 1000)
        await ToolCallLogDocument(
            trace_id=trace_id,
            conversation_turn_id=conversation_turn_id,
            tool_name="admin_approve_payment",
            input={"payment_proof_id": payment_proof_id, "note": note},
            output=output.model_dump(mode="json") if output else {},
            status="error" if error_code else "success",
            error_code=error_code,
            latency_ms=latency_ms,
        ).insert()


async def admin_reject_payment_proof(
    payment_proof_id: str,
    reason: str,
    trace_id: str | None = None,
    conversation_turn_id: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    started = time.perf_counter()
    trace_id = trace_id or str(uuid4())
    error_code: str | None = None
    output: AdminRejectPaymentProofOutput | None = None

    try:
        payload = PaymentProofRejectSchema(
            confirmation_token="REJECT_PAYMENT",
            reason=reason,
        )
        doc = await _get_service().reject_payment(
            payment_proof_id=payment_proof_id,
            payload=payload,
            actor_id=None,
            actor_role=UserRole.ADMIN,
        )

        output = AdminRejectPaymentProofOutput(
            trace_id=trace_id,
            rejected=True,
            payment_proof_id=_safe_str(doc.id),
            new_status=str(doc.status.value) if doc.status else None,
            message=f"Comprobante rechazado. Motivo: {reason}",
        )
        return output.model_dump(mode="json")

    except ApiError as exc:
        error_code = exc.code
        output = AdminRejectPaymentProofOutput(
            trace_id=trace_id,
            rejected=False,
            blocking_reasons=[
                ToolBlockingReason(code=exc.code, message=exc.message, details=exc.details or {})
            ],
        )
        return output.model_dump(mode="json")

    except Exception as exc:
        error_code = "tool.unhandled_error"
        output = AdminRejectPaymentProofOutput(
            trace_id=trace_id,
            rejected=False,
            blocking_reasons=[ToolBlockingReason(code=error_code, message=str(exc))],
        )
        return output.model_dump(mode="json")

    finally:
        from app.documents.tool_call_log_document import ToolCallLogDocument

        latency_ms = int((time.perf_counter() - started) * 1000)
        await ToolCallLogDocument(
            trace_id=trace_id,
            conversation_turn_id=conversation_turn_id,
            tool_name="admin_reject_payment_proof",
            input={"payment_proof_id": payment_proof_id, "reason": reason},
            output=output.model_dump(mode="json") if output else {},
            status="error" if error_code else "success",
            error_code=error_code,
            latency_ms=latency_ms,
        ).insert()


async def admin_unverify_payment_proof(
    payment_proof_id: str,
    note: str | None = None,
    trace_id: str | None = None,
    conversation_turn_id: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    started = time.perf_counter()
    trace_id = trace_id or str(uuid4())
    error_code: str | None = None
    output: AdminUnverifyPaymentProofOutput | None = None

    try:
        payload = PaymentProofUnverifySchema(
            confirmation_token="UNVERIFY_PAYMENT",
            note=note,
        )
        doc = await _get_service().unverify_payment(
            payment_proof_id=payment_proof_id,
            payload=payload,
            actor_id=None,
            actor_role=UserRole.ADMIN,
        )

        output = AdminUnverifyPaymentProofOutput(
            trace_id=trace_id,
            unverified=True,
            payment_proof_id=_safe_str(doc.id),
            new_status=str(doc.status.value) if doc.status else None,
            message="Verificación de comprobante deshecha.",
        )
        return output.model_dump(mode="json")

    except ApiError as exc:
        error_code = exc.code
        output = AdminUnverifyPaymentProofOutput(
            trace_id=trace_id,
            unverified=False,
            blocking_reasons=[
                ToolBlockingReason(code=exc.code, message=exc.message, details=exc.details or {})
            ],
        )
        return output.model_dump(mode="json")

    except Exception as exc:
        error_code = "tool.unhandled_error"
        output = AdminUnverifyPaymentProofOutput(
            trace_id=trace_id,
            unverified=False,
            blocking_reasons=[ToolBlockingReason(code=error_code, message=str(exc))],
        )
        return output.model_dump(mode="json")

    finally:
        from app.documents.tool_call_log_document import ToolCallLogDocument

        latency_ms = int((time.perf_counter() - started) * 1000)
        await ToolCallLogDocument(
            trace_id=trace_id,
            conversation_turn_id=conversation_turn_id,
            tool_name="admin_unverify_payment_proof",
            input={"payment_proof_id": payment_proof_id, "note": note},
            output=output.model_dump(mode="json") if output else {},
            status="error" if error_code else "success",
            error_code=error_code,
            latency_ms=latency_ms,
        ).insert()


async def admin_unreject_payment_proof(
    payment_proof_id: str,
    note: str | None = None,
    trace_id: str | None = None,
    conversation_turn_id: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    started = time.perf_counter()
    trace_id = trace_id or str(uuid4())
    error_code: str | None = None
    output: AdminUnrejectPaymentProofOutput | None = None

    try:
        payload = PaymentProofUnrejectSchema(
            confirmation_token="UNREJECT_PAYMENT",
            note=note,
        )
        doc = await _get_service().unreject_payment(
            payment_proof_id=payment_proof_id,
            payload=payload,
            actor_id=None,
            actor_role=UserRole.ADMIN,
        )

        output = AdminUnrejectPaymentProofOutput(
            trace_id=trace_id,
            unrejected=True,
            payment_proof_id=_safe_str(doc.id),
            new_status=str(doc.status.value) if doc.status else None,
            message="Rechazo de comprobante deshecho.",
        )
        return output.model_dump(mode="json")

    except ApiError as exc:
        error_code = exc.code
        output = AdminUnrejectPaymentProofOutput(
            trace_id=trace_id,
            unrejected=False,
            blocking_reasons=[
                ToolBlockingReason(code=exc.code, message=exc.message, details=exc.details or {})
            ],
        )
        return output.model_dump(mode="json")

    except Exception as exc:
        error_code = "tool.unhandled_error"
        output = AdminUnrejectPaymentProofOutput(
            trace_id=trace_id,
            unrejected=False,
            blocking_reasons=[ToolBlockingReason(code=error_code, message=str(exc))],
        )
        return output.model_dump(mode="json")

    finally:
        from app.documents.tool_call_log_document import ToolCallLogDocument

        latency_ms = int((time.perf_counter() - started) * 1000)
        await ToolCallLogDocument(
            trace_id=trace_id,
            conversation_turn_id=conversation_turn_id,
            tool_name="admin_unreject_payment_proof",
            input={"payment_proof_id": payment_proof_id, "note": note},
            output=output.model_dump(mode="json") if output else {},
            status="error" if error_code else "success",
            error_code=error_code,
            latency_ms=latency_ms,
        ).insert()
