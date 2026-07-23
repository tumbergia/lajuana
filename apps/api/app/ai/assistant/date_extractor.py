from __future__ import annotations

import re
from datetime import date, timedelta

from app.core.time import now_colombia

MESES = {
    "enero": 1,
    "febrero": 2,
    "marzo": 3,
    "abril": 4,
    "mayo": 5,
    "junio": 6,
    "julio": 7,
    "agosto": 8,
    "septiembre": 9,
    "octubre": 10,
    "noviembre": 11,
    "diciembre": 12,
}

MESES_ABR = {
    "ene": 1,
    "feb": 2,
    "mar": 3,
    "abr": 4,
    "may": 5,
    "jun": 6,
    "jul": 7,
    "ago": 8,
    "sep": 9,
    "oct": 10,
    "nov": 11,
    "dic": 12,
}
MESES_ABR.update({f"{k}.": v for k, v in list(MESES_ABR.items())})

ENGLISH_MONTHS = {
    "january": 1,
    "february": 2,
    "march": 3,
    "april": 4,
    "may": 5,
    "june": 6,
    "july": 7,
    "august": 8,
    "september": 9,
    "october": 10,
    "november": 11,
    "december": 12,
}

ENGLISH_MONTHS_ABR = {
    "jan": 1,
    "feb": 2,
    "mar": 3,
    "apr": 4,
    "may": 5,
    "jun": 6,
    "jul": 7,
    "aug": 8,
    "sep": 9,
    "sept": 9,
    "oct": 10,
    "nov": 11,
    "dec": 12,
}
ENGLISH_MONTHS_ABR.update({f"{k}.": v for k, v in list(ENGLISH_MONTHS_ABR.items())})

# Variantes y errores tipográficos comunes que el usuario mete al escribir rápido.
# Mapeo a clave canónica.
MONTH_TYPOS = {
    "agust": "august",
    "agost": "august",
    "augus": "august",
    "setiembre": "september",
    "septiem": "september",
    "diciem": "december",
    "ener": "january",
    "febr": "february",
    "marz": "march",
    "abri": "april",
    "jul": "july",
    "juni": "june",
    "octu": "october",
    "novi": "november",
}


def extract_date_from_message(message: str) -> str | None:
    normalized = message.lower().strip()
    today = now_colombia().date()
    current_year = today.year

    # Aplica correcciones de typos a meses antes de las regex
    for typo, correct in MONTH_TYPOS.items():
        normalized = re.sub(rf"\b{typo}\b", correct, normalized, flags=re.IGNORECASE)

    patterns = [
        # "20 de junio de 2026" / "20 of agust of 2026"
        r"(?:del?\s+)?(\d{1,2})\s+(?:de|of)\s+([a-záéíóúñ]+)\s+(?:de|of)\s+(\d{4})",
        # "20 junio 2026" / "20 august 2026"
        r"(?:del?\s+)?(\d{1,2})\s+([a-záéíóúñ]+)\s+(\d{4})",
        # "20/06/2026" o "20-06-2026"
        r"(\d{1,2})[/-](\d{1,2})[/-](\d{4})",
        # "2026-06-20" (ya iso)
        r"(\d{4})-(\d{2})-(\d{2})",
        # "5 de agosto" / "5 of august" (sin año)
        r"(?:del?\s+)?(\d{1,2})\s+(?:de|of)\s+([a-záéíóúñ]+)(?:\s+(?:de|of)\s+(\d{4}))?",
        # "5 agosto" / "5 august" / "5 agust" (typo corregido arriba)
        r"(?:del?\s+)?(\d{1,2})\s+([a-záéíóúñ]+)(?:\s+(\d{4}))?",
        # English: "august 5" / "august 5, 2026" / "aug 5"
        r"([a-z]+)\.?\s+(\d{1,2})(?:,?\s+(\d{4}))?",
    ]

    for pattern in patterns:
        for match in re.finditer(pattern, normalized):
            groups = match.groups()
            try:
                if pattern == patterns[3]:
                    a, b, c = int(groups[1]), int(groups[2]), int(groups[0])
                    return date(c, a, b).isoformat()

                if pattern in (patterns[0], patterns[1]):
                    day, month_str, year = int(groups[0]), groups[1], int(groups[2])
                    month = MESES.get(month_str) or MESES_ABR.get(month_str)
                    if month is None:
                        continue
                    return date(year, month, day).isoformat()

                if pattern == patterns[2]:
                    a, b, c = int(groups[0]), int(groups[1]), int(groups[2])
                    for day, month, year in [(a, b, c), (b, a, c)]:
                        if month > 12:
                            continue
                        try:
                            return date(year, month, day).isoformat()
                        except ValueError:
                            continue
                    continue

                if pattern in (patterns[4], patterns[5]):
                    day = int(groups[0])
                    month_str = groups[1]
                    year = int(groups[2]) if groups[2] else current_year
                    month = (
                        MESES.get(month_str)
                        or MESES_ABR.get(month_str)
                        or ENGLISH_MONTHS.get(month_str)
                        or ENGLISH_MONTHS_ABR.get(month_str)
                    )
                    if month is None:
                        continue
                    try:
                        candidate = date(year, month, day)
                    except ValueError:
                        continue
                    if candidate < today:
                        candidate = date(year + 1, month, day)
                    return candidate.isoformat()

                if pattern == patterns[6]:
                    month_str = groups[0]
                    day = int(groups[1])
                    year = int(groups[2]) if groups[2] else current_year
                    month = (
                        MESES.get(month_str)
                        or MESES_ABR.get(month_str)
                        or ENGLISH_MONTHS.get(month_str)
                        or ENGLISH_MONTHS_ABR.get(month_str)
                    )
                    if month is None:
                        continue
                    try:
                        candidate = date(year, month, day)
                    except ValueError:
                        continue
                    if candidate < today:
                        candidate = date(year + 1, month, day)
                    return candidate.isoformat()
            except (ValueError, KeyError):
                continue

    return None


