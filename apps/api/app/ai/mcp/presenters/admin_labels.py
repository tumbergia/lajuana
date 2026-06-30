"""Human-readable labels for admin MCP tool outputs."""

from __future__ import annotations

import datetime

from app.common.enums import PaymentStatus, ReservationStatus

_RESERVATION_STATUS_LABELS: dict[ReservationStatus, str] = {
    ReservationStatus.CONTACT: "Contacto",
    ReservationStatus.QUOTED: "Cotizado",
    ReservationStatus.PRE_RESERVED: "Pre-reserva",
    ReservationStatus.PENDING_PAYMENT: "Pago pendiente",
    ReservationStatus.PAYMENT_RECEIVED: "Pago recibido",
    ReservationStatus.CONFIRMED: "Confirmada",
    ReservationStatus.CANCELLED: "Cancelada",
    ReservationStatus.COMPLETED: "Completada",
    ReservationStatus.EXPIRED: "Expirada",
}

_PAYMENT_STATUS_LABELS: dict[PaymentStatus, str] = {
    PaymentStatus.PENDING: "Pendiente",
    PaymentStatus.RECEIVED: "Recibido",
    PaymentStatus.VERIFIED: "Verificado",
    PaymentStatus.REJECTED: "Rechazado",
}

_MONTHS_ES = (
    "ene",
    "feb",
    "mar",
    "abr",
    "may",
    "jun",
    "jul",
    "ago",
    "sep",
    "oct",
    "nov",
    "dic",
)


def reservation_status_label_es(status: str | ReservationStatus | None) -> str:
    if status is None:
        return "Sin estado"
    if isinstance(status, ReservationStatus):
        return _RESERVATION_STATUS_LABELS.get(status, status.value)
    try:
        parsed = ReservationStatus(status)
    except ValueError:
        return str(status).replace("_", " ")
    return _RESERVATION_STATUS_LABELS.get(parsed, parsed.value)


def payment_status_label_es(status: str | PaymentStatus | None) -> str:
    if status is None or status == "":
        return "Sin informacion"
    if isinstance(status, PaymentStatus):
        return _PAYMENT_STATUS_LABELS.get(status, status.value)
    try:
        parsed = PaymentStatus(status)
    except ValueError:
        return str(status).replace("_", " ")
    return _PAYMENT_STATUS_LABELS.get(parsed, parsed.value)


def format_date_es(value: datetime.date | datetime.datetime | str | None) -> str:
    if value is None:
        return "Sin fecha"
    if isinstance(value, str):
        raw = value.split("T", 1)[0].split(" ", 1)[0]
        try:
            parsed = datetime.date.fromisoformat(raw)
        except ValueError:
            return value
        value = parsed
    if isinstance(value, datetime.datetime):
        value = value.date()
    month = _MONTHS_ES[value.month - 1]
    return f"{value.day} {month} {value.year}"


def list_summary_es(*, total: int, singular: str, plural: str) -> str:
    if total == 0:
        return f"No se encontraron {plural}."
    if total == 1:
        return f"1 {singular} encontrado."
    return f"{total} {plural} encontrados."
