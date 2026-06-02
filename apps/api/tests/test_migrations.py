"""Tests for the migration infrastructure (base class + runner logic).

Registry tests require a real MongoDB; they live in test_migrations_registry.py
and are excluded from the default unit-test run.
"""

from __future__ import annotations

import os

os.environ["APP_SKIP_DB_INIT"] = "true"

import pytest

from app.migrations.base import Migration
from app.migrations.runner import run_migrations


class _DummyMigration(Migration):
    """Minimal migration for testing base class mechanics."""

    applied = False

    def __init__(self) -> None:
        super().__init__(version="999", name="dummy", description="Test migration")

    async def apply(self) -> None:
        self.applied = True


class TestMigrationBase:

    def test_qualified_name(self) -> None:
        m = _DummyMigration()
        assert m.qualified_name == "999_dummy"

    def test_checksum_is_stable(self) -> None:
        m1 = _DummyMigration()
        m2 = _DummyMigration()
        assert m1.checksum == m2.checksum
        assert len(m1.checksum) == 16

    def test_checksum_changes_when_apply_changes(self) -> None:
        m1 = _DummyMigration()

        class DifferentMigration(Migration):
            def __init__(self) -> None:
                super().__init__(version="998", name="diff")

            async def apply(self) -> None:
                pass  # different implementation

        m2 = DifferentMigration()
        assert m1.checksum != m2.checksum

    def test_apply_is_called(self) -> None:
        m = _DummyMigration()

        async def run() -> None:
            await m.apply()

        import asyncio
        asyncio.run(run())
        assert m.applied is True

    def test_rollback_default_is_noop(self) -> None:
        m = _DummyMigration()

        async def run() -> None:
            await m.rollback()  # should not raise

        import asyncio
        asyncio.run(run())

    def test_version_required(self) -> None:
        with pytest.raises(ValueError, match="version"):
            Migration(version="", name="bad")

    def test_name_required(self) -> None:
        with pytest.raises(ValueError, match="name"):
            Migration(version="001", name="")


class TestMigrationVersions:

    def test_all_migrations_have_valid_properties(self) -> None:
        from app.migrations.versions import MIGRATIONS

        assert len(MIGRATIONS) >= 1
        for m in MIGRATIONS:
            assert m.version
            assert m.name
            assert m.qualified_name
            assert m.checksum
            version_int = int(m.version)
            assert 1 <= version_int <= 999

    def test_migrations_ordered_by_version(self) -> None:
        from app.migrations.versions import MIGRATIONS

        versions = [int(m.version) for m in MIGRATIONS]
        assert versions == sorted(versions), "Migrations must be in version order"


class TestMigrationRunner:

    def test_runner_skipped_when_app_skip_db_init(self) -> None:
        """run_migrations returns early when APP_SKIP_DB_INIT is set."""

        async def run() -> None:
            # Should not raise even with db.client = None
            await run_migrations()

        import asyncio
        asyncio.run(run())
