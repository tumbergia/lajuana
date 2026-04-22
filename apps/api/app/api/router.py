from fastapi import APIRouter

from app.api.endpoints.assignments import router as assignments_router
from app.api.endpoints.auth import router as auth_router
from app.api.endpoints.config import router as config_router
from app.api.endpoints.diagnostics import router as diagnostics_router
from app.api.endpoints.equines import router as equines_router
from app.api.endpoints.experiences import router as experiences_router
from app.api.endpoints.health import router as health_router
from app.api.endpoints.logs import router as logs_router
from app.api.endpoints.participants import router as participants_router
from app.api.endpoints.payment_proofs import router as payment_proofs_router
from app.api.endpoints.policies import router as policies_router
from app.api.endpoints.providers import router as providers_router
from app.api.endpoints.reservations import router as reservations_router
from app.api.endpoints.saddles import router as saddles_router
from app.api.endpoints.schedules import router as schedules_router
from app.api.endpoints.users import router as users_router
from app.core.config import settings

api_router = APIRouter(prefix=f"{settings.api_prefix}/{settings.api_version}")
api_router.include_router(health_router)
api_router.include_router(diagnostics_router)
api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(experiences_router)
api_router.include_router(schedules_router)
api_router.include_router(reservations_router)
api_router.include_router(payment_proofs_router)
api_router.include_router(participants_router)
api_router.include_router(config_router)
api_router.include_router(equines_router)
api_router.include_router(saddles_router)
api_router.include_router(assignments_router)
api_router.include_router(logs_router)
api_router.include_router(providers_router)
api_router.include_router(policies_router)
