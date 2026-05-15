from __future__ import annotations

import re
from datetime import date

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
