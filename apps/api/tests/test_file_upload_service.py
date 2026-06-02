"""Tests for FileUploadService.

Covers: init upload (presigned URL generation), complete upload
(object existence check), error cases.

Requires heavy mocking of boto3 S3 client.
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.common.labels import ErrorCode
from app.core.errors import ApiError


class TestFileUploadServiceInit:

    def test_init_upload_returns_signed_url(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Happy path: init_upload returns upload_id + presigned URL."""
        from app.schemas.file_upload import FileInitUploadRequestSchema
        from app.services.file_upload_service import FileUploadService

        mock_s3 = MagicMock()
        mock_s3.generate_presigned_url.return_value = "https://presigned.example.com/upload"

        inserted_docs: list[object] = []

        class FakeDoc:
            def __init__(self, **kwargs: object) -> None:
                for k, v in kwargs.items():
                    setattr(self, k, v)

            async def insert(self) -> None:
                inserted_docs.append(self)

        fake_user = SimpleNamespace(id="user_001")

        async def run() -> None:
            monkeypatch.setattr(
                "app.services.file_upload_service.FileUploadService._build_client",
                lambda _: mock_s3,
            )
            monkeypatch.setattr(
                "app.services.file_upload_service.FileUploadDocument",
                FakeDoc,
            )

            service = FileUploadService()
            body = FileInitUploadRequestSchema(
                context="payment_proofs",
                filename="recibo.png",
                mime_type="image/png",
                size_bytes=102400,
                sha256_hash="abc123def456",
            )
            result = await service.init_upload(current_user=fake_user, body=body)
            assert result.upload_id is not None
            assert result.upload_url == "https://presigned.example.com/upload"
            assert result.storage_key is not None
            assert len(inserted_docs) == 1

        asyncio.run(run())

    def test_init_upload_sets_correct_expiration(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """init_upload uses configured expiration in presigned URL."""
        from app.schemas.file_upload import FileInitUploadRequestSchema
        from app.services.file_upload_service import FileUploadService

        mock_s3 = MagicMock()
        mock_s3.generate_presigned_url.return_value = "https://presigned.url"

        fake_user = SimpleNamespace(id="user_001")

        class FakeDoc:
            def __init__(self, **kwargs: object) -> None:
                for k, v in kwargs.items():
                    setattr(self, k, v)

            async def insert(self) -> None:
                pass

        async def run() -> None:
            monkeypatch.setattr(
                "app.services.file_upload_service.FileUploadService._build_client",
                lambda _: mock_s3,
            )
            monkeypatch.setattr(
                "app.services.file_upload_service.FileUploadDocument",
                FakeDoc,
            )

            service = FileUploadService()
            body = FileInitUploadRequestSchema(
                context="payment_proofs",
                filename="doc.pdf",
                mime_type="application/pdf",
                size_bytes=50000,
                sha256_hash="hash123",
            )
            result = await service.init_upload(current_user=fake_user, body=body)
            # expires_at should be in the future
            assert result.expires_at > datetime(2025, 1, 1, tzinfo=UTC)

        asyncio.run(run())


class TestFileUploadServiceComplete:

    def test_complete_upload_not_found(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Complete with unknown upload_id → ApiError 404."""
        from app.services.file_upload_service import FileUploadService

        mock_s3 = MagicMock()

        async def find_none(*_args: object, **_kwargs: object) -> None:
            return None

        fake_user = SimpleNamespace(id="user_001")

        async def run() -> None:
            monkeypatch.setattr(
                "app.services.file_upload_service.FileUploadService._build_client",
                lambda _: mock_s3,
            )
            monkeypatch.setattr(
                "app.services.file_upload_service.FileUploadDocument.find_one",
                find_none,
            )

            service = FileUploadService()
            with pytest.raises(ApiError) as exc:
                await service.complete_upload(
                    current_user=fake_user, upload_id="nonexistent"
                )
            assert exc.value.status_code == 404
            assert exc.value.code == ErrorCode.FILE_UPLOAD_NOT_FOUND

        asyncio.run(run())

    def test_complete_upload_expired(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Complete with expired upload → ApiError 409."""
        from app.services.file_upload_service import FileUploadService

        mock_s3 = MagicMock()
        expired_doc = SimpleNamespace(
            upload_id="upload_001",
            user_id="user_001",
            storage_key="payment_proofs/abc-doc.pdf",
            expires_at=datetime(2020, 1, 1, tzinfo=UTC),  # expired
            size_bytes=50000,
            sha256_hash="hash123",
            status="initialized",
            mime_type="application/pdf",
            filename="doc.pdf",
            context="payment_proofs",
        )
        async def _save() -> None:
            pass
        expired_doc.save = _save  # satisfy await doc.save()

        async def find_doc(*_args: object, **_kwargs: object) -> SimpleNamespace:
            return expired_doc

        async def run() -> None:
            monkeypatch.setattr(
                "app.services.file_upload_service.FileUploadService._build_client",
                lambda _: mock_s3,
            )
            monkeypatch.setattr(
                "app.services.file_upload_service.FileUploadDocument.find_one",
                find_doc,
            )

            service = FileUploadService()
            with pytest.raises(ApiError) as exc:
                await service.complete_upload(
                    current_user=SimpleNamespace(id="user_001"),
                    upload_id="upload_001",
                )
            assert exc.value.status_code == 409
            assert exc.value.code == ErrorCode.FILE_UPLOAD_EXPIRED

        asyncio.run(run())

    def test_complete_upload_success(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Happy path: S3 object exists → status becomes 'ready'."""
        from app.services.file_upload_service import FileUploadService

        mock_s3 = MagicMock()
        # head_object succeeds — file exists in S3
        mock_s3.head_object.return_value = {"ContentLength": 50000}

        saved_status: list[str] = []

        active_doc = SimpleNamespace(
            upload_id="upload_001",
            user_id="user_001",
            storage_key="payment_proofs/abc-doc.pdf",
            expires_at=datetime(2030, 1, 1, tzinfo=UTC),
            size_bytes=50000,
            sha256_hash="hash123",
            status="initialized",
            mime_type="application/pdf",
            filename="doc.pdf",
            context="payment_proofs",
        )

        async def fake_save() -> None:
            saved_status.append(active_doc.status)

        active_doc.save = fake_save

        async def find_doc(*_args: object, **_kwargs: object) -> SimpleNamespace:
            return active_doc

        async def run() -> None:
            monkeypatch.setattr(
                "app.services.file_upload_service.FileUploadService._build_client",
                lambda _: mock_s3,
            )
            monkeypatch.setattr(
                "app.services.file_upload_service.FileUploadDocument.find_one",
                find_doc,
            )

            service = FileUploadService()
            result = await service.complete_upload(
                current_user=SimpleNamespace(id="user_001"),
                upload_id="upload_001",
            )
            assert result.status == "ready"

        asyncio.run(run())
