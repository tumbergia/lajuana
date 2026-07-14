"""Normalize free-text country values to ISO 3166-1 alpha-2.

Does not invent codes. Unresolved values are reported, original text preserved.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field


@dataclass(frozen=True)
class CountryNormalizationResult:
    original: str
    country_code: str | None
    country_name: str | None
    resolved: bool


@dataclass
class NormalizationReport:
    total: int = 0
    resolved: int = 0
    unresolved: int = 0
    unresolved_values: list[str] = field(default_factory=list)

    def add(self, result: CountryNormalizationResult) -> None:
        self.total += 1
        if result.resolved:
            self.resolved += 1
        else:
            self.unresolved += 1
            if result.original and result.original not in self.unresolved_values:
                self.unresolved_values.append(result.original)


# Canonical name (Spanish display) by ISO code.
_ISO_NAMES: dict[str, str] = {
    "CO": "Colombia",
    "US": "Estados Unidos",
    "CA": "Canadá",
    "MX": "México",
    "ES": "España",
    "AR": "Argentina",
    "CL": "Chile",
    "PE": "Perú",
    "EC": "Ecuador",
    "BR": "Brasil",
    "VE": "Venezuela",
    "PA": "Panamá",
    "CR": "Costa Rica",
    "DE": "Alemania",
    "FR": "Francia",
    "IT": "Italia",
    "GB": "Reino Unido",
    "NL": "Países Bajos",
    "BE": "Bélgica",
    "CH": "Suiza",
    "AU": "Australia",
    "NZ": "Nueva Zelanda",
    "JP": "Japón",
    "KR": "Corea del Sur",
    "CN": "China",
    "IN": "India",
    "UY": "Uruguay",
    "PY": "Paraguay",
    "BO": "Bolivia",
    "GT": "Guatemala",
    "HN": "Honduras",
    "SV": "El Salvador",
    "NI": "Nicaragua",
    "DO": "República Dominicana",
    "CU": "Cuba",
    "PR": "Puerto Rico",
    "PT": "Portugal",
    "IE": "Irlanda",
    "AT": "Austria",
    "SE": "Suecia",
    "NO": "Noruega",
    "DK": "Dinamarca",
    "FI": "Finlandia",
    "PL": "Polonia",
    "CZ": "Chequia",
    "IL": "Israel",
    "ZA": "Sudáfrica",
}


def _strip_accents(value: str) -> str:
    nfkd = unicodedata.normalize("NFKD", value)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def _normalize_key(value: str) -> str:
    cleaned = _strip_accents(value).lower().strip()
    cleaned = re.sub(r"[^\w\s]", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


# Aliases → ISO code. Keys must be normalized via _normalize_key.
_ALIASES: dict[str, str] = {
    "colombia": "CO",
    "colombiano": "CO",
    "colombiana": "CO",
    "co": "CO",
    "estados unidos": "US",
    "eeuu": "US",
    "ee uu": "US",
    "usa": "US",
    "u s a": "US",
    "united states": "US",
    "united states of america": "US",
    "america": "US",
    "us": "US",
    "canada": "CA",
    "canadá": "CA",
    "mexico": "MX",
    "méxico": "MX",
    "espana": "ES",
    "españa": "ES",
    "spain": "ES",
    "argentina": "AR",
    "chile": "CL",
    "peru": "PE",
    "perú": "PE",
    "ecuador": "EC",
    "brasil": "BR",
    "brazil": "BR",
    "venezuela": "VE",
    "panama": "PA",
    "panamá": "PA",
    "costa rica": "CR",
    "alemania": "DE",
    "germany": "DE",
    "francia": "FR",
    "france": "FR",
    "italia": "IT",
    "italy": "IT",
    "reino unido": "GB",
    "united kingdom": "GB",
    "uk": "GB",
    "gran bretana": "GB",
    "inglaterra": "GB",
    "england": "GB",
    "paises bajos": "NL",
    "holanda": "NL",
    "netherlands": "NL",
    "belgica": "BE",
    "belgium": "BE",
    "suiza": "CH",
    "switzerland": "CH",
    "australia": "AU",
    "nueva zelanda": "NZ",
    "new zealand": "NZ",
    "japon": "JP",
    "japan": "JP",
    "corea del sur": "KR",
    "south korea": "KR",
    "china": "CN",
    "india": "IN",
    "uruguay": "UY",
    "paraguay": "PY",
    "bolivia": "BO",
    "guatemala": "GT",
    "honduras": "HN",
    "el salvador": "SV",
    "nicaragua": "NI",
    "republica dominicana": "DO",
    "dominican republic": "DO",
    "cuba": "CU",
    "puerto rico": "PR",
    "portugal": "PT",
    "irlanda": "IE",
    "ireland": "IE",
    "austria": "AT",
    "suecia": "SE",
    "sweden": "SE",
    "noruega": "NO",
    "norway": "NO",
    "dinamarca": "DK",
    "denmark": "DK",
    "finlandia": "FI",
    "finland": "FI",
    "polonia": "PL",
    "poland": "PL",
    "chequia": "CZ",
    "republica checa": "CZ",
    "israel": "IL",
    "sudafrica": "ZA",
    "south africa": "ZA",
}

# Rebuild alias keys without accents for lookup consistency.
_ALIASES_NORM = {_normalize_key(k): v for k, v in _ALIASES.items()}


class AnalyticsCountryNormalizer:
    """Server-owned country normalization. Never invents ISO codes."""

    def normalize(self, raw: str | None) -> CountryNormalizationResult:
        original = (raw or "").strip()
        if not original:
            return CountryNormalizationResult(
                original=original,
                country_code=None,
                country_name=None,
                resolved=False,
            )

        key = _normalize_key(original)

        # Already an ISO alpha-2?
        if len(key) == 2 and key.upper() in _ISO_NAMES:
            code = key.upper()
            return CountryNormalizationResult(
                original=original,
                country_code=code,
                country_name=_ISO_NAMES[code],
                resolved=True,
            )

        code = _ALIASES_NORM.get(key)
        if code and code in _ISO_NAMES:
            return CountryNormalizationResult(
                original=original,
                country_code=code,
                country_name=_ISO_NAMES[code],
                resolved=True,
            )

        return CountryNormalizationResult(
            original=original,
            country_code=None,
            country_name=None,
            resolved=False,
        )

    def normalize_many(self, values: list[str | None]) -> tuple[
        list[CountryNormalizationResult], NormalizationReport
    ]:
        report = NormalizationReport()
        results: list[CountryNormalizationResult] = []
        for value in values:
            result = self.normalize(value)
            report.add(result)
            results.append(result)
        return results, report

    @staticmethod
    def display_name(code: str | None, fallback: str | None = None) -> str:
        if code and code in _ISO_NAMES:
            return _ISO_NAMES[code]
        if fallback and fallback.strip():
            return fallback.strip()
        return "País sin especificar"
