"""Shared test configuration.

Initializes the DI container before each test session so endpoints and tools
that call ``Container.get_instance()`` work without modification.

Usage:
    All test files under tests/ automatically load this conftest.

    Tests that need specific mocks can override individual services::

        from app.core.di import Container
        Container.get_instance()._services["reservation_service"] = mock_service

    Use the ``mongomock_db`` fixture for unit tests that need an in-memory
    MongoDB — avoids the real DB entirely::

        async def test_foo(mongomock_db) -> None:
            # mongomock_db is an AsyncIOMotorDatabase
            ...

    Mark tests that require a real MongoDB with ``@pytest.mark.integration``.
    Run ``pytest -m "not integration"`` for fast local unit tests.
"""

from __future__ import annotations

import os

# Prevent real DB connection during tests
os.environ.setdefault("APP_SKIP_DB_INIT", "true")

import mongomock
import pytest

from app.core.di import Container


@pytest.fixture(autouse=True, scope="session")
def _init_container() -> None:
    """Initialize the DI container once per test session."""
    Container.init()


@pytest.fixture(autouse=True)
def _reset_container() -> None:
    """Reset container state between tests to avoid cross-test pollution."""
    pass


@pytest.fixture(scope="function")
def mongomock_client() -> mongomock.MongoClient:
    """In-memory MongoDB via mongomock for unit tests.

    Yields a ``mongomock.MongoClient`` that works as a drop-in replacement
    for ``pymongo.MongoClient``.  No real MongoDB server required.

    Usage::

        def test_foo(mongomock_client) -> None:
            db = mongomock_client["test_db"]
            collection = db["my_collection"]
            collection.insert_one({"_id": "1", "name": "test"})
            assert collection.find_one({"_id": "1"}) is not None

    For services backed by Beanie Documents, monkeypatch
    ``Document.get_motor_collection()`` to return a mongomock collection::

        mock_collection = mongomock_client["test_db"]["experiences"]
        monkeypatch.setattr(
            ExperienceDocument, "get_motor_collection", lambda: mock_collection,
        )

    No setup/teardown required — the mock is ephemeral.
    """
    client = mongomock.MongoClient()
    yield client
