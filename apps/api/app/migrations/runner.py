"""Orchestrator — runs pending migrations on startup.

Called from lifespan after init_db().
Follows fail-open policy: migration errors are logged but do not crash the app.
"""

from __future__ import annotations

import logging
import time

from app.core.config import settings
from app.migrations import registry
from app.migrations.versions import MIGRATIONS

logger = logging.getLogger(__name__)


async def run_migrations() -> None:
    """Apply all pending migrations in version order.

    Idempotent: skips already-applied versions.
    Fail-open: logs errors but does not raise.
    """
    if settings.app_skip_db_init:
        logger.info("[migrations] Skipped (APP_SKIP_DB_INIT=true)")
        return

    try:
        await registry.ensure_index()
    except Exception:
        logger.warning("[migrations] Failed to ensure index — may already exist")

    for m in MIGRATIONS:
        try:
            if await registry.is_applied(m.version):
                continue
        except Exception:
            logger.exception(
                "[migrations] Failed to check %s — skipping",
                m.qualified_name,
            )
            continue

        logger.info(
            "[migrations] Applying %s — %s",
            m.qualified_name,
            m.description,
        )
        t0 = time.monotonic()
        try:
            await m.apply()
        except Exception:
            logger.exception(
                "[migrations] FAILED %s — manual intervention required",
                m.qualified_name,
            )
            continue

        elapsed = time.monotonic() - t0
        await registry.mark_applied(
            version=m.version,
            name=m.name,
            checksum=m.checksum,
            execution_seconds=elapsed,
        )
        logger.info(
            "[migrations] Applied %s in %.2fs",
            m.qualified_name,
            elapsed,
        )
