"""Unit tests for analytics v2: formulas, countries, prefs, catalog, export."""

from __future__ import annotations

from datetime import date, datetime, timezone
from types import SimpleNamespace

import pytest

from app.common.enums import Permission, UserRole
from app.schemas.analytics_v2 import (
    ANALYTICS_SCHEMA_VERSION,
    AnalyticsModule,
    AnalyticsPreferencesUpdateSchema,
    ComparisonMode,
    DashboardQuery,
    DashboardResponse,
    DateRangePreset,
    Freshness,
    ModuleCategory,
    ModuleStatus,
    Period,
    PrimaryValue,
    RankingItem,
    Series,
    SeriesPoint,
    ValueType,
    VisualizationType,
    build_comparison,
    format_currency_cop,
    freshness_label,
)
from app.services.analytics_catalog_service import (
    ADMIN_DEFAULT_MODULES,
    GUIDE_DEFAULT_MODULES,
    LEGACY_LEAD_TO_MODULE,
    AnalyticsCatalogService,
)
from app.services.analytics_country_normalizer import AnalyticsCountryNormalizer
from app.services.analytics_export_service import AnalyticsExportService
from app.services.analytics_preferences_service import AnalyticsPreferencesService
from app.services.analytics_query_service import aggregation_grain, resolve_period
from app.services.analytics_service import HOME_INELIGIBLE_IDS, _lead


# ── formulas / comparison ────────────────────────────────────────────────


def test_quoted_amount_never_labeled_facturado_in_helper() -> None:
    # format helper is currency; label is caller's responsibility — guard wording
    assert "facturado" not in format_currency_cop(1500000).lower()
    assert format_currency_cop(1500).startswith("$")


def test_build_comparison_uses_absolute_when_base_small() -> None:
    cmp = build_comparison(current=2, previous=1, previous_label="el periodo anterior")
    assert cmp.mode == ComparisonMode.ABSOLUTE
    assert cmp.sufficient_sample is False
    assert "Pasó de" in (cmp.label or "")


def test_build_comparison_percentage_when_base_sufficient() -> None:
    cmp = build_comparison(current=118, previous=100, previous_label="los 30 días anteriores")
    assert cmp.mode == ComparisonMode.BOTH
    assert cmp.percentage_delta == 18.0
    assert "18.0 % más" in (cmp.label or "") or "18 % más" in (cmp.label or "")


def test_conversion_blocked_documented_in_catalog_concepts() -> None:
    from app.services.analytics_catalog_service import BLOCKED_CONCEPTS

    assert "commercial_conversion" in BLOCKED_CONCEPTS
    assert "collected_revenue" in BLOCKED_CONCEPTS


def test_resolve_period_last_30_and_previous_equal_length() -> None:
    today = date(2026, 7, 14)
    current, previous = resolve_period(
        DashboardQuery(range=DateRangePreset.LAST_30_DAYS), today=today
    )
    assert current.end == today
    assert current.start == date(2026, 6, 15)
    assert (current.end - current.start).days == (previous.end - previous.start).days


def test_aggregation_grain() -> None:
    p7 = Period(start=date(2026, 7, 8), end=date(2026, 7, 14), label="7d")
    p60 = Period(start=date(2026, 5, 16), end=date(2026, 7, 14), label="2m")
    p365 = Period(start=date(2026, 1, 1), end=date(2026, 7, 14), label="y")
    assert aggregation_grain(p7) == "day"
    assert aggregation_grain(p60) == "week"
    assert aggregation_grain(p365) == "month"


# ── countries ────────────────────────────────────────────────────────────


def test_country_normalizer_common_variants() -> None:
    n = AnalyticsCountryNormalizer()
    assert n.normalize("Colombia").country_code == "CO"
    assert n.normalize("USA").country_code == "US"
    assert n.normalize("Estados Unidos").country_code == "US"
    assert n.normalize("EEUU").country_code == "US"
    assert n.normalize("México").country_code == "MX"
    assert n.normalize("us").country_code == "US"


