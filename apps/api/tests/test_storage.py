"""Tests for LocalStorageAdapter (real filesystem via tmp_path).

Covers: store_base64, read_bytes, write_bytes, delete.
"""

from __future__ import annotations

import asyncio
import base64
import os

import pytest


class TestLocalStorageAdapter:

    def test_store_base64_writes_file(self, monkeypatch: pytest.MonkeyPatch, tmp_path: str) -> None:
        """Base64 content → file created on disk at correct path."""
        from app.services.storage import LocalStorageAdapter

        monkeypatch.setattr(
            "app.services.storage.settings.storage_local_root",
            str(tmp_path),
        )
        monkeypatch.setattr(
            "app.services.storage.settings.storage_local_payment_proofs_prefix",
            "payment_proofs",
        )

        adapter = LocalStorageAdapter()
        content = base64.b64encode(b"hello world").decode()

        async def run() -> None:
            key = await adapter.store_base64(
                reservation_id="res_001",
                filename="proof.png",
                content_base64=content,
            )
            assert "payment_proofs" in key
            assert "res_001" in key
            assert key.endswith("proof.png")
            full_path = tmp_path / key
            assert os.path.exists(full_path)
            with open(full_path, "rb") as f:
                assert f.read() == b"hello world"

        asyncio.run(run())

    def test_read_bytes_returns_content(self, monkeypatch: pytest.MonkeyPatch, tmp_path: str) -> None:
        """Existing file → content returned as bytes."""
        from app.services.storage import LocalStorageAdapter

        monkeypatch.setattr(
            "app.services.storage.settings.storage_local_root",
            str(tmp_path),
        )

        # Create file directly
        test_dir = tmp_path / "payment_proofs" / "res_001"
        test_dir.mkdir(parents=True)
        test_file = test_dir / "doc.txt"
        test_file.write_text("test content")

        adapter = LocalStorageAdapter()

        async def run() -> None:
            result = await adapter.read_bytes("payment_proofs/res_001/doc.txt")
            assert result == b"test content"

        asyncio.run(run())

    def test_read_bytes_nonexistent_returns_none(self, monkeypatch: pytest.MonkeyPatch, tmp_path: str) -> None:
        """Non-existent key → returns None."""
        from app.services.storage import LocalStorageAdapter

        monkeypatch.setattr(
            "app.services.storage.settings.storage_local_root",
            str(tmp_path),
        )

        adapter = LocalStorageAdapter()

        async def run() -> None:
            result = await adapter.read_bytes("nonexistent/file.txt")
            assert result is None

        asyncio.run(run())

    def test_write_bytes_creates_file(self, monkeypatch: pytest.MonkeyPatch, tmp_path: str) -> None:
        """write_bytes creates file and returns relative path."""
        from app.services.storage import LocalStorageAdapter

        monkeypatch.setattr(
            "app.services.storage.settings.storage_local_root",
            str(tmp_path),
        )

        adapter = LocalStorageAdapter()

        async def run() -> None:
            key = await adapter.write_bytes("logs/event.log", b"event data")
            # Path separator is platform-dependent (Windows uses \\)
            assert "event.log" in key
            assert "logs" in key
            full_path = tmp_path / key
            assert os.path.exists(full_path)
            with open(full_path, "rb") as f:
                assert f.read() == b"event data"

        asyncio.run(run())

    def test_delete_removes_file(self, monkeypatch: pytest.MonkeyPatch, tmp_path: str) -> None:
        """delete removes file from disk."""
        from app.services.storage import LocalStorageAdapter

        monkeypatch.setattr(
            "app.services.storage.settings.storage_local_root",
            str(tmp_path),
        )

        test_file = tmp_path / "to_delete.txt"
        test_file.write_text("delete me")

        adapter = LocalStorageAdapter()

        async def run() -> None:
            await adapter.delete("to_delete.txt")
            assert not os.path.exists(test_file)

        asyncio.run(run())
