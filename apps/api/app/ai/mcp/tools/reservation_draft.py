from __future__ import annotations

import time
from typing import Any
from uuid import uuid4

from app.ai.mcp.tool_contracts import (
    AttachPaymentProofToReservationInput,
    AttachPaymentProofToReservationOutput,
    CreateReservationDraftInput,
    CreateReservationDraftOutput,
    GetReservationPublicSummaryInput,
    GetReservationPublicSummaryOutput,
    GetReservationStatusByPhoneInput,
    GetReservationStatusByPhoneOutput,
    ToolBlockingReason,
)
from app.core.di import Container
from app.core.errors import ApiError
from app.documents import ReservationDocument
from app.documents.reservation_document import ACTIVE_RESERVATION_STATUSES
from app.documents.tool_call_log_document import ToolCallLogDocument
from app.services.payment_proof_service import ALLOWED_CONTENT_TYPES, PaymentProofService


def _format_currency(amount: Any, currency: str) -> str:
    if isinstance(amount, int | float):
        return f"${amount:,.0f} {currency}".replace(",", ".")
    return f"No disponible ({currency})"


def _build_pre_reservation_response(
    *,
    code: str,
    expire_at: Any,
    requested_date: Any,
    participant_count: int,
    quote_snapshot: dict[str, Any],
    payment_instructions: Any,
) -> str:
    experience = (
        quote_snapshot.get("experience_name")
        or quote_snapshot.get("experience_id")
        or "No disponible"
    )
    subtotal = quote_snapshot.get("subtotal")
    currency = quote_snapshot.get("currency", "COP")

    return (
        "Pre-reserva registrada.\n\n"
        "Resumen:\n"
        f"- Experiencia: {experience}\n"
        f"- Fecha: {requested_date}\n"
        f"- Personas: {participant_count}\n"
        f"- Valor: {_format_currency(subtotal, currency)}\n"
        f"- Codigo: {code}\n"
        f"- Vence: {expire_at}\n\n"
        "Instrucciones de pago:\n"
        f"- Banco: {payment_instructions.account_bank}\n"
        f"- Tipo de cuenta: {payment_instructions.account_type}\n"
        f"- Numero de cuenta: {payment_instructions.account_number}\n"
        f"- Titular: {payment_instructions.account_holder_name}\n"
        f"- Identificacion: {payment_instructions.account_holder_id}\n"
        f"- Nota: {payment_instructions.transfer_note}\n\n"
        "Importante: esta pre-reserva no esta confirmada. "
        "Solo queda confirmada cuando un administrador verifica el pago "
        "y revalida la disponibilidad."
    )


def _public_payment_stage(status: str) -> str:
    if status == "payment_received":
        return "payment_received"
    if status == "pending_payment":
        return "pending_payment"
    return "unknown"


async def create_reservation_draft(**kwargs: Any) -> dict[str, Any]:
    trace_id = kwargs.pop("trace_id", None) or str(uuid4())
    conversation_turn_id = kwargs.pop("conversation_turn_id", None)
    started = time.perf_counter()

    payload: CreateReservationDraftInput | None = None
    output: CreateReservationDraftOutput | None = None
    error_code: str | None = None

    try:
        filtered = {
            k: v for k, v in kwargs.items() if k in CreateReservationDraftInput.model_fields
        }
        payload = CreateReservationDraftInput.model_validate(filtered)

        container = Container.get_instance()
        service = container.reservation_draft_service
        config_service = container.config_service
        result = await service.create_reservation_draft(
            experience_id=payload.experience_id,
            schedule_id=payload.schedule_id,
            participant_count=payload.participant_count,
            holder_phone=payload.holder_phone,
            holder_name=payload.holder_name,
            holder_email=payload.holder_email,
            requested_date=str(payload.requested_date),
            quote_snapshot=payload.quote_snapshot,
            conversation_id=payload.conversation_id,
            trace_id=trace_id,
        )
        payment_instructions = await config_service.get_payment_instructions()

        output = CreateReservationDraftOutput(
            created=True,
            code=result.get("code"),
            status=result.get("status", ""),
            expire_at=result.get("expire_at"),
            message=result.get("message", ""),
            response=_build_pre_reservation_response(
                code=result.get("code", ""),
                expire_at=result.get("expire_at", ""),
                requested_date=payload.requested_date,
                participant_count=payload.participant_count,
                quote_snapshot=payload.quote_snapshot,
                payment_instructions=payment_instructions,
            ),
        )
        return output.model_dump(mode="json")

    except Exception as exc:
        error_code = "tool.unhandled_error"
        output = CreateReservationDraftOutput(
            created=False,
            message=str(exc),
            blocking_reasons=[
                ToolBlockingReason(
                    code=error_code,
                    message=str(exc),
                )
            ],
        )
        return output.model_dump(mode="json")

    finally:
        latency_ms = int((time.perf_counter() - started) * 1000)
        await ToolCallLogDocument(
            trace_id=trace_id,
            conversation_turn_id=conversation_turn_id,
            tool_name="create_reservation_draft",
            input=payload.model_dump(mode="json") if payload else {},
            output=output.model_dump(mode="json") if output else {},
            status="error" if error_code else "success",
            error_code=error_code,
            latency_ms=latency_ms,
        ).insert()


