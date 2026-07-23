"""Analytics dashboard v2 contracts — typed, deterministic modules."""

from __future__ import annotations

from datetime import UTC, date, datetime
from enum import StrEnum

from pydantic import BaseModel, Field

ANALYTICS_SCHEMA_VERSION = 2


class VisualizationType(StrEnum):
    KPI = "kpi"
    SPARKLINE = "sparkline"
    LINE = "line"
    BAR = "bar"
    DONUT = "donut"
    PROGRESS = "progress"
    RANKING = "ranking"
    ACTION_LIST = "action_list"


class ModuleCategory(StrEnum):
    ACTION = "action"
    RESERVATIONS = "reservations"
    MONEY = "money"
    EXPERIENCES = "experiences"
    PARTICIPANTS = "participants"
    EQUINES = "equines"
    OPERATIONS = "operations"


class ModuleStatus(StrEnum):
    OK = "ok"
    EMPTY = "empty"
    DEGRADED = "degraded"
    BLOCKED = "blocked"
    ERROR = "error"


class ValueType(StrEnum):
    COUNT = "count"
    CURRENCY = "currency"
    PERCENT = "percent"
    RATIO = "ratio"
    TEXT = "text"


class ComparisonMode(StrEnum):
    NONE = "none"
    ABSOLUTE = "absolute"
    PERCENTAGE = "percentage"
    BOTH = "both"


class DateRangePreset(StrEnum):
    LAST_7_DAYS = "last_7_days"
    LAST_30_DAYS = "last_30_days"
    LAST_3_MONTHS = "last_3_months"
    THIS_YEAR = "this_year"
    CUSTOM = "custom"


class PrimaryValue(BaseModel):
    raw: float
    formatted: str
    unit: str
    value_type: ValueType = ValueType.COUNT


class Period(BaseModel):
    start: date
    end: date
    label: str
    preset: DateRangePreset | None = None


class Comparison(BaseModel):
    mode: ComparisonMode = ComparisonMode.NONE
    previous_raw: float | None = None
    previous_formatted: str | None = None
    absolute_delta: float | None = None
    absolute_formatted: str | None = None
    percentage_delta: float | None = None
    label: str | None = None
    sufficient_sample: bool = True


class SeriesPoint(BaseModel):
    raw: float
    unit: str = ""
    label: str
    point_date: date | None = None
    category: str | None = None


class Series(BaseModel):
    id: str
    label: str
    unit: str = ""
    points: list[SeriesPoint] = Field(default_factory=list)


class RankingItem(BaseModel):
    rank: int
    key: str
    label: str
    raw_value: float
    formatted_value: str
    unit: str = ""
    share_percentage: float | None = None
    country_code: str | None = None
    country_name: str | None = None


class BreakdownItem(BaseModel):
    dimension: str
    key: str
    label: str
    raw_value: float
    formatted_value: str
    unit: str = ""
    share_percentage: float | None = None
    rank: int | None = None
    country_code: str | None = None


class ModuleAction(BaseModel):
    label: str
    target: str
    route_hint: str | None = None


class Freshness(BaseModel):
    generated_at: datetime
    label: str
    is_stale: bool = False
    is_local: bool = False


class AnalyticsModule(BaseModel):
    id: str
    category: ModuleCategory
    title: str
    description: str
    visualization: VisualizationType
    period: Period
    primary_value: PrimaryValue | None = None
    comparison: Comparison | None = None
    series: list[Series] = Field(default_factory=list)
    ranking: list[RankingItem] = Field(default_factory=list)
    breakdown: list[BreakdownItem] = Field(default_factory=list)
    status: ModuleStatus = ModuleStatus.OK
    insight_text: str | None = None
    analysis: list[str] = Field(default_factory=list)
    action: ModuleAction | None = None
    generated_at: datetime
    freshness: Freshness
    # Presentation-safe empty / blocked messages
    empty_message: str | None = None
    blocked_reason: str | None = None


class CatalogModuleSize(StrEnum):
    COMPACT = "compact"
    STANDARD = "standard"
    WIDE = "wide"


class CatalogModule(BaseModel):
    id: str
    category: ModuleCategory
    title: str
    description: str
    recommended_visualization: VisualizationType
    supported_ranges: list[DateRangePreset]
    allowed_sizes: list[CatalogModuleSize]
    required_permission: str
    home_configurable: bool = True
    always_show_when_active: bool = False
    blocked: bool = False
    blocked_reason: str | None = None


class CatalogResponse(BaseModel):
    modules: list[CatalogModule]
    schema_version: int = ANALYTICS_SCHEMA_VERSION
    generated_at: datetime


class DashboardQuery(BaseModel):
    date_from: date | None = None
    date_to: date | None = None
    range: DateRangePreset = DateRangePreset.LAST_30_DAYS
    comparison: bool = True
    module_ids: list[str] | None = None
    experience_id: str | None = None


class DashboardResponse(BaseModel):
    modules: list[AnalyticsModule]
    period: Period
    generated_at: datetime
    freshness: Freshness
    schema_version: int = ANALYTICS_SCHEMA_VERSION


class AnalyticsPreferencesSchema(BaseModel):
    schema_version: int = ANALYTICS_SCHEMA_VERSION
    selected_module_ids: list[str] = Field(default_factory=list)
    module_order: list[str] = Field(default_factory=list)
    default_range: DateRangePreset = DateRangePreset.LAST_30_DAYS
    updated_at: datetime | None = None


class AnalyticsPreferencesUpdateSchema(BaseModel):
    selected_module_ids: list[str] = Field(default_factory=list)
    module_order: list[str] | None = None
    default_range: DateRangePreset | None = None


