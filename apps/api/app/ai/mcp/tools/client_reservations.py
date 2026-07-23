from __future__ import annotations

import time
from typing import Any
from uuid import uuid4

from app.ai.mcp.tool_contracts import (
    CancelReservationInput,
    CancelReservationOutput,
    ToolBlockingReason,
    UpdateReservationDateInput,
    UpdateReservationDateOutput,
    UpdateReservationParticipantsInput,
    UpdateReservationParticipantsOutput,
)
from app.common.enums import PaymentStatus, ReservationStatus
from app.core.di import Container
from app.core.errors import ApiError
from app.documents import ReservationDocument
from app.documents.tool_call_log_document import ToolCallLogDocument


async def cancel_reservation(**kwargs: Any) -> dict[str, Any]:
    trace_id = kwargs.pop("trace_id", None) or str(uuid4())
    conversation_turn_id = kwargs.pop("conversation_turn_id", None)
    started = time.perf_counter()

    payload: CancelReservationInput | None = None
    output: CancelReservationOutput | None = None
    error_code: str | None = None

    try:
        filtered = {k: v for k, v in kwargs.items() if k in CancelReservationInput.model_fields}
        payload = CancelReservationInput.model_validate(filtered)

        reservation = await ReservationDocument.find_one(
            {"code": payload.reservation_code, "holder_phone": payload.holder_phone}
        )
        if reservation is None:
            output = CancelReservationOutput(
                cancelled=False,
                trace_id=trace_id,
                blocking_reasons=[
                    ToolBlockingReason(
                        code="reservation.not_found",
                        message="No encontré una reserva con ese código y teléfono.",
                    )
                ],
            )
            return output.model_dump(mode="json")

        if reservation.payment_status != PaymentStatus.PENDING:
            output = CancelReservationOutput(
                cancelled=False,
                trace_id=trace_id,
                reservation_code=reservation.code,
                message="Solo se pueden cancelar reservas con pago pendiente.",
                response=(
                    "Lo siento, solo puedo cancelar reservas que aún no tienen pago registrado. "
                    "Si necesitas ayuda con esta reserva, te transfiero con un asesor."
                ),
            )
            return output.model_dump(mode="json")

        service = Container.get_instance().reservation_service
        doc = await service.cancel_reservation(
            str(reservation.id),
            actor_id=None,
            notify_client=False,
        )

        output = CancelReservationOutput(
            cancelled=True,
            trace_id=trace_id,
            reservation_code=doc.code,
            message="Reserva cancelada exitosamente.",
            response=(
                f"Listo, tu reserva {doc.code} ha sido cancelada. "
                "Si en algún momento quieres reprogramar, escríbeme y con gusto te ayudo."
            ),
        )
        return output.model_dump(mode="json")

    except ApiError as exc:
        error_code = exc.code
        output = CancelReservationOutput(
            cancelled=False,
            trace_id=trace_id,
            message=exc.message,
            response="No pude cancelar la reserva en este momento. Intenta de nuevo.",
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
        output = CancelReservationOutput(
            cancelled=False,
            trace_id=trace_id,
            message=str(exc),
            response="Ocurrió un error inesperado. Intenta de nuevo en unos minutos.",
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
            tool_name="cancel_reservation",
            input=payload.model_dump(mode="json") if payload else {},
            output=output.model_dump(mode="json") if output else {},
            status="error" if error_code else "success",
            error_code=error_code,
            latency_ms=latency_ms,
        ).insert()


async def update_reservation_date(**kwargs: Any) -> dict[str, Any]:
    trace_id = kwargs.pop("trace_id", None) or str(uuid4())
    conversation_turn_id = kwargs.pop("conversation_turn_id", None)
    started = time.perf_counter()

    payload: UpdateReservationDateInput | None = None
    output: UpdateReservationDateOutput | None = None
    error_code: str | None = None

    try:
        filtered = {k: v for k, v in kwargs.items() if k in UpdateReservationDateInput.model_fields}
        payload = UpdateReservationDateInput.model_validate(filtered)

        reservation = await ReservationDocument.find_one(
            {"code": payload.reservation_code, "holder_phone": payload.holder_phone}
        )
        if reservation is None:
            output = UpdateReservationDateOutput(
                updated=False,
                trace_id=trace_id,
                blocking_reasons=[
                    ToolBlockingReason(
                        code="reservation.not_found",
                        message="No encontré una reserva con ese código y teléfono.",
                    )
                ],
            )
            return output.model_dump(mode="json")

        if reservation.status in {
            ReservationStatus.CANCELLED,
            ReservationStatus.COMPLETED,
            ReservationStatus.EXPIRED,
        }:
            output = UpdateReservationDateOutput(
                updated=False,
                trace_id=trace_id,
                reservation_code=reservation.code,
                message="No se puede modificar una reserva en estado terminal.",
                response=(
                    "Lo siento, esta reserva ya no puede modificarse porque está finalizada o cancelada."
                ),
            )
            return output.model_dump(mode="json")

        if reservation.payment_status != PaymentStatus.PENDING:
            output = UpdateReservationDateOutput(
                updated=False,
                trace_id=trace_id,
                reservation_code=reservation.code,
                message="Solo se pueden modificar reservas con pago pendiente.",
                response=(
                    "Lo siento, solo puedo modificar reservas que aún no tienen pago registrado. "
                    "Si necesitas cambiar una reserva con pago confirmado, te transfiero con un asesor."
                ),
            )
            return output.model_dump(mode="json")

        service = Container.get_instance().reservation_service
        await service.ensure_date_available(
            payload.new_date,
            exclude_reservation_id=str(reservation.id),
        )

        reservation.requested_date = payload.new_date
        await service._sync_day_lock_fields(reservation)
        await reservation.save()

        output = UpdateReservationDateOutput(
            updated=True,
            trace_id=trace_id,
            reservation_code=reservation.code,
            new_date=payload.new_date,
            message="Fecha actualizada exitosamente.",
            response=(
                f"Perfecto, cambié la fecha de tu reserva {reservation.code} "
                f"para el {payload.new_date.isoformat()}. Todo sigue igual."
            ),
        )
        return output.model_dump(mode="json")

    except ApiError as exc:
        error_code = exc.code
        output = UpdateReservationDateOutput(
            updated=False,
            trace_id=trace_id,
            message=exc.message,
            response="No pude cambiar la fecha en este momento. Intenta de nuevo.",
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
        output = UpdateReservationDateOutput(
            updated=False,
            trace_id=trace_id,
            message=str(exc),
            response="Ocurrió un error inesperado. Intenta de nuevo en unos minutos.",
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
            tool_name="update_reservation_date",
            input=payload.model_dump(mode="json") if payload else {},
            output=output.model_dump(mode="json") if output else {},
            status="error" if error_code else "success",
            error_code=error_code,
            latency_ms=latency_ms,
        ).insert()


async def update_reservation_participants(**kwargs: Any) -> dict[str, Any]:
    trace_id = kwargs.pop("trace_id", None) or str(uuid4())
    conversation_turn_id = kwargs.pop("conversation_turn_id", None)
    started = time.perf_counter()

    payload: UpdateReservationParticipantsInput | None = None
    output: UpdateReservationParticipantsOutput | None = None
    error_code: str | None = None

    try:
        filtered = {
            k: v for k, v in kwargs.items() if k in UpdateReservationParticipantsInput.model_fields
        }
        payload = UpdateReservationParticipantsInput.model_validate(filtered)

        reservation = await ReservationDocument.find_one(
            {"code": payload.reservation_code, "holder_phone": payload.holder_phone}
        )
        if reservation is None:
            output = UpdateReservationParticipantsOutput(
                updated=False,
                trace_id=trace_id,
                blocking_reasons=[
                    ToolBlockingReason(
                        code="reservation.not_found",
                        message="No encontré una reserva con ese código y teléfono.",
                    )
                ],
            )
            return output.model_dump(mode="json")

        if reservation.status in {
            ReservationStatus.CANCELLED,
            ReservationStatus.COMPLETED,
            ReservationStatus.EXPIRED,
        }:
            output = UpdateReservationParticipantsOutput(
                updated=False,
                trace_id=trace_id,
                reservation_code=reservation.code,
                message="No se puede modificar una reserva en estado terminal.",
                response=(
                    "Lo siento, esta reserva ya no puede modificarse porque está finalizada o cancelada."
                ),
            )
            return output.model_dump(mode="json")

        if reservation.payment_status != PaymentStatus.PENDING:
            output = UpdateReservationParticipantsOutput(
                updated=False,
                trace_id=trace_id,
                reservation_code=reservation.code,
                message="Solo se pueden modificar reservas con pago pendiente.",
                response=(
                    "Lo siento, solo puedo modificar reservas que aún no tienen pago registrado. "
                    "Si necesitas cambiar una reserva con pago confirmado, te transfiero con un asesor."
                ),
            )
            return output.model_dump(mode="json")

        reservation.participant_count = payload.new_participant_count
        await reservation.save()

        output = UpdateReservationParticipantsOutput(
            updated=True,
            trace_id=trace_id,
            reservation_code=reservation.code,
            new_participant_count=payload.new_participant_count,
            message="Cantidad de participantes actualizada exitosamente.",
            response=(
                f"Listo, ahora tu reserva {reservation.code} quedó para "
                f"{payload.new_participant_count} participantes."
            ),
        )
        return output.model_dump(mode="json")

    except ApiError as exc:
        error_code = exc.code
        output = UpdateReservationParticipantsOutput(
            updated=False,
            trace_id=trace_id,
            message=exc.message,
            response="No pude cambiar la cantidad de participantes en este momento. Intenta de nuevo.",
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
        output = UpdateReservationParticipantsOutput(
            updated=False,
            trace_id=trace_id,
            message=str(exc),
            response="Ocurrió un error inesperado. Intenta de nuevo en unos minutos.",
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
            tool_name="update_reservation_participants",
            input=payload.model_dump(mode="json") if payload else {},
            output=output.model_dump(mode="json") if output else {},
            status="error" if error_code else "success",
            error_code=error_code,
            latency_ms=latency_ms,
        ).insert()
