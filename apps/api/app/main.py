from fastapi import FastAPI

from app.api.router import api_router
from app.core.config import settings
from app.core.errors import register_error_handlers
from app.core.lifespan import lifespan

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
)
register_error_handlers(app)
app.include_router(api_router)
