import asyncio
import base64
import io
import logging
from pathlib import Path

from app.core.config import settings

logger = logging.getLogger(__name__)


class LocalStorageAdapter:
    def __init__(self) -> None:
        self.root = Path(settings.storage_local_root)

    async def store_base64(self, *, reservation_id: str, filename: str, content_base64: str) -> str:
        prefix = settings.storage_local_payment_proofs_prefix
        directory = self.root / prefix / reservation_id
        directory.mkdir(parents=True, exist_ok=True)
        file_path = directory / filename
        file_path.write_bytes(base64.b64decode(content_base64))
        return str(file_path.relative_to(self.root))

    async def read_bytes(self, storage_key: str) -> bytes | None:
        file_path = self.root / storage_key
        if not file_path.exists():
            return None
        return file_path.read_bytes()

    async def exists(self, storage_key: str) -> bool:
        return (self.root / storage_key).is_file()

    async def write_bytes(self, storage_key: str, data: bytes) -> str:
        file_path = self.root / storage_key
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_bytes(data)
        return str(file_path.relative_to(self.root))

    async def delete(self, storage_key: str) -> None:
        file_path = self.root / storage_key
        if file_path.exists():
            file_path.unlink()


class S3StorageAdapter:
    def __init__(self) -> None:
        self.bucket = settings.storage_s3_bucket
        self.region = settings.storage_s3_region
        self._client = self._build_client()

    def _build_client(self):
        try:
            import boto3
            from botocore.config import Config
        except ImportError:
            raise RuntimeError(
                "S3 credentials detected (storage_s3_access_key_id set) but boto3 is not installed. "
                "Install boto3 or unset S3 credentials to use LocalStorageAdapter.",
            )

        return boto3.client(
            "s3",
            region_name=self.region,
            endpoint_url=settings.storage_s3_endpoint_url,
            aws_access_key_id=settings.storage_s3_access_key_id,
            aws_secret_access_key=settings.storage_s3_secret_access_key,
            config=Config(signature_version="s3v4"),
        )

    async def read_bytes(self, storage_key: str) -> bytes | None:
        try:
            buf = io.BytesIO()
            await asyncio.to_thread(
                self._client.download_fileobj,
                Bucket=self.bucket, Key=storage_key, Fileobj=buf,
            )
            return buf.getvalue()
        except Exception:
            return None

    async def exists(self, storage_key: str) -> bool:
        try:
            await asyncio.to_thread(
                self._client.head_object, Bucket=self.bucket, Key=storage_key,
            )
            return True
        except Exception:
            return False

    async def write_bytes(self, storage_key: str, data: bytes) -> str:
        await asyncio.to_thread(
            self._client.put_object,
            Bucket=self.bucket, Key=storage_key, Body=data,
        )
        return storage_key

    async def delete(self, storage_key: str) -> None:
        try:
            await asyncio.to_thread(
                self._client.delete_object,
                Bucket=self.bucket, Key=storage_key,
            )
        except Exception:
            logger.warning(
                "[s3] Failed to delete object | key=%s",
                storage_key,
                exc_info=True,
            )


def get_storage_adapter() -> LocalStorageAdapter | S3StorageAdapter:
    if settings.storage_s3_access_key_id and settings.storage_s3_secret_access_key:
        return S3StorageAdapter()
    return LocalStorageAdapter()