# --- Legacy compatibility (kept for adapter) ---


class LeadItem(BaseModel):
    id: str
    category: str
    title: str
    value: str
    unit: str
    description: str
    icon: str
    order: int
    details: list[dict[str, str]] = Field(default_factory=list)
    home_eligible: bool = True
    home_priority: int = 1


class LeadCategory(BaseModel):
    id: str
    name: str
    icon: str
    leads: list[LeadItem]


class AnalyticsResponse(BaseModel):
    """Legacy response shape for /analytics/leads."""

    categories: list[LeadCategory]
    generated_at: datetime
    total_leads: int


class LeadsPreferencesSchema(BaseModel):
    pinned_lead_ids: list[str] = Field(default_factory=list)
    excluded_lead_ids: list[str] = Field(default_factory=list)

    @classmethod
    def from_user_prefs(cls, prefs: dict | None) -> LeadsPreferencesSchema:
        stored = prefs or {}
        pinned = list(stored.get("pinned_lead_ids") or [])
        excluded = list(stored.get("excluded_lead_ids") or [])
        seen_pin: set[str] = set()
        clean_pins: list[str] = []
        for lid in pinned:
            if not isinstance(lid, str) or not lid or lid in seen_pin:
                continue
            seen_pin.add(lid)
            clean_pins.append(lid)
            if len(clean_pins) >= 5:
                break
        seen_excl: set[str] = set()
        clean_excl: list[str] = []
        for lid in excluded:
            if not isinstance(lid, str) or not lid or lid in seen_excl or lid in seen_pin:
                continue
            seen_excl.add(lid)
            clean_excl.append(lid)
        return cls(pinned_lead_ids=clean_pins, excluded_lead_ids=clean_excl)


class LeadsPreferencesUpdateSchema(BaseModel):
    pinned_lead_ids: list[str] = Field(default_factory=list)
    excluded_lead_ids: list[str] = Field(default_factory=list)


def format_currency_cop(amount: float) -> str:
    return f"${int(round(amount)):,}".replace(",", ".")


def format_count(value: float) -> str:
    if value == int(value):
        return str(int(value))
    return f"{value:.1f}"


def build_comparison(
    *,
    current: float,
    previous: float,
    previous_label: str,
    value_type: ValueType = ValueType.COUNT,
    min_base_for_pct: float = 5.0,
    unit: str = "",
) -> Comparison:
    """Decide absolute vs percentage comparison for business-friendly labels."""
    absolute = current - previous
    if previous <= 0 and current <= 0:
        return Comparison(mode=ComparisonMode.NONE, sufficient_sample=False)

    pct: float | None = None
    if previous >= min_base_for_pct:
        pct = round((absolute / previous) * 100, 1)

    if value_type == ValueType.CURRENCY:
        abs_fmt = format_currency_cop(abs(absolute))
        prev_fmt = format_currency_cop(previous)
        cur_unit = "COP"
    else:
        abs_fmt = format_count(abs(absolute))
        prev_fmt = format_count(previous)
        cur_unit = unit or ""

    if previous < min_base_for_pct:
        if absolute == 0:
            return Comparison(
                mode=ComparisonMode.ABSOLUTE,
                previous_raw=previous,
                previous_formatted=prev_fmt,
                absolute_delta=absolute,
                absolute_formatted=abs_fmt,
                sufficient_sample=False,
                label=f"Sin cambio frente a {previous_label}",
            )
        direction = "más" if absolute > 0 else "menos"
        return Comparison(
            mode=ComparisonMode.ABSOLUTE,
            previous_raw=previous,
            previous_formatted=prev_fmt,
            absolute_delta=absolute,
            absolute_formatted=abs_fmt,
            sufficient_sample=False,
            label=f"Pasó de {prev_fmt} a {format_count(current)} {cur_unit}".strip(),
        )

    if absolute == 0:
        return Comparison(
            mode=ComparisonMode.BOTH if pct is not None else ComparisonMode.ABSOLUTE,
            previous_raw=previous,
            previous_formatted=prev_fmt,
            absolute_delta=0,
            absolute_formatted="0",
            percentage_delta=0.0,
            label=f"Igual que en {previous_label}",
        )

    direction = "más" if absolute > 0 else "menos"
    if pct is not None:
        return Comparison(
            mode=ComparisonMode.BOTH,
            previous_raw=previous,
            previous_formatted=prev_fmt,
            absolute_delta=absolute,
            absolute_formatted=abs_fmt,
            percentage_delta=pct,
            label=f"{abs(pct)} % {direction} que en {previous_label}",
        )
    return Comparison(
        mode=ComparisonMode.ABSOLUTE,
        previous_raw=previous,
        previous_formatted=prev_fmt,
        absolute_delta=absolute,
        absolute_formatted=abs_fmt,
        label=f"{abs_fmt} {direction} que en {previous_label}",
    )


def freshness_label(generated_at: datetime, *, now: datetime | None = None) -> str:

    now = now or datetime.now(UTC)
    if generated_at.tzinfo is None:
        generated_at = generated_at.replace(tzinfo=UTC)
    delta = now - generated_at
    seconds = max(0, int(delta.total_seconds()))
    if seconds < 60:
        return "Actualizado ahora"
    minutes = seconds // 60
    if minutes < 60:
        return f"Actualizado hace {minutes} minuto{'s' if minutes != 1 else ''}"
    hours = minutes // 60
    if hours < 24:
        return f"Actualizado hace {hours} hora{'s' if hours != 1 else ''}"
    days = hours // 24
    return f"Actualizado hace {days} día{'s' if days != 1 else ''}"
