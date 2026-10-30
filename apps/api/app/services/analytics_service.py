"""Analytics facade — single entry for DI; delegates to v2 services.

Legacy /analytics/leads* endpoints adapt module results into LeadItem shapes
so existing mobile clients keep working during migration.
"""

from __future__ import annotations

from app.common.enums import UserRole
from app.documents import UserDocument
from app.schemas.analytics_v2 import (
    AnalyticsPreferencesSchema,
    AnalyticsPreferencesUpdateSchema,
    AnalyticsResponse,
    CatalogResponse,
    DashboardQuery,
    DashboardResponse,
    DateRangePreset,
    LeadCategory,
    LeadItem,
    ModuleStatus,
)
from app.services.analytics_catalog_service import AnalyticsCatalogService
from app.services.analytics_country_normalizer import AnalyticsCountryNormalizer
from app.services.analytics_export_service import AnalyticsExportService
from app.services.analytics_preferences_service import AnalyticsPreferencesService
from app.services.analytics_query_service import AnalyticsQueryService

# Re-export for tests that import from analytics_service
HOME_INELIGIBLE_IDS: frozenset[str] = frozenset(
    {
        "eq_total",
        "eq_mules",
        "eq_horses",
        "eq_donkeys",
        "par_total",
        "par_avg_age",
        "par_top_level",
        "ori_total_paises",
        "ori_top_pais",
        "ori_top_pct",
        "ori_top_5",
        "exp_total",
        "exp_published",
        "exp_routes",
        "exp_experiences",
        "exp_private",
        "vol_total",
        "op_usuarios",
        "op_usuarios_total",
        "pay_total",
        "vol_conversion",
    }
)

HOME_PRIORITY_BY_ID: dict[str, int] = {
    "ing_confirmed": 10,
    "confirmed_value_trend": 10,
}


def _lead(
    *,
    id: str,
    category: str,
    title: str,
    value: str,
    unit: str,
    description: str,
    icon: str,
    order: int,
    details: list[dict[str, str]] | None = None,
    home_eligible: bool | None = None,
    home_priority: int | None = None,
) -> LeadItem:
    eligible = home_eligible if home_eligible is not None else id not in HOME_INELIGIBLE_IDS
    priority = home_priority if home_priority is not None else HOME_PRIORITY_BY_ID.get(id, 1)
    return LeadItem(
        id=id,
        category=category,
        title=title,
        value=value,
        unit=unit,
        description=description,
        icon=icon,
        order=order,
        details=details or [],
        home_eligible=eligible,
        home_priority=max(1, priority) if eligible else 0,
    )


_MODULE_ICON = {
    "action_center": "priority_high",
    "reservation_trend": "trending_up",
    "reservation_status": "donut_large",
    "confirmed_value_trend": "verified",
    "payment_status": "payments",
    "top_experiences": "emoji_events",
    "occupancy": "event_seat",
    "top_countries": "flag",
    "participant_readiness": "assignment_late",
    "equine_availability": "pets",
    "equine_workload": "fitness_center",
    "equine_care_alerts": "health_and_safety",
}

_CATEGORY_META = {
    "action": ("accion", "Pendientes de acción", "priority_high"),
    "reservations": ("reservas", "Reservas", "bar_chart"),
    "money": ("dinero", "Ingresos y pagos", "monetization_on"),
    "experiences": ("catalogo", "Experiencias", "menu_book"),
    "participants": ("personas", "Participantes", "people"),
    "equines": ("eq_operacion", "Equinos", "pets"),
    "operations": ("accion", "Operación", "pending_actions"),
}


