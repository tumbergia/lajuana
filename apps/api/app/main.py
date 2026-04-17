from fastapi import FastAPI

from app.api.router import api_router
from app.core.config import settings
from app.core.lifespan import lifespan

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.app_debug,
    lifespan=lifespan,
)
app.include_router(api_router)
