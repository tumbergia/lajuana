"""Tests del BaseService genérico CRUD.

Verifica que get-or-404, create, update, soft_delete, restore, list, count
funcionen correctamente con un documento Beanie mockeado.
"""

# ruff: noqa: SLF001

import asyncio
import os

os.environ["APP_SKIP_DB_INIT"] = "true"

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

from app.common.labels import ErrorCode
from app.core.errors import ApiError
from app.services.base_service import BaseService


class FakeDoc:
    """Simula un documento Beanie para tests del BaseService."""

    def __init__(self, **kwargs: object) -> None:
        for k, v in kwargs.items():
            setattr(self, k, v)
        self._insert_called = False
        self._save_called = False

    async def insert(self) -> None:
        self._insert_called = True

    async def save(self) -> None:
        self._save_called = True


class CreateSchema:
    def __init__(self, **kwargs: object) -> None:
        self._data = dict(kwargs)

    def model_dump(self) -> dict[str, object]:
        return dict(self._data)


class UpdateSchema:
    def __init__(self, **kwargs: object) -> None:
        self._data = {k: v for k, v in kwargs.items() if v is not None}

    def model_dump(self, exclude_none: bool = True) -> dict[str, object]:
        if exclude_none:
            return {k: v for k, v in self._data.items() if v is not None}
        return dict(self._data)


class ConcreteService(BaseService[FakeDoc, CreateSchema, UpdateSchema]):  # type: ignore[type-arg]
    document_class = FakeDoc  # type: ignore[assignment]
    not_found_code = ErrorCode.USER_NOT_FOUND
    not_found_message = "Recurso de prueba no encontrado."


# ======================================================================
# TESTS
# ======================================================================


class TestGet:
    def test_get_returns_doc_when_exists(self) -> None:
        async def run() -> None:
            doc = FakeDoc(id="abc", name="test")
            FakeDoc.get = AsyncMock(return_value=doc)  # type: ignore[assignment]
            svc = ConcreteService()
            result = await svc.get("abc")
            assert result.id == "abc"
            assert result.name == "test"

        asyncio.run(run())

    def test_get_raises_404_when_not_found(self) -> None:
        async def run() -> None:
            FakeDoc.get = AsyncMock(return_value=None)  # type: ignore[assignment]
            svc = ConcreteService()
            try:
                await svc.get("nonexistent")
                assert False, "Expected ApiError"
            except ApiError as e:
                assert e.status_code == 404
                assert e.code == ErrorCode.USER_NOT_FOUND

        asyncio.run(run())


class TestCreate:
    def test_create_inserts_doc(self) -> None:
        async def run() -> None:
            payload = CreateSchema(name="new", value=42)
            svc = ConcreteService()
            result = await svc.create(payload)
            assert result._insert_called is True
            assert result.name == "new"
            assert result.value == 42

        asyncio.run(run())


class TestUpdate:
    def test_update_partial(self) -> None:
        async def run() -> None:
            doc = FakeDoc(id="abc", name="old", value=1)
            FakeDoc.get = AsyncMock(return_value=doc)  # type: ignore[assignment]
            payload = UpdateSchema(name="updated", value=None)
            svc = ConcreteService()
            result = await svc.update("abc", payload)
            assert result.name == "updated"
            assert result.value == 1  # unchanged (excluded None)
            assert result._save_called is True

        asyncio.run(run())

    def test_update_raises_404_if_missing(self) -> None:
        async def run() -> None:
            FakeDoc.get = AsyncMock(return_value=None)  # type: ignore[assignment]
            svc = ConcreteService()
            try:
                await svc.update("x", UpdateSchema(name="x"))
                assert False, "Expected ApiError"
            except ApiError as e:
                assert e.status_code == 404

        asyncio.run(run())


class TestSoftDelete:
    def test_soft_delete_sets_deleted_at(self) -> None:
        async def run() -> None:
            doc = FakeDoc(id="abc", deleted_at=None)
            FakeDoc.get = AsyncMock(return_value=doc)  # type: ignore[assignment]
            svc = ConcreteService()
            before = datetime.now(UTC)
            result = await svc.soft_delete("abc")
            after = datetime.now(UTC)
            assert result.deleted_at is not None
            assert before <= result.deleted_at <= after
            assert result._save_called is True

        asyncio.run(run())

    def test_soft_delete_raises_404_if_missing(self) -> None:
        async def run() -> None:
            FakeDoc.get = AsyncMock(return_value=None)  # type: ignore[assignment]
            svc = ConcreteService()
            try:
                await svc.soft_delete("x")
                assert False, "Expected ApiError"
            except ApiError:
                pass

        asyncio.run(run())


class TestRestore:
    def test_restore_clears_deleted_at(self) -> None:
        async def run() -> None:
            doc = FakeDoc(id="abc", deleted_at=datetime.now(UTC))
            FakeDoc.get = AsyncMock(return_value=doc)  # type: ignore[assignment]
            svc = ConcreteService()
            result = await svc.restore("abc")
            assert result.deleted_at is None
            assert result._save_called is True

        asyncio.run(run())


class TestListAndCount:
    def test_list_excludes_deleted_by_default(self) -> None:
        async def run() -> None:
            fake_cursor = MagicMock()
            fake_cursor.skip.return_value = fake_cursor
            fake_cursor.limit.return_value = fake_cursor
            fake_cursor.to_list = AsyncMock(return_value=[FakeDoc(id="a"), FakeDoc(id="b")])
            FakeDoc.find = MagicMock(return_value=fake_cursor)  # type: ignore[assignment]
            svc = ConcreteService()
            result = await svc.list()
            assert len(result) == 2
            FakeDoc.find.assert_called_once_with({"deleted_at": None})

        asyncio.run(run())

    def test_count_excludes_deleted_by_default(self) -> None:
        async def run() -> None:
            fake_cursor = MagicMock()
            fake_cursor.count = AsyncMock(return_value=5)
            FakeDoc.find = MagicMock(return_value=fake_cursor)  # type: ignore[assignment]
            svc = ConcreteService()
            result = await svc.count()
            assert result == 5
            FakeDoc.find.assert_called_once_with({"deleted_at": None})

        asyncio.run(run())

    def test_list_includes_deleted_when_requested(self) -> None:
        async def run() -> None:
            fake_cursor = MagicMock()
            fake_cursor.skip.return_value = fake_cursor
            fake_cursor.limit.return_value = fake_cursor
            fake_cursor.to_list = AsyncMock(return_value=[FakeDoc(id="a", deleted_at=datetime.now(UTC))])
            FakeDoc.find = MagicMock(return_value=fake_cursor)  # type: ignore[assignment]
            svc = ConcreteService()
            result = await svc.list(include_deleted=True)
            assert len(result) == 1
            FakeDoc.find.assert_called_once_with({})

        asyncio.run(run())
