from __future__ import annotations

import time
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from app.ai.mcp.tool_contracts import (
    AnniversaryAutomationInput,
    AnniversaryAutomationOutput,
    BirthdayAutomationInput,
    BirthdayAutomationOutput,
    PostServiceMessageInput,
    PostServiceMessageOutput,
    ToolBlockingReason,
)
from app.documents import (
    AppConfigDocument,
    AutomationConfig,
    ReservationDocument,
    ServiceLogDocument,
    ServiceLogEventType,
)
from app.documents.tool_call_log_document import ToolCallLogDocument

AUTOMATION_CONFIG_KEY = "automation"

POST_SERVICE_MESSAGE = (
    "Gracias por visitar La Juana. Esperamos que hayas disfrutado tu experiencia. "
    "Te invitamos a dejarnos una reseña y a volver pronto."
)


def _safe_str(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


async def _get_or_create_automation_config() -> AppConfigDocument:
    config = await AppConfigDocument.find_one(AppConfigDocument.key == AUTOMATION_CONFIG_KEY)
    if config is None:
        config = AppConfigDocument(
            key=AUTOMATION_CONFIG_KEY,
            automation=AutomationConfig(),
        )
        await config.insert()
    elif config.automation is None:
        config.automation = AutomationConfig()
        await config.save()
    return config


async def send_post_service_message(
    reservation_id: str,
    trace_id: str | None = None,
    conversation_turn_id: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    started = time.perf_counter()
    trace_id = trace_id or str(uuid4())

    payload: PostServiceMessageInput | None = None
    output: PostServiceMessageOutput | None = None
    error_code: str | None = None

    try:
        payload = PostServiceMessageInput(reservation_id=reservation_id)

        reservation = await ReservationDocument.get(payload.reservation_id)
        if reservation is None:
            output = PostServiceMessageOutput(
                trace_id=trace_id,
                sent=False,
                message="Reserva no encontrada.",
                blocking_reasons=[
                    ToolBlockingReason(
                        code="reservation.not_found",
                        message="Reserva no encontrada.",
                    )
                ],
            )
            return output.model_dump(mode="json")

        if hasattr(reservation, "status") and str(reservation.status) not in (
            "completed",
            "confirmed",
        ):
            output = PostServiceMessageOutput(
                trace_id=trace_id,
                sent=False,
                message=(
                    "La reserva debe estar completada o confirmada "
                    "para enviar mensaje post-servicio."
                ),
                blocking_reasons=[
                    ToolBlockingReason(
                        code="reservation.invalid_status",
                        message="Estado no apto para post-servicio.",
                    )
                ],
            )
            return output.model_dump(mode="json")

        await ServiceLogDocument(
            reservation_id=reservation.id,
            event_type=ServiceLogEventType.NOTE,
            happened_at=datetime.now(UTC),
            notes=f"[POST-SERVICE] {POST_SERVICE_MESSAGE}",
        ).insert()

        output = PostServiceMessageOutput(
            trace_id=trace_id,
            sent=True,
            message="Mensaje post-servicio registrado correctamente.",
        )
        return output.model_dump(mode="json")

    except Exception as exc:
        error_code = "tool.unhandled_error"
        output = PostServiceMessageOutput(
            trace_id=trace_id,
            sent=False,
            message=str(exc),
            blocking_reasons=[
                ToolBlockingReason(code=error_code, message=str(exc)),
            ],
        )
        return output.model_dump(mode="json")

    finally:
        latency_ms = int((time.perf_counter() - started) * 1000)
        await ToolCallLogDocument(
            trace_id=trace_id,
            conversation_turn_id=conversation_turn_id,
            tool_name="send_post_service_message",
            input=payload.model_dump(mode="json") if payload else {},
            output=output.model_dump(mode="json") if output else {},
            status="error" if error_code else "success",
            error_code=error_code,
            latency_ms=latency_ms,
        ).insert()


async def schedule_birthday_automation(
    enabled: bool | None = None,
    trace_id: str | None = None,
    conversation_turn_id: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    started = time.perf_counter()
    trace_id = trace_id or str(uuid4())

    payload: BirthdayAutomationInput | None = None
    output: BirthdayAutomationOutput | None = None
    error_code: str | None = None

    try:
        payload = BirthdayAutomationInput(enabled=enabled)
        config = await _get_or_create_automation_config()

        if payload.enabled is not None:
            config.automation.birthday_messages_enabled = payload.enabled
            await config.save()

        current = config.automation.birthday_messages_enabled

        output = BirthdayAutomationOutput(
            trace_id=trace_id,
            enabled=current,
            message=(f"Notificaciones de cumpleaños {'activadas' if current else 'desactivadas'}."),
        )
        return output.model_dump(mode="json")

    except Exception as exc:
        error_code = "tool.unhandled_error"
        output = BirthdayAutomationOutput(
            trace_id=trace_id,
            enabled=False,
            message=str(exc),
            blocking_reasons=[
                ToolBlockingReason(code=error_code, message=str(exc)),
            ],
        )
        return output.model_dump(mode="json")

    finally:
        latency_ms = int((time.perf_counter() - started) * 1000)
        await ToolCallLogDocument(
            trace_id=trace_id,
            conversation_turn_id=conversation_turn_id,
            tool_name="schedule_birthday_automation",
            input=payload.model_dump(mode="json") if payload else {},
            output=output.model_dump(mode="json") if output else {},
            status="error" if error_code else "success",
            error_code=error_code,
            latency_ms=latency_ms,
        ).insert()


async def schedule_visit_anniversary_automation(
    enabled: bool | None = None,
    trace_id: str | None = None,
    conversation_turn_id: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    started = time.perf_counter()
    trace_id = trace_id or str(uuid4())

    payload: AnniversaryAutomationInput | None = None
    output: AnniversaryAutomationOutput | None = None
    error_code: str | None = None

    try:
        payload = AnniversaryAutomationInput(enabled=enabled)
        config = await _get_or_create_automation_config()

        if payload.enabled is not None:
            config.automation.anniversary_messages_enabled = payload.enabled
            await config.save()

        current = config.automation.anniversary_messages_enabled

        output = AnniversaryAutomationOutput(
            trace_id=trace_id,
            enabled=current,
            message=(
                f"Notificaciones de aniversario {'activadas' if current else 'desactivadas'}."
            ),
        )
        return output.model_dump(mode="json")

    except Exception as exc:
        error_code = "tool.unhandled_error"
        output = AnniversaryAutomationOutput(
            trace_id=trace_id,
            enabled=False,
            message=str(exc),
            blocking_reasons=[
                ToolBlockingReason(code=error_code, message=str(exc)),
            ],
        )
        return output.model_dump(mode="json")

    finally:
        latency_ms = int((time.perf_counter() - started) * 1000)
        await ToolCallLogDocument(
            trace_id=trace_id,
            conversation_turn_id=conversation_turn_id,
            tool_name="schedule_visit_anniversary_automation",
            input=payload.model_dump(mode="json") if payload else {},
            output=output.model_dump(mode="json") if output else {},
            status="error" if error_code else "success",
            error_code=error_code,
            latency_ms=latency_ms,
        ).insert()
