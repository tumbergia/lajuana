from fastapi import APIRouter

from app.api.endpoints.auth import router as auth_router
from app.api.endpoints.config import router as config_router
from app.api.endpoints.diagnostics import router as diagnostics_router
from app.api.endpoints.experiences import router as experiences_router
from app.api.endpoints.health import router as health_router
from app.api.endpoints.participants import router as participants_router
from app.api.endpoints.reservations import router as reservations_router
from app.api.endpoints.schedules import router as schedules_router
from app.core.config import settings

api_router = APIRouter(prefix=f"{settings.api_prefix}/{settings.api_version}")
api_router.include_router(health_router)
api_router.include_router(diagnostics_router)
api_router.include_router(auth_router)
api_router.include_router(experiences_router)
api_router.include_router(schedules_router)
api_router.include_router(reservations_router)
api_router.include_router(participants_router)
api_router.include_router(config_router)