async def get_reservation_public_summary(**kwargs: Any) -> dict[str, Any]:
    trace_id = kwargs.pop("trace_id", None) or str(uuid4())
    conversation_turn_id = kwargs.pop("conversation_turn_id", None)
    started = time.perf_counter()

    payload: GetReservationPublicSummaryInput | None = None
    output: GetReservationPublicSummaryOutput | None = None
    error_code: str | None = None

    try:
        filtered = {
            k: v for k, v in kwargs.items() if k in GetReservationPublicSummaryInput.model_fields
        }
        payload = GetReservationPublicSummaryInput.model_validate(filtered)

        reservation = await ReservationDocument.find_one(
            {"code": payload.code, "holder_phone": payload.holder_phone}
        )

        if reservation is None:
            output = GetReservationPublicSummaryOutput(
                found=False,
                blocking_reasons=[
                    ToolBlockingReason(
                        code="reservation.not_found",
                        message="No se encontró una pre-reserva con ese código.",
                    )
                ],
            )
            return output.model_dump(mode="json")

        output = GetReservationPublicSummaryOutput(
            found=True,
            code=reservation.code,
            status=reservation.status.value
            if hasattr(reservation.status, "value")
            else str(reservation.status),
            expire_at=reservation.expire_at.isoformat() if reservation.expire_at else None,
            participant_count=reservation.participant_count,
        )
        return output.model_dump(mode="json")

    except Exception as exc:
        error_code = "tool.unhandled_error"
        output = GetReservationPublicSummaryOutput(
            found=False,
            blocking_reasons=[
                ToolBlockingReason(
                    code=error_code,
                    message=str(exc),
                )
            ],
        )
        return output.model_dump(mode="json")

    finally:
        latency_ms = int((time.perf_counter() - started) * 1000)
        await ToolCallLogDocument(
            trace_id=trace_id,
            conversation_turn_id=conversation_turn_id,
            tool_name="get_reservation_public_summary",
            input=payload.model_dump(mode="json") if payload else {},
            output=output.model_dump(mode="json") if output else {},
            status="error" if error_code else "success",
            error_code=error_code,
            latency_ms=latency_ms,
        ).insert()


async def get_reservation_status_by_phone(**kwargs: Any) -> dict[str, Any]:
    trace_id = kwargs.pop("trace_id", None) or str(uuid4())
    conversation_turn_id = kwargs.pop("conversation_turn_id", None)
    started = time.perf_counter()

    payload: GetReservationStatusByPhoneInput | None = None
    output: GetReservationStatusByPhoneOutput | None = None
    error_code: str | None = None

    try:
        filtered = {
            k: v for k, v in kwargs.items() if k in GetReservationStatusByPhoneInput.model_fields
        }
        payload = GetReservationStatusByPhoneInput.model_validate(filtered)

        reservations = await ReservationDocument.find(
            {"holder_phone": payload.holder_phone}
        ).to_list()
        if not reservations:
            output = GetReservationStatusByPhoneOutput(
                found=False,
                blocking_reasons=[
                    ToolBlockingReason(
                        code="reservation.not_found",
                        message="No se encontró una reserva para ese teléfono.",
                    )
                ],
            )
            return output.model_dump(mode="json")

        active_statuses = set(ACTIVE_RESERVATION_STATUSES + ["pre_reserved"])
        active_reservations = [
            reservation
            for reservation in reservations
            if (
                reservation.status.value
                if hasattr(reservation.status, "value")
                else str(reservation.status)
            )
            in active_statuses
        ]

        candidates = active_reservations if active_reservations else reservations
        reservation = max(
            candidates,
            key=lambda item: (
                getattr(item, "updated_at", None) or getattr(item, "created_at", None),
                getattr(item, "created_at", None),
            ),
        )

        output = GetReservationStatusByPhoneOutput(
            found=True,
            code=reservation.code,
            status=reservation.status.value
            if hasattr(reservation.status, "value")
            else str(reservation.status),
            expire_at=reservation.expire_at.isoformat() if reservation.expire_at else None,
            participant_count=reservation.participant_count,
        )
        return output.model_dump(mode="json")

    except Exception as exc:
        error_code = "tool.unhandled_error"
        output = GetReservationStatusByPhoneOutput(
            found=False,
            blocking_reasons=[
                ToolBlockingReason(
                    code=error_code,
                    message=str(exc),
                )
            ],
        )
        return output.model_dump(mode="json")

    finally:
        latency_ms = int((time.perf_counter() - started) * 1000)
        await ToolCallLogDocument(
            trace_id=trace_id,
            conversation_turn_id=conversation_turn_id,
            tool_name="get_reservation_status_by_phone",
            input=payload.model_dump(mode="json") if payload else {},
            output=output.model_dump(mode="json") if output else {},
            status="error" if error_code else "success",
            error_code=error_code,
            latency_ms=latency_ms,
        ).insert()


