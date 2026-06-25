import re
from uuid import uuid4

from beanie import PydanticObjectId
from fastapi import UploadFile

from app.common.enums import UserRole
from app.common.labels import ErrorCode
from app.core.errors import ApiError
from app.documents import ReservationDocument, ServiceLogDocument, ServiceLogEventType
from app.documents.service_log_document import ServiceLogPhoto
from app.schemas.service_log import (
    ServiceLogCreateSchema,
    ServiceLogPhotoInputSchema,
    ServiceLogPhotoUploadResponseSchema,
    ServiceLogUpdateSchema,
)
from app.services.base_service import BaseService
from app.services.storage import get_storage_adapter

MAX_PHOTOS_PER_LOG = 10
MAX_PHOTO_SIZE_BYTES = 5 * 1024 * 1024
ALLOWED_PHOTO_CONTENT_TYPES = frozenset(
    {"image/jpeg", "image/png", "image/webp", "image/jpg"},
)


class ServiceLogService(BaseService[ServiceLogDocument, ServiceLogCreateSchema, ServiceLogUpdateSchema]):
    document_class = ServiceLogDocument
    not_found_code = ErrorCode.LOG_NOT_FOUND
    not_found_message = "Log no encontrado."

    @staticmethod
    def _ensure_mutable(
        doc: ServiceLogDocument,
        *,
        actor_role: UserRole,
        for_delete: bool = False,
    ) -> None:
        is_note = doc.event_type == ServiceLogEventType.NOTE
        if is_note:
            return
        if actor_role != UserRole.ADMIN:
            action = "eliminar" if for_delete else "modificar"
            raise ApiError(
                status_code=403,
                code=ErrorCode.AUTH_FORBIDDEN,
                message=f"Solo un administrador puede {action} entradas automáticas.",
            )

    @staticmethod
    def _sanitize_filename(filename: str) -> str:
        base = filename.rsplit("/", 1)[-1].rsplit("\\", 1)[-1]
        cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", base).strip("._")
        return cleaned or "foto.jpg"

    @staticmethod
    def _expected_photo_prefix(reservation_id: str) -> str:
        return f"service_logs/{reservation_id}/"

    def _validate_photo_inputs(
        self,
        reservation_id: str,
        photos: list[ServiceLogPhotoInputSchema],
    ) -> list[ServiceLogPhoto]:
        if len(photos) > MAX_PHOTOS_PER_LOG:
            raise ApiError(
                status_code=400,
                code=ErrorCode.LOG_PHOTO_LIMIT,
                message=f"Máximo {MAX_PHOTOS_PER_LOG} fotos por entrada.",
            )
        prefix = self._expected_photo_prefix(reservation_id)
        validated: list[ServiceLogPhoto] = []
        for photo in photos:
            content_type = photo.content_type.lower()
            if content_type not in ALLOWED_PHOTO_CONTENT_TYPES:
                raise ApiError(
                    status_code=400,
                    code=ErrorCode.LOG_PHOTO_INVALID_TYPE,
                    message="Solo se permiten imágenes JPEG, PNG o WebP.",
                )
            if not photo.storage_key.startswith(prefix):
                raise ApiError(
                    status_code=400,
                    code=ErrorCode.LOG_PHOTO_NOT_FOUND,
                    message="La foto no pertenece a esta reserva.",
                )
            validated.append(
                ServiceLogPhoto(
                    storage_key=photo.storage_key,
                    filename=photo.filename,
                    content_type=content_type,
                    size_bytes=photo.size_bytes,
                )
            )
        return validated

    async def _delete_photos(self, photos: list[ServiceLogPhoto]) -> None:
        if not photos:
            return
        adapter = get_storage_adapter()
        for photo in photos:
            try:
                await adapter.delete(photo.storage_key)
            except Exception:
                continue

    async def upload_photo(
        self,
        *,
        reservation_id: str,
        upload: UploadFile,
    ) -> ServiceLogPhotoUploadResponseSchema:
        reservation = await ReservationDocument.get(reservation_id)
        if reservation is None:
            raise ApiError(
                status_code=404,
                code=ErrorCode.RESERVATION_NOT_FOUND,
                message="Reserva no encontrada.",
            )

        content_type = (upload.content_type or "application/octet-stream").lower()
        if content_type not in ALLOWED_PHOTO_CONTENT_TYPES:
            raise ApiError(
                status_code=400,
                code=ErrorCode.LOG_PHOTO_INVALID_TYPE,
                message="Solo se permiten imágenes JPEG, PNG o WebP.",
            )

        data = await upload.read()
        if not data:
            raise ApiError(
                status_code=400,
                code=ErrorCode.LOG_PHOTO_INVALID_TYPE,
                message="Archivo vacío.",
            )
        if len(data) > MAX_PHOTO_SIZE_BYTES:
            raise ApiError(
                status_code=400,
                code=ErrorCode.LOG_PHOTO_LIMIT,
                message="La imagen supera el tamaño máximo permitido (5 MB).",
            )

        filename = self._sanitize_filename(upload.filename or "foto.jpg")
        storage_key = f"{self._expected_photo_prefix(reservation_id)}{uuid4().hex}-{filename}"
        adapter = get_storage_adapter()
        await adapter.write_bytes(storage_key, data)

        return ServiceLogPhotoUploadResponseSchema(
            storage_key=storage_key,
            filename=filename,
            content_type=content_type,
            size_bytes=len(data),
        )

    async def get_photo_download(
        self,
        log_id: str,
        photo_index: int,
    ) -> tuple[str, bytes]:
        doc = await self.get(log_id)
        if photo_index < 0 or photo_index >= len(doc.photos):
            raise ApiError(
                status_code=404,
                code=ErrorCode.LOG_PHOTO_NOT_FOUND,
                message="Foto no encontrada.",
            )
        photo = doc.photos[photo_index]
        adapter = get_storage_adapter()
        file_bytes = await adapter.read_bytes(photo.storage_key)
        if file_bytes is None:
            raise ApiError(
                status_code=404,
                code=ErrorCode.LOG_PHOTO_NOT_FOUND,
                message="Archivo no encontrado en almacenamiento.",
            )
        return photo.content_type, file_bytes

    async def list_by_reservation(
        self,
        reservation_id: str,
        *,
        limit: int = 200,
        skip: int = 0,
    ) -> list[ServiceLogDocument]:
        reservation = await ReservationDocument.get(reservation_id)
        if reservation is None:
            raise ApiError(
                status_code=404,
                code=ErrorCode.RESERVATION_NOT_FOUND,
                message="Reserva no encontrada.",
            )
        return await ServiceLogDocument.find(
            {
                "reservation_id": reservation.id,
                "deleted_at": None,
            },
        ).sort([("happened_at", -1)]).skip(skip).limit(limit).to_list()

    async def create(
        self,
        payload: ServiceLogCreateSchema,
        *,
        actor_id: PydanticObjectId | None = None,
    ) -> ServiceLogDocument:
        reservation = await ReservationDocument.get(payload.reservation_id)
        if reservation is None:
            raise ApiError(
                status_code=404,
                code=ErrorCode.RESERVATION_NOT_FOUND,
                message="Reserva no encontrada.",
            )
        if payload.event_type == ServiceLogEventType.CHECKPOINT and not payload.checkpoint_name:
            raise ApiError(
                status_code=400,
                code=ErrorCode.LOG_CHECKPOINT_NAME_REQUIRED,
                message="checkpoint_name es obligatorio para event_type checkpoint.",
            )
        photos = self._validate_photo_inputs(str(reservation.id), payload.photos)
        if photos and payload.event_type != ServiceLogEventType.NOTE:
            raise ApiError(
                status_code=400,
                code=ErrorCode.LOG_PHOTO_INVALID_TYPE,
                message="Solo las notas manuales admiten fotos.",
            )
        doc = ServiceLogDocument(
            reservation_id=reservation.id,
            event_type=payload.event_type,
            happened_at=payload.happened_at,
            checkpoint_name=payload.checkpoint_name,
            notes=payload.notes,
            related_participant_id=payload.related_participant_id,
            related_equine_id=payload.related_equine_id,
            created_by=actor_id,
            photos=photos,
        )
        await doc.insert()
        return doc

    async def update(
        self,
        log_id: str,
        payload: ServiceLogUpdateSchema,
        *,
        actor_role: UserRole,
    ) -> ServiceLogDocument:
        doc = await self.get(log_id)
        if doc.event_type != ServiceLogEventType.NOTE:
            raise ApiError(
                status_code=403,
                code=ErrorCode.AUTH_FORBIDDEN,
                message="Solo las notas manuales pueden editarse.",
            )
        self._ensure_mutable(doc, actor_role=actor_role)
        updates = payload.model_dump(exclude_none=True)
        event_type = updates.get("event_type", doc.event_type)
        checkpoint_name = updates.get("checkpoint_name", doc.checkpoint_name)
        if event_type == ServiceLogEventType.CHECKPOINT and not checkpoint_name:
            raise ApiError(
                status_code=400,
                code=ErrorCode.LOG_CHECKPOINT_NAME_REQUIRED,
                message="checkpoint_name es obligatorio para event_type checkpoint.",
            )
        if "photos" in updates:
            new_photos = self._validate_photo_inputs(
                str(doc.reservation_id),
                payload.photos or [],
            )
            removed = [
                photo
                for photo in doc.photos
                if photo.storage_key not in {p.storage_key for p in new_photos}
            ]
            await self._delete_photos(removed)
            doc.photos = new_photos
            updates.pop("photos")
        for field, value in updates.items():
            setattr(doc, field, value)
        await doc.save()
        return doc

    async def soft_delete(
        self,
        log_id: str,
        *,
        actor_role: UserRole,
    ) -> ServiceLogDocument:
        doc = await self.get(log_id)
        self._ensure_mutable(doc, actor_role=actor_role, for_delete=True)
        await self._delete_photos(doc.photos)
        return await super().soft_delete(log_id)
