"""Canonical analytics palette for XLSX export charts.

Keep in sync with:
  packages/mobile_ui/lib/src/theme/analytics_visual_tokens.dart
  apps/mobile/.../insights/insight_cards.dart (breakdownItemColor / channel map)
"""

from __future__ import annotations

# Domain accents (light theme tokens from AnalyticsVisualTokens).
DOMAIN_COLORS: dict[str, str] = {
    "action": "FF9800",
    "reservations": "1E88E5",
    "money": "43A047",
    "experiences": "00897B",
    "participants": "5C6BC0",
    "equines": "8D6E63",
    "operations": "546E7A",
}

# seriesPalette from AnalyticsVisualTokens.light
SERIES_PALETTE: list[str] = [
    "1E88E5",  # reservations blue
    "00897B",  # experiences teal
    "43A047",  # money green
    "F9A825",  # amber
    "FF7043",  # coral
    "5C6BC0",  # participants indigo
]

STATUS_COLORS: dict[str, str] = {
    "success": "43A047",
    "warning": "F9A825",
    "danger": "E53935",
    "neutral": "90A4AE",
    "white": "FFFFFF",
    "soft_green": "81C784",
}

# Brand channel colors (reservation_origins).
CHANNEL_COLORS: dict[str, str] = {
    "whatsapp": "25D366",
    "facebook": "1877F2",
    "instagram": "E1306C",
    "email": "64748B",
}

# Reservation / payment status keys → fill hex.
RESERVATION_STATUS_COLORS: dict[str, str] = {
    "payment_received": STATUS_COLORS["white"],
    "confirmed": STATUS_COLORS["soft_green"],
    "completed": STATUS_COLORS["soft_green"],
    "pending_payment": STATUS_COLORS["warning"],
    "cancelled": STATUS_COLORS["danger"],
    "expired": STATUS_COLORS["danger"],
}

PAYMENT_STATUS_COLORS: dict[str, str] = {
    "pending": STATUS_COLORS["warning"],
    "received": STATUS_COLORS["white"],
    "verified": STATUS_COLORS["soft_green"],
    "rejected": STATUS_COLORS["danger"],
}

READINESS_COLORS: dict[str, str] = {
    "completed": STATUS_COLORS["success"],
    "pending": STATUS_COLORS["warning"],
}

EXPERIENCES_VIVID_PALETTE: list[str] = [
    "00E676",
    "FF9100",
    "40C4FF",
    "E040FB",
    "FFEA00",
    "7C4DFF",
]


def domain_color(category: str) -> str:
    return DOMAIN_COLORS.get(category, STATUS_COLORS["neutral"])


def series_color(index: int) -> str:
    return SERIES_PALETTE[index % len(SERIES_PALETTE)]


def breakdown_color(module_id: str, key: str, index: int) -> str:
    if module_id == "reservation_origins":
        return CHANNEL_COLORS.get(key, series_color(index))
    if module_id == "reservation_status":
        return RESERVATION_STATUS_COLORS.get(key, series_color(index))
    if module_id == "payment_status":
        return PAYMENT_STATUS_COLORS.get(key, series_color(index))
    if module_id == "participant_readiness":
        return READINESS_COLORS.get(key, series_color(index))
    return series_color(index)


def ranking_color(module_id: str, index: int) -> str:
    if module_id == "top_experiences":
        return EXPERIENCES_VIVID_PALETTE[index % len(EXPERIENCES_VIVID_PALETTE)]
    return series_color(index)


def occupancy_color(share_percentage: float | None) -> str:
    if share_percentage is None:
        return STATUS_COLORS["neutral"]
    if share_percentage < 25:
        return STATUS_COLORS["danger"]
    if share_percentage < 75:
        return STATUS_COLORS["warning"]
    return STATUS_COLORS["success"]
