"""Migration infrastructure — formal, trackable, idempotent.

Usage from lifespan:
    from app.migrations import run_migrations
    await run_migrations()
"""

from app.migrations.runner import run_migrations

__all__ = ["run_migrations"]