def test_country_normalizer_does_not_invent() -> None:
    n = AnalyticsCountryNormalizer()
    result = n.normalize("Narnia")
    assert result.resolved is False
    assert result.country_code is None
    assert result.original == "Narnia"


def test_country_normalizer_report_unresolved() -> None:
    n = AnalyticsCountryNormalizer()
    _, report = n.normalize_many(["Colombia", "Atlantis", "USA", "Atlantis"])
    assert report.resolved == 2
    assert report.unresolved == 2
    assert "Atlantis" in report.unresolved_values


# ── catalog / permissions ────────────────────────────────────────────────


def test_catalog_filters_payment_for_guide() -> None:
    catalog = AnalyticsCatalogService()
    admin = {m.id for m in catalog.get_catalog(UserRole.ADMIN).modules}
    guide = {m.id for m in catalog.get_catalog(UserRole.GUIDE).modules}
    assert "payment_status" in admin
    assert "payment_status" not in guide
    assert "reservation_trend" in guide
    assert "equine_care_alerts" in guide


def test_defaults_by_role() -> None:
    catalog = AnalyticsCatalogService()
    assert catalog.defaults_for_role(UserRole.ADMIN) == [
        m for m in ADMIN_DEFAULT_MODULES if m in catalog.allowed_module_ids(UserRole.ADMIN)
    ][:4]
    guide_defaults = catalog.defaults_for_role(UserRole.GUIDE)
    assert len(guide_defaults) <= 4
    for mid in guide_defaults:
        assert mid in GUIDE_DEFAULT_MODULES or mid in catalog.allowed_module_ids(UserRole.GUIDE)


def test_legacy_pin_mapping_skips_unknown() -> None:
    catalog = AnalyticsCatalogService()
    mapped = catalog.map_legacy_pins(
        ["ing_confirmed", "vol_conversion", "ori_top_pais", "unknown_x"],
        UserRole.ADMIN,
    )
    assert "confirmed_value_trend" in mapped
    assert "top_countries" in mapped
    assert "vol_conversion" not in LEGACY_LEAD_TO_MODULE or "vol_conversion" not in mapped


# ── preferences ──────────────────────────────────────────────────────────


def test_preferences_cap_at_four_and_drop_action_center() -> None:
    svc = AnalyticsPreferencesService()

    class FakeUser:
        role = UserRole.ADMIN
        analytics_preferences: dict = {}
        leads_preferences: dict = {}

        async def save(self) -> None:
            return None

    user = FakeUser()
    # sync path via _clean
    cleaned = svc._clean(
        {
            "schema_version": 2,
            "selected_module_ids": [
                "action_center",
                "reservation_trend",
                "confirmed_value_trend",
                "top_experiences",
                "top_countries",
                "occupancy",
            ],
        },
        UserRole.ADMIN,
    )
    assert "action_center" not in cleaned.selected_module_ids
    assert len(cleaned.selected_module_ids) <= 4


@pytest.mark.asyncio
async def test_preferences_update_persists() -> None:
    svc = AnalyticsPreferencesService()

    class FakeUser:
        role = UserRole.ADMIN
        analytics_preferences: dict = {}
        leads_preferences: dict = {}
        saved = False

        async def save(self) -> None:
            self.saved = True

    user = FakeUser()
    body = AnalyticsPreferencesUpdateSchema(
        selected_module_ids=[
            "confirmed_value_trend",
            "reservation_trend",
            "top_experiences",
            "top_countries",
            "occupancy",
        ]
    )
    result = await svc.update_preferences(user, body)  # type: ignore[arg-type]
    assert len(result.selected_module_ids) == 4
    assert user.saved is True
    assert user.analytics_preferences["schema_version"] == ANALYTICS_SCHEMA_VERSION


def test_lazy_migrate_from_legacy_pins() -> None:
    svc = AnalyticsPreferencesService()

    class FakeUser:
        role = UserRole.ADMIN
        analytics_preferences: dict = {}
        leads_preferences = {"pinned_lead_ids": ["ing_confirmed", "exp_top"]}

    prefs = svc.get_preferences(FakeUser())  # type: ignore[arg-type]
    assert prefs.selected_module_ids[0] == "confirmed_value_trend"
    assert "top_experiences" in prefs.selected_module_ids


