"""Versioned analytics dashboard preferences."""

from __future__ import annotations

from datetime import UTC, datetime

from app.common.enums import UserRole
from app.documents import UserDocument
from app.schemas.analytics_v2 import (
    ANALYTICS_SCHEMA_VERSION,
    AnalyticsPreferencesSchema,
    AnalyticsPreferencesUpdateSchema,
    DateRangePreset,
)
from app.services.analytics_catalog_service import AnalyticsCatalogService


class AnalyticsPreferencesService:
    def __init__(self, catalog: AnalyticsCatalogService | None = None) -> None:
        self._catalog = catalog or AnalyticsCatalogService()

    def get_preferences(self, user: UserDocument) -> AnalyticsPreferencesSchema:
        stored = getattr(user, "analytics_preferences", None) or {}
        if stored.get("schema_version") and stored.get("selected_module_ids") is not None:
            return self._clean(stored, user.role)

        # Lazy migrate from legacy leads pins when no v2 prefs yet.
        legacy = getattr(user, "leads_preferences", None) or {}
        pinned = list(legacy.get("pinned_lead_ids") or [])
        mapped = self._catalog.map_legacy_pins(pinned, user.role)
        if not mapped:
            mapped = self._catalog.defaults_for_role(user.role)
        return AnalyticsPreferencesSchema(
            schema_version=ANALYTICS_SCHEMA_VERSION,
            selected_module_ids=mapped,
            module_order=list(mapped),
            default_range=DateRangePreset.LAST_30_DAYS,
            updated_at=None,
        )

    async def ensure_persisted(self, user: UserDocument) -> AnalyticsPreferencesSchema:
        """Persist lazy-migrated prefs if analytics_preferences is empty."""
        stored = getattr(user, "analytics_preferences", None) or {}
        prefs = self.get_preferences(user)
        if not stored.get("selected_module_ids"):
            user.analytics_preferences = prefs.model_dump(mode="json")
            await user.save()
        return prefs

    async def update_preferences(
        self,
        user: UserDocument,
        body: AnalyticsPreferencesUpdateSchema,
    ) -> AnalyticsPreferencesSchema:
        allowed = self._catalog.allowed_module_ids(user.role)
        selected: list[str] = []
        seen: set[str] = set()
        for mid in body.selected_module_ids:
            if mid not in allowed or mid in seen or mid == "action_center":
                continue
            seen.add(mid)
            selected.append(mid)

        order_source = body.module_order if body.module_order is not None else selected
        order: list[str] = []
        seen_order: set[str] = set()
        for mid in order_source:
            if mid in selected and mid not in seen_order:
                seen_order.add(mid)
                order.append(mid)
        for mid in selected:
            if mid not in seen_order:
                order.append(mid)

        default_range = body.default_range or DateRangePreset.LAST_30_DAYS
        prefs = AnalyticsPreferencesSchema(
            schema_version=ANALYTICS_SCHEMA_VERSION,
            selected_module_ids=order,
            module_order=order,
            default_range=default_range,
            updated_at=datetime.now(UTC),
        )
        user.analytics_preferences = prefs.model_dump(mode="json")
        await user.save()
        return prefs

    def restore_defaults(self, role: UserRole) -> AnalyticsPreferencesSchema:
        defaults = self._catalog.defaults_for_role(role)
        return AnalyticsPreferencesSchema(
            schema_version=ANALYTICS_SCHEMA_VERSION,
            selected_module_ids=defaults,
            module_order=list(defaults),
            default_range=DateRangePreset.LAST_30_DAYS,
            updated_at=datetime.now(UTC),
        )

    def _clean(self, stored: dict, role: UserRole) -> AnalyticsPreferencesSchema:
        allowed = self._catalog.allowed_module_ids(role)
        selected: list[str] = []
        seen: set[str] = set()
        for mid in list(stored.get("selected_module_ids") or []):
            if not isinstance(mid, str) or mid not in allowed or mid in seen:
                continue
            if mid == "action_center":
                continue
            seen.add(mid)
            selected.append(mid)
        if not selected:
            selected = self._catalog.defaults_for_role(role)
        order = list(selected)
        raw_range = stored.get("default_range") or DateRangePreset.LAST_30_DAYS.value
        try:
            default_range = DateRangePreset(raw_range)
        except ValueError:
            default_range = DateRangePreset.LAST_30_DAYS
        updated_at = stored.get("updated_at")
        if isinstance(updated_at, str):
            try:
                updated_at = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
            except ValueError:
                updated_at = None
        return AnalyticsPreferencesSchema(
            schema_version=ANALYTICS_SCHEMA_VERSION,
            selected_module_ids=order,
            module_order=order,
            default_range=default_range,
            updated_at=updated_at,
        )
