import re
from dataclasses import dataclass
from datetime import date

MONTHS_ES = {
    "enero": 1,
    "febrero": 2,
    "marzo": 3,
    "abril": 4,
    "mayo": 5,
    "junio": 6,
    "julio": 7,
    "agosto": 8,
    "septiembre": 9,
    "setiembre": 9,
    "octubre": 10,
    "noviembre": 11,
    "diciembre": 12,
}


@dataclass(frozen=True)
class DetectedIntent:
    name: str
    requires_tool: bool
    tool_name: str | None
    requested_date: date | None
    participant_count: int | None
    experience_query: str | None


def _parse_iso_date(text: str) -> date | None:
    match = re.search(r"\b(20\d{2})-(\d{2})-(\d{2})\b", text)
    if not match:
        return None
    year, month, day = map(int, match.groups())
    try:
        return date(year, month, day)
    except ValueError:
        return None


def _parse_spanish_date(text: str) -> date | None:
    pattern = r"\b(\d{1,2})\s+de\s+([a-záéíóúñ]+)(?:\s+de\s+(20\d{2}))?\b"
    match = re.search(pattern, text.lower())
    if not match:
        return None

    day_raw, month_raw, year_raw = match.groups()
    month = MONTHS_ES.get(month_raw)
    if not month:
        return None

    year = int(year_raw) if year_raw else date.today().year
    try:
        return date(year, month, int(day_raw))
    except ValueError:
        return None


def _parse_participant_count(text: str) -> int | None:
    patterns = [
        r"\bpara\s+(\d{1,2})\s+(?:personas|participantes|clientes)\b",
        r"\b(\d{1,2})\s+(?:personas|participantes|clientes)\b",
        r"\bsomos\s+(\d{1,2})\b",
    ]

    for pattern in patterns:
        match = re.search(pattern, text.lower())
        if match:
            value = int(match.group(1))
            if 1 <= value <= 30:
                return value

    return None


def _parse_experience_query(text: str) -> str | None:
    lowered = text.lower()

    candidates = [
        "medio día",
        "medio dia",
        "un día",
        "un dia",
        "varios días",
        "varios dias",
        "café",
        "cafe",
        "mula",
        "mulas",
        "recorrido",
        "experiencia",
    ]

    hits = [candidate for candidate in candidates if candidate in lowered]
    if not hits:
        return None

    return " ".join(hits)


def detect_intent(message: str) -> DetectedIntent:
    lowered = message.lower().strip()

    requested_date = _parse_iso_date(lowered) or _parse_spanish_date(lowered)
    participant_count = _parse_participant_count(lowered)
    experience_query = _parse_experience_query(lowered)

    availability_terms = [
        "disponible",
        "disponibilidad",
        "hay cupo",
        "cupos",
        "reservar",
        "reserva",
        "cotizar",
        "cotización",
        "cotizacion",
        "quiero ir",
        "quiero una experiencia",
    ]

    if any(term in lowered for term in availability_terms):
        return DetectedIntent(
            name="availability_check",
            requires_tool=bool(requested_date and participant_count),
            tool_name="check_experience_availability",
            requested_date=requested_date,
            participant_count=participant_count,
            experience_query=experience_query,
        )

    return DetectedIntent(
        name="general_message",
        requires_tool=False,
        tool_name=None,
        requested_date=None,
        participant_count=None,
        experience_query=None,
    )