async def attach_payment_proof_to_reservation(**kwargs: Any) -> dict[str, Any]:
    trace_id = kwargs.pop("trace_id", None) or str(uuid4())
    conversation_turn_id = kwargs.pop("conversation_turn_id", None)
    started = time.perf_counter()

    payload: AttachPaymentProofToReservationInput | None = None
    output: AttachPaymentProofToReservationOutput | None = None
    error_code: str | None = None

    try:
        filtered = {
            k: v
            for k, v in kwargs.items()
            if k in AttachPaymentProofToReservationInput.model_fields
        }
        payload = AttachPaymentProofToReservationInput.model_validate(filtered)

        normalized_mime = payload.media_mime_type.strip().lower()
        if normalized_mime not in ALLOWED_CONTENT_TYPES:
            output = AttachPaymentProofToReservationOutput(
                attached=False,
                trace_id=trace_id,
                proof_status="rejected",
                message="El comprobante debe ser imagen (JPG/PNG) o PDF.",
                response=(
                    "Recibi tu archivo, pero el formato no es valido. "
                    "Por favor envia una imagen (JPG/PNG) o PDF del comprobante."
                ),
                blocking_reasons=[
                    ToolBlockingReason(
                        code="payment_proof.invalid_content_type",
                        message="Tipo de contenido no permitido.",
                        details={"media_mime_type": payload.media_mime_type},
                    )
                ],
            )
            return output.model_dump(mode="json")

        service = Container.get_instance().payment_proof_service
        reservation = await service.get_attachable_reservation(
            reservation_id=payload.reservation_id,
            public_reservation_code=payload.public_reservation_code,
            from_phone=payload.from_phone,
        )

        existing = await service.find_existing_by_whatsapp_message(
            reservation_id=reservation.id,
            whatsapp_message_id=payload.whatsapp_message_id,
        )
        if existing is None:
            existing = await service.find_existing_by_hash(
                reservation_id=reservation.id,
                media_id=payload.media_id,
            )

        if existing is not None:
            output = AttachPaymentProofToReservationOutput(
                attached=True,
                idempotent=True,
                trace_id=trace_id,
                reservation_code=reservation.code,
                reservation_status=_public_payment_stage(reservation.status.value),
                proof_status="duplicate",
                message="Comprobante ya recibido anteriormente; se mantiene en revision.",
                response=(
                    f"Ya teniamos tu comprobante para la reserva {reservation.code}. "
                    "Sigue en revision administrativa y la reserva aun no esta confirmada."
                ),
            )
            return output.model_dump(mode="json")

        now_id = payload.whatsapp_message_id
        storage_key = f"whatsapp/{payload.media_id}"
        filename = payload.filename or f"wa-proof-{now_id}"

        doc = await service.create_metadata_only(
            reservation=reservation,
            storage_key=storage_key,
            filename=filename,
            content_type=normalized_mime,
            media_id=payload.media_id,
        )
        reservation = await ReservationDocument.get(reservation.id)
        reservation_status = "unknown"
        if reservation is not None:
            reservation_status = _public_payment_stage(reservation.status.value)

        output = AttachPaymentProofToReservationOutput(
            attached=doc is not None,
            idempotent=False,
            trace_id=trace_id,
            reservation_code=reservation.code,
            reservation_status=reservation_status,
            proof_status="under_review",
            message="Comprobante recibido y en revision administrativa.",
            response=(
                f"Recibimos tu comprobante para la reserva {reservation.code}. "
                "Queda en revision administrativa y la reserva aun NO esta confirmada."
            ),
        )
        return output.model_dump(mode="json")

    except ApiError as exc:
        error_code = exc.code
        output = AttachPaymentProofToReservationOutput(
            attached=False,
            trace_id=trace_id,
            message=exc.message,
            response=(
                "No pude asociar el comprobante. Verifica el codigo de reserva y que este "
                "aun este pendiente de confirmacion."
            ),
            blocking_reasons=[
                ToolBlockingReason(
                    code=exc.code,
                    message=exc.message,
                    details=exc.details or {},
                )
            ],
        )
        return output.model_dump(mode="json")

    except Exception as exc:
        error_code = "tool.unhandled_error"
        output = AttachPaymentProofToReservationOutput(
            attached=False,
            trace_id=trace_id,
            message=str(exc),
            response=(
                "No logramos registrar el comprobante en este momento. "
                "Intenta de nuevo o comparte el codigo de tu reserva."
            ),
            blocking_reasons=[
                ToolBlockingReason(
                    code=error_code,
                    message=str(exc),
                )
            ],
        )
        return output.model_dump(mode="json")

    finally:
        latency_ms = int((time.perf_counter() - started) * 1000)
        await ToolCallLogDocument(
            trace_id=trace_id,
            conversation_turn_id=conversation_turn_id,
            tool_name="attach_payment_proof_to_reservation",
            input=payload.model_dump(mode="json") if payload else {},
            output=output.model_dump(mode="json") if output else {},
            status="error" if error_code else "success",
            error_code=error_code,
            latency_ms=latency_ms,
        ).insert()
