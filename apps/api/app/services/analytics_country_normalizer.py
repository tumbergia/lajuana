"""Normalize free-text country values to ISO 3166-1 alpha-2.

Catalog aligned with mobile `kPhoneCountries` (phone picker / muted phones).
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


# Canonical Spanish display name by ISO code (same catalog as mobile phone countries).
_ISO_NAMES: dict[str, str] = {
    "AF": "Afganistán",
    "AL": "Albania",
    "DZ": "Argelia",
    "AS": "American Samoa",
    "AD": "Andorra",
    "AO": "Angola",
    "AI": "Anguilla",
    "AG": "Antigua and Barbuda",
    "AR": "Argentina",
    "AM": "Armenia",
    "AW": "Aruba",
    "AU": "Australia",
    "AT": "Austria",
    "AZ": "Azerbaiyán",
    "BS": "Bahamas",
    "BH": "Baréin",
    "BD": "Bangladés",
    "BB": "Barbados",
    "BY": "Bielorrusia",
    "BE": "Bélgica",
    "BZ": "Belize",
    "BJ": "Benín",
    "BM": "Bermuda",
    "BT": "Bután",
    "BO": "Bolivia",
    "BA": "Bosnia y Herzegovina",
    "BW": "Botsuana",
    "BR": "Brasil",
    "BN": "Brunéi",
    "BG": "Bulgaria",
    "BF": "Burkina Faso",
    "BI": "Burundi",
    "KH": "Camboya",
    "CM": "Camerún",
    "CA": "Canadá",
    "CV": "Cabo Verde",
    "KY": "Cayman Islands",
    "CF": "República Centroafricana",
    "TD": "Chad",
    "CL": "Chile",
    "CN": "China",
    "CO": "Colombia",
    "KM": "Comoras",
    "CG": "Congo",
    "CD": "Congo (RDC)",
    "CR": "Costa Rica",
    "CI": "Costa de Marfil",
    "HR": "Croacia",
    "CU": "Cuba",
    "CY": "Chipre",
    "CZ": "Chequia",
    "DK": "Dinamarca",
    "DJ": "Yibuti",
    "DM": "Dominica",
    "DO": "República Dominicana",
    "EC": "Ecuador",
    "EG": "Egipto",
    "SV": "El Salvador",
    "GQ": "Guinea Ecuatorial",
    "ER": "Eritrea",
    "EE": "Estonia",
    "SZ": "Eswatini",
    "ET": "Etiopía",
    "FK": "Falkland Islands",
    "FO": "Faroe Islands",
    "FJ": "Fiyi",
    "FI": "Finlandia",
    "FR": "Francia",
    "GF": "French Guiana",
    "PF": "French Polynesia",
    "GA": "Gabón",
    "GM": "Gambia",
    "GE": "Georgia",
    "DE": "Alemania",
    "GH": "Ghana",
    "GI": "Gibraltar",
    "GR": "Grecia",
    "GL": "Greenland",
    "GD": "Grenada",
    "GP": "Guadeloupe",
    "GU": "Guam",
    "GT": "Guatemala",
    "GN": "Guinea",
    "GW": "Guinea-Bisáu",
    "GY": "Guyana",
    "HT": "Haití",
    "HN": "Honduras",
    "HK": "Hong Kong",
    "HU": "Hungría",
    "IS": "Islandia",
    "IN": "India",
    "ID": "Indonesia",
    "IR": "Irán",
    "IQ": "Irak",
    "IE": "Irlanda",
    "IL": "Israel",
    "IT": "Italia",
    "JM": "Jamaica",
    "JP": "Japón",
    "JO": "Jordania",
    "KZ": "Kazajistán",
    "KE": "Kenia",
    "KI": "Kiribati",
    "KW": "Kuwait",
    "KG": "Kirguistán",
    "LA": "Laos",
    "LV": "Letonia",
    "LB": "Líbano",
    "LS": "Lesoto",
    "LR": "Liberia",
    "LY": "Libia",
    "LI": "Liechtenstein",
    "LT": "Lituania",
    "LU": "Luxemburgo",
    "MO": "Macao",
    "MG": "Madagascar",
    "MW": "Malaui",
    "MY": "Malasia",
    "MV": "Maldivas",
    "ML": "Malí",
    "MT": "Malta",
    "MH": "Marshall Islands",
    "MQ": "Martinique",
    "MR": "Mauritania",
    "MU": "Mauricio",
    "MX": "México",
    "FM": "Micronesia",
    "MD": "Moldavia",
    "MC": "Mónaco",
    "MN": "Mongolia",
    "ME": "Montenegro",
    "MS": "Montserrat",
    "MA": "Marruecos",
    "MZ": "Mozambique",
    "MM": "Myanmar",
    "NA": "Namibia",
    "NR": "Nauru",
    "NP": "Nepal",
    "NL": "Países Bajos",
    "NC": "New Caledonia",
    "NZ": "Nueva Zelanda",
    "NI": "Nicaragua",
    "NE": "Níger",
    "NG": "Nigeria",
    "KP": "Corea del Norte",
    "MK": "Macedonia del Norte",
    "NO": "Noruega",
    "OM": "Omán",
    "PK": "Pakistán",
    "PW": "Palau",
    "PS": "Palestina",
    "PA": "Panamá",
    "PG": "Papúa Nueva Guinea",
    "PY": "Paraguay",
    "PE": "Perú",
    "PH": "Filipinas",
    "PL": "Polonia",
    "PT": "Portugal",
    "PR": "Puerto Rico",
    "QA": "Catar",
    "RE": "Reunion",
    "RO": "Rumania",
    "RU": "Rusia",
    "RW": "Ruanda",
    "KN": "Saint Kitts and Nevis",
    "LC": "Saint Lucia",
    "VC": "Saint Vincent",
    "WS": "Samoa",
    "SM": "San Marino",
    "ST": "Santo Tomé y Príncipe",
    "SA": "Arabia Saudita",
    "SN": "Senegal",
    "RS": "Serbia",
    "SC": "Seychelles",
    "SL": "Sierra Leona",
    "SG": "Singapur",
    "SK": "Eslovaquia",
    "SI": "Eslovenia",
    "SB": "Solomon Islands",
    "SO": "Somalia",
    "ZA": "Sudáfrica",
    "KR": "Corea del Sur",
    "SS": "Sudán del Sur",
    "ES": "España",
    "LK": "Sri Lanka",
    "SD": "Sudán",
    "SR": "Suriname",
    "SE": "Suecia",
    "CH": "Suiza",
    "SY": "Siria",
    "TW": "Taiwán",
    "TJ": "Tayikistán",
    "TZ": "Tanzania",
    "TH": "Tailandia",
    "TL": "Timor-Leste",
    "TG": "Togo",
    "TO": "Tonga",
    "TT": "Trinidad and Tobago",
    "TN": "Túnez",
    "TR": "Turquía",
    "TM": "Turkmenistán",
    "TC": "Turks and Caicos",
    "TV": "Tuvalu",
    "UG": "Uganda",
    "UA": "Ucrania",
    "AE": "Emiratos Árabes Unidos",
    "GB": "Reino Unido",
    "US": "Estados Unidos",
    "UY": "Uruguay",
    "UZ": "Uzbekistán",
    "VU": "Vanuatu",
    "VA": "Ciudad del Vaticano",
    "VE": "Venezuela",
    "VN": "Vietnam",
    "VI": "Virgin Islands (US)",
    "YE": "Yemen",
    "ZM": "Zambia",
    "ZW": "Zimbabue",
}

# English names from the mobile phone-country catalog (alias seeds).
_EN_NAMES: dict[str, str] = {
    "AF": "Afghanistan",
    "AL": "Albania",
    "DZ": "Algeria",
    "AS": "American Samoa",
    "AD": "Andorra",
    "AO": "Angola",
    "AI": "Anguilla",
    "AG": "Antigua and Barbuda",
    "AR": "Argentina",
    "AM": "Armenia",
    "AW": "Aruba",
    "AU": "Australia",
    "AT": "Austria",
    "AZ": "Azerbaijan",
    "BS": "Bahamas",
    "BH": "Bahrain",
    "BD": "Bangladesh",
    "BB": "Barbados",
    "BY": "Belarus",
    "BE": "Belgium",
    "BZ": "Belize",
    "BJ": "Benin",
    "BM": "Bermuda",
    "BT": "Bhutan",
    "BO": "Bolivia",
    "BA": "Bosnia and Herzegovina",
    "BW": "Botswana",
    "BR": "Brazil",
    "BN": "Brunei",
    "BG": "Bulgaria",
    "BF": "Burkina Faso",
    "BI": "Burundi",
    "KH": "Cambodia",
    "CM": "Cameroon",
    "CA": "Canada",
    "CV": "Cape Verde",
    "KY": "Cayman Islands",
    "CF": "Central African Republic",
    "TD": "Chad",
    "CL": "Chile",
    "CN": "China",
    "CO": "Colombia",
    "KM": "Comoros",
    "CG": "Congo",
    "CD": "Congo (DRC)",
    "CR": "Costa Rica",
    "CI": "Cote d'Ivoire",
    "HR": "Croatia",
    "CU": "Cuba",
    "CY": "Cyprus",
    "CZ": "Czechia",
    "DK": "Denmark",
    "DJ": "Djibouti",
    "DM": "Dominica",
    "DO": "Dominican Republic",
    "EC": "Ecuador",
    "EG": "Egypt",
    "SV": "El Salvador",
    "GQ": "Equatorial Guinea",
    "ER": "Eritrea",
    "EE": "Estonia",
    "SZ": "Eswatini",
    "ET": "Ethiopia",
    "FK": "Falkland Islands",
    "FO": "Faroe Islands",
    "FJ": "Fiji",
    "FI": "Finland",
    "FR": "France",
    "GF": "French Guiana",
    "PF": "French Polynesia",
    "GA": "Gabon",
    "GM": "Gambia",
    "GE": "Georgia",
    "DE": "Germany",
    "GH": "Ghana",
    "GI": "Gibraltar",
    "GR": "Greece",
    "GL": "Greenland",
    "GD": "Grenada",
    "GP": "Guadeloupe",
    "GU": "Guam",
    "GT": "Guatemala",
    "GN": "Guinea",
    "GW": "Guinea-Bissau",
    "GY": "Guyana",
    "HT": "Haiti",
    "HN": "Honduras",
    "HK": "Hong Kong",
    "HU": "Hungary",
    "IS": "Iceland",
    "IN": "India",
    "ID": "Indonesia",
    "IR": "Iran",
    "IQ": "Iraq",
    "IE": "Ireland",
    "IL": "Israel",
    "IT": "Italy",
    "JM": "Jamaica",
    "JP": "Japan",
    "JO": "Jordan",
    "KZ": "Kazakhstan",
    "KE": "Kenya",
    "KI": "Kiribati",
    "KW": "Kuwait",
    "KG": "Kyrgyzstan",
    "LA": "Laos",
    "LV": "Latvia",
    "LB": "Lebanon",
    "LS": "Lesotho",
    "LR": "Liberia",
    "LY": "Libya",
    "LI": "Liechtenstein",
    "LT": "Lithuania",
    "LU": "Luxembourg",
    "MO": "Macao",
    "MG": "Madagascar",
    "MW": "Malawi",
    "MY": "Malaysia",
    "MV": "Maldives",
    "ML": "Mali",
    "MT": "Malta",
    "MH": "Marshall Islands",
    "MQ": "Martinique",
    "MR": "Mauritania",
    "MU": "Mauritius",
    "MX": "Mexico",
    "FM": "Micronesia",
    "MD": "Moldova",
    "MC": "Monaco",
    "MN": "Mongolia",
    "ME": "Montenegro",
    "MS": "Montserrat",
    "MA": "Morocco",
    "MZ": "Mozambique",
    "MM": "Myanmar",
    "NA": "Namibia",
    "NR": "Nauru",
    "NP": "Nepal",
    "NL": "Netherlands",
    "NC": "New Caledonia",
    "NZ": "New Zealand",
    "NI": "Nicaragua",
    "NE": "Niger",
    "NG": "Nigeria",
    "KP": "North Korea",
    "MK": "North Macedonia",
    "NO": "Norway",
    "OM": "Oman",
    "PK": "Pakistan",
    "PW": "Palau",
    "PS": "Palestine",
    "PA": "Panama",
    "PG": "Papua New Guinea",
    "PY": "Paraguay",
    "PE": "Peru",
    "PH": "Philippines",
    "PL": "Poland",
    "PT": "Portugal",
    "PR": "Puerto Rico",
    "QA": "Qatar",
    "RE": "Reunion",
    "RO": "Romania",
    "RU": "Russia",
    "RW": "Rwanda",
    "KN": "Saint Kitts and Nevis",
    "LC": "Saint Lucia",
    "VC": "Saint Vincent",
    "WS": "Samoa",
    "SM": "San Marino",
    "ST": "Sao Tome and Principe",
    "SA": "Saudi Arabia",
    "SN": "Senegal",
    "RS": "Serbia",
    "SC": "Seychelles",
    "SL": "Sierra Leone",
    "SG": "Singapore",
    "SK": "Slovakia",
    "SI": "Slovenia",
    "SB": "Solomon Islands",
    "SO": "Somalia",
    "ZA": "South Africa",
    "KR": "South Korea",
    "SS": "South Sudan",
    "ES": "Spain",
    "LK": "Sri Lanka",
    "SD": "Sudan",
    "SR": "Suriname",
    "SE": "Sweden",
    "CH": "Switzerland",
    "SY": "Syria",
    "TW": "Taiwan",
    "TJ": "Tajikistan",
    "TZ": "Tanzania",
    "TH": "Thailand",
    "TL": "Timor-Leste",
    "TG": "Togo",
    "TO": "Tonga",
    "TT": "Trinidad and Tobago",
    "TN": "Tunisia",
    "TR": "Turkey",
    "TM": "Turkmenistan",
    "TC": "Turks and Caicos",
    "TV": "Tuvalu",
    "UG": "Uganda",
    "UA": "Ukraine",
    "AE": "United Arab Emirates",
    "GB": "United Kingdom",
    "US": "United States",
    "UY": "Uruguay",
    "UZ": "Uzbekistan",
    "VU": "Vanuatu",
    "VA": "Vatican City",
    "VE": "Venezuela",
    "VN": "Vietnam",
    "VI": "Virgin Islands (US)",
    "YE": "Yemen",
    "ZM": "Zambia",
    "ZW": "Zimbabwe",
}


def _strip_accents(value: str) -> str:
    nfkd = unicodedata.normalize("NFKD", value)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def _normalize_key(value: str) -> str:
    cleaned = _strip_accents(value).lower().strip()
    cleaned = re.sub(r"[^\w\s]", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


# Extra free-text aliases (beyond auto-generated catalog names / ISO codes).
_EXTRA_ALIASES: dict[str, str] = {
    "colombiano": "CO",
    "colombiana": "CO",
    "estados unidos": "US",
    "eeuu": "US",
    "ee uu": "US",
    "usa": "US",
    "u s a": "US",
    "united states": "US",
    "united states of america": "US",
    "america": "US",
    "uk": "GB",
    "gran bretana": "GB",
    "inglaterra": "GB",
    "england": "GB",
    "united kingdom": "GB",
    "holanda": "NL",
    "netherlands": "NL",
    "paises bajos": "NL",
    "corea del sur": "KR",
    "south korea": "KR",
    "sudafrica": "ZA",
    "south africa": "ZA",
    "ivory coast": "CI",
    "cote d ivoire": "CI",
    "cote divoire": "CI",
    "rdc": "CD",
    "drc": "CD",
    "congo drc": "CD",
    "democratic republic of the congo": "CD",
    "republica dominicana": "DO",
    "dominican republic": "DO",
    "emirates": "AE",
    "uae": "AE",
    "emiratos": "AE",
}


def _build_aliases() -> dict[str, str]:
    aliases: dict[str, str] = {}
    for code, name in _ISO_NAMES.items():
        aliases[_normalize_key(code)] = code
        aliases[_normalize_key(name)] = code
    for code, name in _EN_NAMES.items():
        aliases[_normalize_key(name)] = code
    for key, code in _EXTRA_ALIASES.items():
        aliases[_normalize_key(key)] = code
    return aliases


_ALIASES_NORM = _build_aliases()


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

        # Already an ISO alpha-2 from the phone-country catalog?
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