class AnalyticsService:
    """Facade used by FastAPI DI and legacy endpoints."""

    def __init__(self) -> None:
        self.catalog = AnalyticsCatalogService()
        self.countries = AnalyticsCountryNormalizer()
        self.query = AnalyticsQueryService(catalog=self.catalog, country_normalizer=self.countries)
        self.preferences = AnalyticsPreferencesService(catalog=self.catalog)
        self.export = AnalyticsExportService()

    # ── v2 API ───────────────────────────────────────────────────────────

    def get_catalog(self, role: UserRole) -> CatalogResponse:
        return self.catalog.get_catalog(role)

    async def get_dashboard(
        self,
        *,
        role: UserRole,
        query: DashboardQuery | None = None,
        force_refresh: bool = False,
    ) -> DashboardResponse:
        return await self.query.get_dashboard(
            role=role,
            query=query or DashboardQuery(),
            force_refresh=force_refresh,
        )

    def get_preferences(self, user: UserDocument) -> AnalyticsPreferencesSchema:
        return self.preferences.get_preferences(user)

    async def update_preferences(
        self, user: UserDocument, body: AnalyticsPreferencesUpdateSchema
    ) -> AnalyticsPreferencesSchema:
        return await self.preferences.update_preferences(user, body)

    async def export_dashboard(
        self,
        *,
        role: UserRole,
        user_name: str,
        query: DashboardQuery | None = None,
    ) -> tuple[bytes, str]:
        dashboard = await self.get_dashboard(role=role, query=query, force_refresh=True)
        return self.export.export_dashboard(dashboard, generated_by=user_name)

    # ── legacy API (adapter) ─────────────────────────────────────────────

    async def get_all_leads(
        self,
        force_refresh: bool = False,
        *,
        role: UserRole = UserRole.ADMIN,
    ) -> AnalyticsResponse:
        dashboard = await self.get_dashboard(
            role=role,
            query=DashboardQuery(range=DateRangePreset.LAST_30_DAYS, comparison=False),
            force_refresh=force_refresh,
        )
        return self._modules_to_legacy(dashboard)

    async def generate_export(
        self,
        lead_id: str | None = None,
        *,
        role: UserRole = UserRole.ADMIN,
        user_name: str = "La Juana",
    ) -> tuple[bytes, str]:
        # Prefer v2 fixed structure; lead_id ignored for sheet layout (compat).
        _ = lead_id
        return await self.export_dashboard(role=role, user_name=user_name)

    def _modules_to_legacy(self, dashboard: DashboardResponse) -> AnalyticsResponse:
        by_cat: dict[str, list[LeadItem]] = {}
        order = 0
        for mod in dashboard.modules:
            cat_key = mod.category.value if hasattr(mod.category, "value") else str(mod.category)
            legacy_id, legacy_name, legacy_icon = _CATEGORY_META.get(
                cat_key, (cat_key, cat_key, "insights")
            )
            order += 1
            value = mod.primary_value.formatted if mod.primary_value else "—"
            unit = mod.primary_value.unit if mod.primary_value else ""
            details: list[dict[str, str]] = []
            for item in mod.breakdown:
                details.append({"Etiqueta": item.label, "Cantidad": item.formatted_value})
            for item in mod.ranking:
                details.append({"Etiqueta": item.label, "Cantidad": item.formatted_value})
            lead = _lead(
                id=mod.id,
                category=legacy_id,
                title=mod.title,
                value=value,
                unit=unit,
                description=mod.description,
                icon=_MODULE_ICON.get(mod.id, "insights"),
                order=order,
                details=details,
                home_eligible=mod.id != "action_center" and mod.status != ModuleStatus.BLOCKED,
                home_priority=5,
            )
            by_cat.setdefault(legacy_id, []).append(lead)
            # stash name/icon on first
            by_cat.setdefault(f"__meta_{legacy_id}", [])  # type: ignore[arg-type]

        categories: list[LeadCategory] = []
        seen: set[str] = set()
        for mod in dashboard.modules:
            cat_key = mod.category.value if hasattr(mod.category, "value") else str(mod.category)
            legacy_id, legacy_name, legacy_icon = _CATEGORY_META.get(
                cat_key, (cat_key, cat_key, "insights")
            )
            if legacy_id in seen:
                continue
            seen.add(legacy_id)
            categories.append(
                LeadCategory(
                    id=legacy_id,
                    name=legacy_name,
                    icon=legacy_icon,
                    leads=by_cat.get(legacy_id, []),
                )
            )

        total = sum(len(c.leads) for c in categories)
        return AnalyticsResponse(
            categories=categories,
            generated_at=dashboard.generated_at,
            total_leads=total,
        )
