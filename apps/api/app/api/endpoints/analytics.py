"""Analytics endpoints — v2 dashboard + legacy leads adapter."""

from __future__ import annotations

import logging
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response

from app.api.deps import get_analytics_service  # type: ignore[attr-defined]
from app.common.enums import Permission
from app.documents import UserDocument
from app.schemas.analytics_v2 import (
    AnalyticsPreferencesSchema,
    AnalyticsPreferencesUpdateSchema,
    CatalogResponse,
    DashboardQuery,
    DashboardResponse,
    DateRangePreset,
    LeadsPreferencesSchema,
    LeadsPreferencesUpdateSchema,
)
from app.services.analytics_service import AnalyticsService

from ..deps import require_permissions

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analytics", tags=["Analytics"])


def _parse_query(
    date_from: date | None,
    date_to: date | None,
    range: DateRangePreset,
    comparison: bool,
    module_ids: str | None,
    experience_id: str | None,
) -> DashboardQuery:
    ids = None
    if module_ids:
        ids = [m.strip() for m in module_ids.split(",") if m.strip()]
    return DashboardQuery(
        date_from=date_from,
        date_to=date_to,
        range=range,
        comparison=comparison,
        module_ids=ids,
        experience_id=experience_id,
    )


# ── v2 dashboard ─────────────────────────────────────────────────────────


@router.get(
    "/dashboard/catalog",
    response_model=CatalogResponse,
    operation_id="get_analytics_dashboard_catalog",
)
async def get_dashboard_catalog(
    current_user: Annotated[
        UserDocument, Depends(require_permissions(Permission.RESERVATION_READ))
    ],
    svc: AnalyticsService = Depends(get_analytics_service),
) -> CatalogResponse:
    return svc.get_catalog(current_user.role)


@router.get(
    "/dashboard",
    response_model=DashboardResponse,
    operation_id="get_analytics_dashboard",
)
async def get_dashboard(
    current_user: Annotated[
        UserDocument, Depends(require_permissions(Permission.RESERVATION_READ))
    ],
    svc: AnalyticsService = Depends(get_analytics_service),
    date_from: date | None = None,
    date_to: date | None = None,
    range: DateRangePreset = DateRangePreset.LAST_30_DAYS,
    comparison: bool = True,
    module_ids: str | None = Query(default=None, description="Comma-separated module ids"),
    experience_id: str | None = None,
    force_refresh: bool = False,
) -> DashboardResponse:
    query = _parse_query(date_from, date_to, range, comparison, module_ids, experience_id)
    return await svc.get_dashboard(
        role=current_user.role, query=query, force_refresh=force_refresh
    )


@router.get(
    "/dashboard/preferences",
    response_model=AnalyticsPreferencesSchema,
    operation_id="get_analytics_dashboard_preferences",
)
async def get_dashboard_preferences(
    current_user: Annotated[
        UserDocument, Depends(require_permissions(Permission.RESERVATION_READ))
    ],
    svc: AnalyticsService = Depends(get_analytics_service),
) -> AnalyticsPreferencesSchema:
    return svc.get_preferences(current_user)


@router.put(
    "/dashboard/preferences",
    response_model=AnalyticsPreferencesSchema,
    operation_id="update_analytics_dashboard_preferences",
)
async def update_dashboard_preferences(
    body: AnalyticsPreferencesUpdateSchema,
    current_user: Annotated[
        UserDocument, Depends(require_permissions(Permission.RESERVATION_READ))
    ],
    svc: AnalyticsService = Depends(get_analytics_service),
) -> AnalyticsPreferencesSchema:
    return await svc.update_preferences(current_user, body)


@router.get(
    "/dashboard/export",
    operation_id="export_analytics_dashboard",
)
async def export_dashboard(
    current_user: Annotated[
        UserDocument, Depends(require_permissions(Permission.RESERVATION_READ))
    ],
    svc: AnalyticsService = Depends(get_analytics_service),
    date_from: date | None = None,
    date_to: date | None = None,
    range: DateRangePreset = DateRangePreset.LAST_30_DAYS,
    comparison: bool = True,
    module_ids: str | None = None,
    experience_id: str | None = None,
) -> Response:
    query = _parse_query(date_from, date_to, range, comparison, module_ids, experience_id)
    data, filename = await svc.export_dashboard(
        role=current_user.role,
        user_name=current_user.full_name,
        query=query,
    )
    return Response(
        content=data,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ── legacy leads (adapter) ───────────────────────────────────────────────


@router.get(
    "/leads",
    operation_id="get_analytics_leads",
)
async def get_leads(
    current_user: Annotated[
        UserDocument, Depends(require_permissions(Permission.RESERVATION_READ))
    ],
    svc: AnalyticsService = Depends(get_analytics_service),
    force_refresh: bool = False,
) -> object:
    return await svc.get_all_leads(force_refresh=force_refresh, role=current_user.role)


@router.get(
    "/leads/preferences",
    response_model=LeadsPreferencesSchema,
    operation_id="get_analytics_leads_preferences",
)
async def get_leads_preferences(
    current_user: Annotated[
        UserDocument, Depends(require_permissions(Permission.RESERVATION_READ))
    ],
) -> LeadsPreferencesSchema:
    return LeadsPreferencesSchema.from_user_prefs(current_user.leads_preferences)


@router.put(
    "/leads/preferences",
    response_model=LeadsPreferencesSchema,
    operation_id="update_analytics_leads_preferences",
)
async def update_leads_preferences(
    body: LeadsPreferencesUpdateSchema,
    current_user: Annotated[
        UserDocument, Depends(require_permissions(Permission.RESERVATION_READ))
    ],
) -> LeadsPreferencesSchema:
    cleaned = LeadsPreferencesSchema.from_user_prefs(
        {
            "pinned_lead_ids": body.pinned_lead_ids,
            "excluded_lead_ids": body.excluded_lead_ids,
        }
    )
    current_user.leads_preferences = {
        "pinned_lead_ids": cleaned.pinned_lead_ids,
        "excluded_lead_ids": cleaned.excluded_lead_ids,
    }
    await current_user.save()
    return cleaned


@router.get(
    "/leads/export",
    operation_id="export_analytics_leads",
)
async def export_leads(
    current_user: Annotated[
        UserDocument, Depends(require_permissions(Permission.RESERVATION_READ))
    ],
    svc: AnalyticsService = Depends(get_analytics_service),
    lead_id: str | None = None,
) -> Response:
    data, filename = await svc.generate_export(
        lead_id=lead_id,
        role=current_user.role,
        user_name=current_user.full_name,
    )
    return Response(
        content=data,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