# ── legacy helper still works for tests ──────────────────────────────────


def test_lead_helper_sets_home_eligible_from_blacklist() -> None:
    blocked = _lead(
        id="eq_total",
        category="catalogo",
        title="Total equinos",
        value="10",
        unit="equinos",
        description="x",
        icon="pets",
        order=1,
    )
    assert blocked.home_eligible is False
    assert "eq_total" in HOME_INELIGIBLE_IDS


# ── export ───────────────────────────────────────────────────────────────


def _sample_dashboard() -> DashboardResponse:
    now = datetime.now(timezone.utc)
    period = Period(
        start=date(2026, 6, 15),
        end=date(2026, 7, 14),
        label="Últimos 30 días",
        preset=DateRangePreset.LAST_30_DAYS,
    )
    fresh = Freshness(generated_at=now, label="Actualizado ahora")
    mod = AnalyticsModule(
        id="reservation_trend",
        category=ModuleCategory.RESERVATIONS,
        title="Tendencia de reservas",
        description="Reservas nuevas",
        visualization=VisualizationType.LINE,
        period=period,
        primary_value=PrimaryValue(
            raw=18, formatted="18", unit="reservas", value_type=ValueType.COUNT
        ),
        series=[
            Series(
                id="reservations",
                label="Reservas nuevas",
                unit="reservas",
                points=[
                    SeriesPoint(raw=3, label="2026-07-01", unit="reservas"),
                    SeriesPoint(raw=5, label="2026-07-02", unit="reservas"),
                ],
            )
        ],
        ranking=[
            RankingItem(
                rank=1,
                key="CO",
                label="Colombia",
                raw_value=10,
                formatted_value="10",
                country_code="CO",
                country_name="Colombia",
                share_percentage=50.0,
            )
        ],
        status=ModuleStatus.OK,
        insight_text="Las reservas aumentaron frente al periodo anterior.",
        generated_at=now,
        freshness=fresh,
    )
    return DashboardResponse(
        modules=[mod],
        period=period,
        generated_at=now,
        freshness=fresh,
        schema_version=ANALYTICS_SCHEMA_VERSION,
    )


def test_export_has_four_visible_sheets_and_reopens() -> None:
    svc = AnalyticsExportService()
    data, filename = svc.export_dashboard(
        _sample_dashboard(), generated_by="Ana Admin", include_logo=False
    )
    assert filename.endswith(".xlsx")
    assert "analitica_" in filename
    names = AnalyticsExportService.visible_sheet_names(data)
    assert names == ["Resumen", "Indicadores", "Tendencias", "Desgloses"]
    hits = AnalyticsExportService.assert_no_forbidden_terms_in_visible(data)
    assert hits == [], hits


def test_export_continues_without_logo() -> None:
    svc = AnalyticsExportService()
    data, _ = svc.export_dashboard(
        _sample_dashboard(), generated_by="Guía", include_logo=True
    )
    assert len(data) > 1000
    assert AnalyticsExportService.visible_sheet_names(data)[0] == "Resumen"


def test_freshness_label_business_language() -> None:
    now = datetime(2026, 7, 14, 12, 0, tzinfo=timezone.utc)
    assert freshness_label(now, now=now) == "Actualizado ahora"
    earlier = datetime(2026, 7, 14, 11, 52, tzinfo=timezone.utc)
    assert "minuto" in freshness_label(earlier, now=now)


def test_leads_preferences_caps_pins_and_drops_dupes() -> None:
    from app.schemas.analytics_v2 import LeadsPreferencesSchema

    schema = LeadsPreferencesSchema.from_user_prefs(
        {
            "pinned_lead_ids": ["a", "b", "a", "c", "d", "e", "f", "", 123],
            "excluded_lead_ids": ["x", "a", "y", "x"],
        }
    )
    assert schema.pinned_lead_ids == ["a", "b", "c", "d", "e"]
    assert schema.excluded_lead_ids == ["x", "y"]
