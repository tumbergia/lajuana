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


def extract_date_from_message(message: str) -> str | None:
    normalized = message.lower().strip()

    patterns = [
        # "20 de junio de 2026"
        r"(?:del?\s+)?(\d{1,2})\s+de\s+([a-záéíóúñ]+)\s+de\s+(\d{4})",
        # "20 junio 2026"
        r"(?:del?\s+)?(\d{1,2})\s+([a-záéíóúñ]+)\s+(\d{4})",
        # "20/06/2026" o "20-06-2026"
        r"(\d{1,2})[/-](\d{1,2})[/-](\d{4})",
        # "2026-06-20" (ya iso)
        r"(\d{4})-(\d{2})-(\d{2})",
    ]

    for pattern in patterns:
        match = re.search(pattern, normalized)
        if match:
            groups = match.groups()
            if pattern == patterns[3]:
                a, b, c = int(groups[1]), int(groups[2]), int(groups[0])
                try:
                    return date(c, a, b).isoformat()
                except ValueError:
                    continue

            if pattern in (patterns[0], patterns[1]):
                day, month_str, year = int(groups[0]), groups[1], int(groups[2])
                month = MESES.get(month_str) or MESES_ABR.get(month_str)
                if month is None:
                    continue
                try:
                    return date(year, month, day).isoformat()
                except ValueError:
                    continue

            if pattern == patterns[2]:
                a, b, c = int(groups[0]), int(groups[1]), int(groups[2])
                for day, month, year in [(a, b, c), (b, a, c)]:
                    if month > 12:
                        continue
                    try:
                        return date(year, month, day).isoformat()
                    except ValueError:
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
    if re.search(r"\bhoy\b", normalized) and not re.search(
        r"\b(desde|hasta)\b", normalized
    ):
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
