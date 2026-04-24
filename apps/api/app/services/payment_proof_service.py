from beanie import PydanticObjectId

from app.common.enums import PaymentStatus
from app.common.labels import ErrorCode
from app.core.errors import ApiError
from app.documents import FileUploadDocument, PaymentProofDocument, ReservationDocument
from app.schemas.payment_proof import PaymentProofCreateSchema, PaymentProofUpdateSchema

ALLOWED_CONTENT_TYPES = {
    "image/jpeg",
    "image/png",
    "application/pdf",
}


class PaymentProofService:
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
                code=ErrorCode.RESERVATION_NOT_FOUND,
                message="Reserva no encontrada.",
            )
        if not payload.storage_key:
            raise ApiError(
                status_code=400,
                code=ErrorCode.PAYMENT_PROOF_STORAGE_KEY_REQUIRED,
                message="Se requiere storage_key para almacenar el comprobante.",
            )
        if payload.content_type not in ALLOWED_CONTENT_TYPES:
            raise ApiError(
                status_code=400,
                code=ErrorCode.PAYMENT_PROOF_INVALID_CONTENT_TYPE,
                message="El tipo de contenido no esta permitido.",
            )
        upload = await FileUploadDocument.find_one(
            FileUploadDocument.storage_key == payload.storage_key
        )
        if upload is None or upload.status != "ready":
            raise ApiError(
                status_code=409,
                code=ErrorCode.FILE_UPLOAD_NOT_READY,
                message="El archivo del comprobante no esta listo para consolidar.",
            )

        doc = PaymentProofDocument(
            reservation_id=reservation.id,
            storage_key=payload.storage_key,
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

    async def get(self, payment_proof_id: str) -> PaymentProofDocument:
        doc = await PaymentProofDocument.get(payment_proof_id)
        if doc is None:
            raise ApiError(
                status_code=404,
                code=ErrorCode.PAYMENT_PROOF_NOT_FOUND,
                message="Comprobante no encontrado.",
            )
        return doc

    async def update(
        self,
        payment_proof_id: str,
        payload: PaymentProofUpdateSchema,
    ) -> PaymentProofDocument:
        doc = await self.get(payment_proof_id)
        updates = payload.model_dump(exclude_none=True)
        if "reservation_id" in updates:
            reservation = await ReservationDocument.get(updates["reservation_id"])
            if reservation is None:
                raise ApiError(
                    status_code=404,
                    code=ErrorCode.RESERVATION_NOT_FOUND,
                    message="Reserva no encontrada.",
                )
            if reservation.id != doc.reservation_id:
                raise ApiError(
                    status_code=409,
                    code=ErrorCode.PAYMENT_PROOF_RESERVATION_MISMATCH,
                    message="El comprobante no coincide con la reserva informada.",
                )
        for field in ("status", "filename", "content_type", "size_bytes", "sha256"):
            if field in updates:
                setattr(doc, field, updates[field])
        await doc.save()
        return doc
