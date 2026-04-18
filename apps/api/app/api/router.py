from fastapi import APIRouter

from app.api.endpoints.diagnostics import router as diagnostics_router
from app.api.endpoints.health import router as health_router
from app.core.config import settings

api_router = APIRouter(prefix=f"{settings.api_prefix}/{settings.api_version}")
api_router.include_router(health_router)
api_router.include_router(diagnostics_router)