def extract_date_range_from_message(message: str) -> tuple[str, str] | None:
    """Extrae un rango date_from/date_to (ISO) para frases relativas en Colombia."""
    normalized = message.lower().strip()
    today = now_colombia().date()

    # "desde el 14 de febrero hasta hoy" / "del 14 de febrero al 20 de marzo"
    range_match = re.search(
        r"(?:desde|del)\s+(.+?)\s+(?:hasta|al)\s+(.+)$",
        normalized,
    )
    if range_match:
        start_raw = range_match.group(1).strip()
        end_raw = range_match.group(2).strip()
        start = _parse_flexible_date(start_raw, today)
        end = _parse_flexible_date(end_raw, today)
        if start and end:
            if end < start:
                start, end = end, start
            return start.isoformat(), end.isoformat()

    # "desde el 4 de mayo de este año" / "desde el 14 de febrero" → hasta hoy
    desde_only = re.search(r"\bdesde\s+(.+)$", normalized)
    if desde_only and not re.search(r"\bhasta\b", normalized):
        start = _parse_flexible_date(desde_only.group(1).strip(), today)
        if start:
            return start.isoformat(), today.isoformat()

    if re.search(r"\besta\s+semana\b|\b(semana\s+actual)\b", normalized):
        start = today - timedelta(days=today.weekday())
        end = start + timedelta(days=6)
        return start.isoformat(), end.isoformat()

    if re.search(r"\b(este\s+mes|mes\s+actual)\b", normalized):
        start = today.replace(day=1)
        return start.isoformat(), today.isoformat()

    if re.search(r"\b(ultimos?|últimos?)\s+30\s+dias?\b", normalized):
        start = today - timedelta(days=29)
        return start.isoformat(), today.isoformat()

    # Bare "hoy" / "mañana" only when they are the whole time reference
    # (not part of "desde X hasta hoy").
    if re.search(r"\bhoy\b", normalized) and not re.search(r"\b(desde|hasta)\b", normalized):
        if not extract_date_from_message(normalized):
            iso = today.isoformat()
            return iso, iso

    if re.search(r"\bmanana\b|\bmañana\b", normalized) and not re.search(
        r"\b(desde|hasta)\b", normalized
    ):
        d = today + timedelta(days=1)
        iso = d.isoformat()
        return iso, iso

    single = extract_date_from_message(message)
    if single:
        return single, single

    return None


def _parse_flexible_date(raw: str, today: date) -> date | None:
    """Parse 'hoy', '14 de febrero', '14 de febrero de este año', ISO, etc."""
    token = raw.strip().lower()
    if token in {"hoy", "actualmente"}:
        return today
    if token in {"manana", "mañana"}:
        return today + timedelta(days=1)

    force_current_year = bool(
        re.search(r"\b(este\s+año|este\s+ano|año\s+actual|ano\s+actual)\b", token)
    )
    token = re.sub(
        r"\s+de\s+(este\s+año|este\s+ano|año\s+actual|ano\s+actual)\b",
        "",
        token,
    ).strip()

    # "14 de febrero" / "14 febrero" without year → current year (or previous if future).
    m = re.search(
        r"(?:del?\s+)?(\d{1,2})\s+(?:de\s+)?([a-záéíóúñ]+)(?:\s+de\s+(\d{4}))?",
        token,
    )
    if m:
        day = int(m.group(1))
        month = MESES.get(m.group(2)) or MESES_ABR.get(m.group(2))
        if month is None:
            return None
        year = int(m.group(3)) if m.group(3) else today.year
        try:
            parsed = date(year, month, day)
        except ValueError:
            return None
        if m.group(3) is None and not force_current_year and parsed > today:
            try:
                parsed = date(year - 1, month, day)
            except ValueError:
                return None
        return parsed

    iso = extract_date_from_message(token)
    if iso:
        return date.fromisoformat(iso)
    return None
