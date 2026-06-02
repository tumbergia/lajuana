"""Demo: mongomock-backed unit tests for MongoDB-dependent code.

This file demonstrates the pattern for writing fast unit tests that
use an in-memory MongoDB (mongomock) instead of a real server.

Usage:
    pytest tests/test_mongomock_demo.py -x -v

Pattern:
    1. Grab the ``mongomock_client`` fixture.
    2. Get a database: ``db = mongomock_client["test_db"]``
    3. Get a collection: ``collection = db["my_collection"]``
    4. Insert test documents via ``collection.insert_one()`` or
       ``collection.insert_many()``.
    5. Query via ``collection.find_one()``, ``collection.find()``, etc.
    6. All operations are in-memory — fast, isolated, ephemeral.
"""

from __future__ import annotations

import mongomock
import pytest


def test_mongomock_insert_and_find(mongomock_client: mongomock.MongoClient) -> None:
    """Verify mongomock can insert documents and find them back."""
    db = mongomock_client["test_db"]
    collection = db["test_docs"]

    doc = {"_id": "abc-123", "name": "Test Document", "value": 42}
    collection.insert_one(doc)

    found = collection.find_one({"_id": "abc-123"})
    assert found is not None
    assert found["name"] == "Test Document"
    assert found["value"] == 42


def test_mongomock_find_missing(mongomock_client: mongomock.MongoClient) -> None:
    """Verify mongomock returns None for non-existent documents."""
    db = mongomock_client["test_db"]
    collection = db["test_docs"]

    found = collection.find_one({"_id": "does-not-exist"})
    assert found is None


def test_mongomock_update(mongomock_client: mongomock.MongoClient) -> None:
    """Verify mongomock supports update_one."""
    db = mongomock_client["test_db"]
    collection = db["test_docs"]

    collection.insert_one({"_id": "1", "counter": 0})
    collection.update_one({"_id": "1"}, {"$set": {"counter": 1}})

    updated = collection.find_one({"_id": "1"})
    assert updated is not None
    assert updated["counter"] == 1


def test_mongomock_delete(mongomock_client: mongomock.MongoClient) -> None:
    """Verify mongomock supports delete_one."""
    db = mongomock_client["test_db"]
    collection = db["test_docs"]

    collection.insert_one({"_id": "1", "name": "To Delete"})
    collection.delete_one({"_id": "1"})

    found = collection.find_one({"_id": "1"})
    assert found is None


def test_mongomock_insert_many_and_count(
    mongomock_client: mongomock.MongoClient,
) -> None:
    """Verify mongomock supports insert_many and count_documents."""
    db = mongomock_client["test_db"]
    collection = db["test_docs"]

    docs = [
        {"_id": "1", "group": "A"},
        {"_id": "2", "group": "A"},
        {"_id": "3", "group": "B"},
    ]
    collection.insert_many(docs)

    count_a = collection.count_documents({"group": "A"})
    assert count_a == 2

    count_all = collection.count_documents({})
    assert count_all == 3
