from datetime import UTC, datetime, timedelta
from uuid import uuid4

from app.common.labels import ErrorCode
from app.core.config import settings
from app.core.errors import ApiError
from app.documents import FileUploadDocument, UserDocument
from app.schemas.file_upload import (
    FileCompleteUploadResponseSchema,
    FileInitUploadRequestSchema,
    FileInitUploadResponseSchema,
)


class FileUploadService:
    def __init__(self) -> None:
        self.bucket = settings.storage_s3_bucket
        self.region = settings.storage_s3_region
        self._client = self._build_client()

    def _build_client(self):
        try:
            import boto3
            from botocore.config import Config
        except ImportError:
            return _FallbackS3Client(bucket=self.bucket, region=self.region)

        return boto3.client(
            "s3",
            region_name=self.region,
            endpoint_url=settings.storage_s3_endpoint_url,
            aws_access_key_id=settings.storage_s3_access_key_id,
            aws_secret_access_key=settings.storage_s3_secret_access_key,
            config=Config(signature_version="s3v4"),
        )

    async def init_upload(
        self, *, current_user: UserDocument, body: FileInitUploadRequestSchema
    ) -> FileInitUploadResponseSchema:
        upload_id = str(uuid4())
        storage_key = f"{body.context}/{upload_id}-{body.filename}"
        expires_in = settings.storage_s3_presign_expiration_seconds
        expires_at = datetime.now(UTC) + timedelta(seconds=expires_in)
        upload_url = self._client.generate_presigned_url(
            "put_object",
            Params={
                "Bucket": self.bucket,
                "Key": storage_key,
                "ContentType": body.mime_type,
            },
            ExpiresIn=expires_in,
        )

        doc = FileUploadDocument(
            upload_id=upload_id,
            user_id=str(current_user.id),
            context=body.context,
            filename=body.filename,
            mime_type=body.mime_type,
            size_bytes=body.size_bytes,
            sha256_hash=body.sha256_hash,
            storage_key=storage_key,
            upload_url=upload_url,
            expires_at=expires_at,
            status="initialized",
        )
        await doc.insert()
        return FileInitUploadResponseSchema(
            upload_id=upload_id,
            storage_key=storage_key,
            upload_url=upload_url,
            expires_at=expires_at,
        )

    async def complete_upload(
        self, *, current_user: UserDocument, upload_id: str
    ) -> FileCompleteUploadResponseSchema:
        doc = await FileUploadDocument.find_one({"upload_id": upload_id})
        if doc is None or doc.user_id != str(current_user.id):
            raise ApiError(
                status_code=404,
                code=ErrorCode.FILE_UPLOAD_NOT_FOUND,
                message="Upload no encontrado.",
            )
        now = datetime.now(UTC)
        if doc.expires_at < now:
            doc.status = "expired"
            await doc.save()
            raise ApiError(
                status_code=409,
                code=ErrorCode.FILE_UPLOAD_EXPIRED,
                message="Upload expirado.",
            )
        try:
            self._client.head_object(Bucket=self.bucket, Key=doc.storage_key)
        except Exception as exc:
            raise ApiError(
                status_code=409,
                code=ErrorCode.FILE_UPLOAD_NOT_READY,
                message="Archivo aun no disponible en almacenamiento.",
            ) from exc

        doc.status = "ready"
        await doc.save()
        return FileCompleteUploadResponseSchema(
            upload_id=doc.upload_id,
            storage_key=doc.storage_key,
            size_bytes=doc.size_bytes,
            sha256_hash=doc.sha256_hash,
            status=doc.status,
        )


class _FallbackS3Client:
    def __init__(self, *, bucket: str, region: str) -> None:
        self.bucket = bucket
        self.region = region

    def generate_presigned_url(self, *_args, **kwargs) -> str:
        key = kwargs.get("Params", {}).get("Key", "unknown")
        return f"https://{self.bucket}.s3.{self.region}.amazonaws.com/{key}?fallback=true"

    def head_object(self, **_kwargs) -> None:
        return None
