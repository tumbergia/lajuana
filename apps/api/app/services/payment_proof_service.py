from beanie import PydanticObjectId

from app.common.enums import PaymentStatus
from app.common.labels import ErrorCode
from app.core.errors import ApiError
from app.documents import PaymentProofDocument, ReservationDocument
from app.schemas.payment_proof import PaymentProofCreateSchema
from app.services.storage import LocalStorageAdapter

ALLOWED_CONTENT_TYPES = {
    "image/jpeg",
    "image/png",
    "application/pdf",
}


class PaymentProofService:
    def __init__(self) -> None:
        self.storage = LocalStorageAdapter()

    async def create(
        self,
        reservation_id: str,
        payload: PaymentProofCreateSchema,
        actor_id: PydanticObjectId | None = None,
    ) -> PaymentProofDocument:
        reservation = await ReservationDocument.get(reservation_id)
        if reservation is None:
            raise ApiError(
                status_code=404,
                code="reservation.not_found",
                message="Reserva no encontrada.",
            )
        if not payload.content_base64:
            raise ApiError(
                status_code=422,
                code=ErrorCode.FILE_STORAGE_REQUIRED,
                message="Se requiere contenido para almacenar el comprobante.",
            )
        if payload.content_type not in ALLOWED_CONTENT_TYPES:
            raise ApiError(
                status_code=422,
                code="payment_proof.invalid_content_type",
                message="El tipo de contenido no está permitido.",
            )

        storage_key = await self.storage.store_base64(
            reservation_id=reservation_id,
            filename=payload.filename,
            content_base64=payload.content_base64,
        )

        doc = PaymentProofDocument(
            reservation_id=reservation.id,
            storage_key=storage_key,
            filename=payload.filename,
            content_type=payload.content_type,
            size_bytes=payload.size_bytes,
            sha256=payload.sha256,
            uploaded_by=actor_id,
            status=PaymentStatus.RECEIVED,
        )
        await doc.insert()
        reservation.payment_proof_ids.append(doc.id)
        reservation.payment_status = PaymentStatus.RECEIVED
        await reservation.save()
        return doc
