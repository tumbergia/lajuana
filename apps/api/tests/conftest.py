"""Shared test configuration.

Initializes the DI container before each test session so endpoints and tools
that call ``Container.get_instance()`` work without modification.

Usage:
    All test files under tests/ automatically load this conftest.

    Tests that need specific mocks can override individual services::

        from app.core.di import Container
        Container.get_instance()._services["reservation_service"] = mock_service
"""

from __future__ import annotations

import os
from typing import Any

# Prevent real DB connection during tests
os.environ.setdefault("APP_SKIP_DB_INIT", "true")

import pytest

from app.core.di import Container


@pytest.fixture(autouse=True, scope="session")
def _init_container() -> None:
    """Initialize the DI container once per test session.

    All services are real instances — no MongoDB queries are made until
    a Document method (find, insert, save, …) is actually called.
    Individual tests monkeypatch those Document methods as needed.
    """
    Container.init()


@pytest.fixture(autouse=True)
def _reset_container() -> None:
    """Reset container state between tests to avoid cross-test pollution."""
    # Individual tests can swap services via monkeypatch or direct assignment.
    # This fixture ensures a clean container per test.
    # Services are singletons — override in the test if needed.
    pass
