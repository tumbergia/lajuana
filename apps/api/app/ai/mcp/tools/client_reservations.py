from __future__ import annotations

import time
from typing import Any
from uuid import uuid4

from app.ai.language.messages import t as _t
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
from app.core.errors import ApiError
from app.documents import ReservationDocument
from app.documents.tool_call_log_document import ToolCallLogDocument
from app.core.di import Container


async def cancel_reservation(**kwargs: Any) -> dict[str, Any]:
    trace_id = kwargs.pop("trace_id", None) or str(uuid4())
    conversation_turn_id = kwargs.pop("conversation_turn_id", None)
    language: str = kwargs.pop("language", "es")
    started = time.perf_counter()

    payload: CancelReservationInput | None = None
    output: CancelReservationOutput | None = None
    error_code: str | None = None

    try:
        filtered = {
            k: v for k, v in kwargs.items() if k in CancelReservationInput.model_fields
        }
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
                        message=_t("client_reservation_not_found", language),
                    )
                ],
            )
            return output.model_dump(mode="json")

        if reservation.payment_status != PaymentStatus.PENDING:
            output = CancelReservationOutput(
                cancelled=False,
                trace_id=trace_id,
                reservation_code=reservation.code,
                message=_t("client_reservation_cannot_cancel_paid", language),
                response=_t("client_reservation_cannot_cancel_paid_response", language),
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
            message=_t("client_reservation_cancelled_success", language),
            response=_t("client_reservation_cancelled_response", language, code=doc.code),
        )
        return output.model_dump(mode="json")

    except ApiError as exc:
        error_code = exc.code
        output = CancelReservationOutput(
            cancelled=False,
            trace_id=trace_id,
            message=exc.message,
            response=_t("client_reservation_unable_to_cancel", language),
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
            response=_t("client_reservation_unexpected_error", language),
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
    language: str = kwargs.pop("language", "es")
    started = time.perf_counter()

    payload: UpdateReservationDateInput | None = None
    output: UpdateReservationDateOutput | None = None
    error_code: str | None = None

    try:
        filtered = {
            k: v for k, v in kwargs.items() if k in UpdateReservationDateInput.model_fields
        }
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
                        message=_t("client_reservation_not_found", language),
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
                message=_t("client_reservation_terminal_state", language),
                response=_t("client_reservation_terminal_state_response", language),
            )
            return output.model_dump(mode="json")

        if reservation.payment_status != PaymentStatus.PENDING:
            output = UpdateReservationDateOutput(
                updated=False,
                trace_id=trace_id,
                reservation_code=reservation.code,
                message=_t("client_reservation_cannot_modify_paid", language),
                response=_t("client_reservation_cannot_modify_paid_response", language),
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
            message=_t("client_reservation_date_updated_short", language),
            response=_t(
                "client_reservation_date_updated_response", language,
                code=reservation.code, new_date=payload.new_date.isoformat(),
            ),
        )
        return output.model_dump(mode="json")

    except ApiError as exc:
        error_code = exc.code
        output = UpdateReservationDateOutput(
            updated=False,
            trace_id=trace_id,
            message=exc.message,
            response=_t("client_reservation_date_unable", language),
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
            response=_t("client_reservation_unexpected_error", language),
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
    language: str = kwargs.pop("language", "es")
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
                        message=_t("client_reservation_not_found", language),
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
                message=_t("client_reservation_terminal_state", language),
                response=_t("client_reservation_terminal_state_response", language),
            )
            return output.model_dump(mode="json")

        if reservation.payment_status != PaymentStatus.PENDING:
            output = UpdateReservationParticipantsOutput(
                updated=False,
                trace_id=trace_id,
                reservation_code=reservation.code,
                message=_t("client_reservation_cannot_modify_paid", language),
                response=_t("client_reservation_cannot_modify_paid_response", language),
            )
            return output.model_dump(mode="json")

        reservation.participant_count = payload.new_participant_count
        await reservation.save()

        output = UpdateReservationParticipantsOutput(
            updated=True,
            trace_id=trace_id,
            reservation_code=reservation.code,
            new_participant_count=payload.new_participant_count,
            message=_t("client_reservation_participants_updated_short", language),
            response=_t(
                "client_reservation_participants_updated_response", language,
                code=reservation.code, count=payload.new_participant_count,
            ),
        )
        return output.model_dump(mode="json")

    except ApiError as exc:
        error_code = exc.code
        output = UpdateReservationParticipantsOutput(
            updated=False,
            trace_id=trace_id,
            message=exc.message,
            response=_t("client_reservation_participants_unable", language),
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
            response=_t("client_reservation_unexpected_error", language),
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
