import logging
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import Response

from app.api.deps import get_analytics_service  # type: ignore[attr-defined]
from app.common.enums import Permission
from app.services.analytics_service import AnalyticsService

from ..deps import require_permissions

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get(
    "/leads",
    operation_id="get_analytics_leads",
)
async def get_leads(
    current_user: Annotated[
        object, Depends(require_permissions(Permission.RESERVATION_READ))
    ],
    svc: AnalyticsService = Depends(get_analytics_service),
    force_refresh: bool = False,
) -> object:
    return await svc.get_all_leads(force_refresh=force_refresh)


@router.get(
    "/leads/export",
    operation_id="export_analytics_leads",
)
async def export_leads(
    current_user: Annotated[
        object, Depends(require_permissions(Permission.RESERVATION_READ))
    ],
    svc: AnalyticsService = Depends(get_analytics_service),
    lead_id: str | None = None,
) -> Response:
    data, filename = await svc.generate_export(lead_id=lead_id)
    return Response(
        content=data,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
