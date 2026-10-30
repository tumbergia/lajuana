"""Backward-compatible re-exports. Prefer analytics_v2 for new code."""

from app.schemas.analytics_v2 import (  # noqa: F401
    AnalyticsPreferencesSchema,
    AnalyticsPreferencesUpdateSchema,
    AnalyticsResponse,
    LeadCategory,
    LeadItem,
    LeadsPreferencesSchema,
    LeadsPreferencesUpdateSchema,
)
