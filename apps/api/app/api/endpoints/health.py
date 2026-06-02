import logging

from fastapi import APIRouter

from app.core.db import db

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict[str, str | dict[str, str]]:
    checks: dict[str, str] = {}

    # MongoDB check
    if db.client is None:
        checks["mongodb"] = "not_initialized"
    else:
        try:
            await db.client.admin.command("ping")
            checks["mongodb"] = "ok"
        except Exception:
            logger.exception("[health] MongoDB ping failed")
            checks["mongodb"] = "error"

    overall = "ok" if all(v == "ok" for v in checks.values()) else "degraded"
    return {"status": overall, "checks": checks}
