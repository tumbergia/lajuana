from datetime import UTC, date, datetime
from zoneinfo import ZoneInfo

APP_TIMEZONE_NAME = "America/Bogota"
APP_TIMEZONE = ZoneInfo(APP_TIMEZONE_NAME)


def now_utc() -> datetime:
    return datetime.now(UTC)


def now_colombia() -> datetime:
    return now_utc().astimezone(APP_TIMEZONE)


def today_colombia() -> date:
    return now_colombia().date()


def today_colombia_iso() -> str:
    return today_colombia().isoformat()


_DAYS_ES = [
    "lunes",
    "martes",
    "miércoles",
    "jueves",
    "viernes",
    "sábado",
    "domingo",
]

_MONTHS_ES = [
    "enero",
    "febrero",
    "marzo",
    "abril",
    "mayo",
    "junio",
    "julio",
    "agosto",
    "septiembre",
    "octubre",
    "noviembre",
    "diciembre",
]


def format_colombia_today_es() -> str:
    now = now_colombia()
    weekday = _DAYS_ES[now.weekday()].capitalize()
    month = _MONTHS_ES[now.month - 1]
    return f"{weekday} {now.day} de {month} de {now.year}"
