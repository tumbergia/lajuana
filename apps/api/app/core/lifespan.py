from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.db import close_db, init_db
from app.core.logging import logger, reconfigure_logger


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    reconfigure_logger()
    logger.info("Application startup — logger reconfigured")
    await init_db()
    yield
    await close_db()
