from hashlib import sha256

from beanie import PydanticObjectId

from app.common.enums import PaymentStatus, ReservationStatus, UserRole
from app.common.labels import ErrorCode
from app.core.errors import ApiError
from app.documents import FileUploadDocument, PaymentProofDocument, ReservationDocument
from app.schemas.payment_proof import (
    PaymentProofCreateSchema,
    PaymentProofRejectSchema,
    PaymentProofUpdateSchema,
    PaymentProofVerifySchema,
)

ALLOWED_CONTENT_TYPES = {
    "image/jpeg",
    "image/png",
    "application/pdf",
}

ALLOWED_PAYMENT_PROOF_TRANSITIONS = {
    PaymentStatus.RECEIVED: {PaymentStatus.VERIFIED, PaymentStatus.REJECTED},
    PaymentStatus.VERIFIED: set(),
    PaymentStatus.REJECTED: set(),
    PaymentStatus.PENDING: set(),
}


class PaymentProofService:
    ATTACHABLE_RESERVATION_STATUSES = {
        ReservationStatus.PRE_RESERVED,
        ReservationStatus.PENDING_PAYMENT,
        ReservationStatus.PAYMENT_RECEIVED,
        ReservationStatus.QUOTED,
    }

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
        if "status" in updates:
            raise ApiError(
                status_code=409,
                code=ErrorCode.RESERVATION_INVALID_STATUS_TRANSITION,
                message="El estado del comprobante solo puede cambiarse en verify/reject.",
            )
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
        for field in ("filename", "content_type", "size_bytes", "sha256"):
            if field in updates:
                setattr(doc, field, updates[field])
        await doc.save()
        return doc

    async def verify_payment(
        self,
        payment_proof_id: str,
        payload: PaymentProofVerifySchema,
        *,
        actor_id: PydanticObjectId | None,
        actor_role: UserRole,
    ) -> PaymentProofDocument:
        if actor_role != UserRole.ADMIN:
            raise ApiError(
                status_code=403,
                code=ErrorCode.AUTH_FORBIDDEN,
                message="No tienes permisos para verificar comprobantes.",
            )
        if payload.confirmation_token != "VERIFY_PAYMENT":
            raise ApiError(
                status_code=400,
                code=ErrorCode.VALIDATION_ERROR,
                message="Token de confirmación inválido para verificar pago.",
            )

        doc = await self.get(payment_proof_id)
        self._ensure_transition_allowed(doc.status, PaymentStatus.VERIFIED)
        reservation = await ReservationDocument.get(doc.reservation_id)
        if reservation is None:
            raise ApiError(
                status_code=404,
                code=ErrorCode.RESERVATION_NOT_FOUND,
                message="Reserva no encontrada.",
            )

        await self._sync_proof_and_reservation_payment_status(
            doc=doc,
            reservation=reservation,
            target_status=PaymentStatus.VERIFIED,
            actor_id=actor_id,
        )
        return doc

    async def reject_payment(
        self,
        payment_proof_id: str,
        payload: PaymentProofRejectSchema,
        *,
        actor_id: PydanticObjectId | None,
        actor_role: UserRole,
    ) -> PaymentProofDocument:
        if actor_role != UserRole.ADMIN:
            raise ApiError(
                status_code=403,
                code=ErrorCode.AUTH_FORBIDDEN,
                message="No tienes permisos para rechazar comprobantes.",
            )
        if payload.confirmation_token != "REJECT_PAYMENT":
            raise ApiError(
                status_code=400,
                code=ErrorCode.VALIDATION_ERROR,
                message="Token de confirmación inválido para rechazar pago.",
            )

        doc = await self.get(payment_proof_id)
        self._ensure_transition_allowed(doc.status, PaymentStatus.REJECTED)
        reservation = await ReservationDocument.get(doc.reservation_id)
        if reservation is None:
            raise ApiError(
                status_code=404,
                code=ErrorCode.RESERVATION_NOT_FOUND,
                message="Reserva no encontrada.",
            )

        await self._sync_proof_and_reservation_payment_status(
            doc=doc,
            reservation=reservation,
            target_status=PaymentStatus.REJECTED,
            actor_id=actor_id,
        )
        return doc

    async def _sync_proof_and_reservation_payment_status(
        self,
        *,
        doc: PaymentProofDocument,
        reservation: ReservationDocument,
        target_status: PaymentStatus,
        actor_id: PydanticObjectId | None,
    ) -> None:
        previous_doc_status = doc.status
        previous_reservation_payment_status = reservation.payment_status
        previous_updated_by = reservation.updated_by

        doc.status = target_status
        reservation.payment_status = target_status
        reservation.updated_by = actor_id
        await doc.save()
        try:
            await reservation.save()
        except Exception as exc:
            doc.status = previous_doc_status
            reservation.payment_status = previous_reservation_payment_status
            reservation.updated_by = previous_updated_by
            try:
                await doc.save()
            except Exception:
                pass
            raise ApiError(
                status_code=500,
                code=ErrorCode.INTERNAL_ERROR,
                message=(
                    "No se pudo persistir la verificacion del comprobante de forma consistente."
                ),
                details={"operation": "payment_proof_status_sync", "cause": str(exc)},
            ) from exc

    def _ensure_transition_allowed(
        self,
        current_status: PaymentStatus,
        target_status: PaymentStatus,
    ) -> None:
        allowed = ALLOWED_PAYMENT_PROOF_TRANSITIONS.get(current_status, set())
        if target_status not in allowed:
            raise ApiError(
                status_code=409,
                code=ErrorCode.RESERVATION_INVALID_STATUS_TRANSITION,
                message="La transición de estado del comprobante no es válida.",
                details={"from": current_status, "to": target_status},
            )

    async def get_attachable_reservation(
        self,
        *,
        reservation_id: str | None,
        public_reservation_code: str | None,
        from_phone: str,
    ) -> ReservationDocument:
        reservation = None
        if reservation_id:
            reservation = await ReservationDocument.get(reservation_id)
        elif public_reservation_code:
            reservation = await ReservationDocument.find_one({"code": public_reservation_code})

        if reservation is None:
            raise ApiError(
                status_code=404,
                code=ErrorCode.RESERVATION_NOT_FOUND,
                message="Reserva no encontrada.",
            )

        if reservation.holder_phone and reservation.holder_phone != from_phone:
            raise ApiError(
                status_code=409,
                code=ErrorCode.RESERVATION_INVALID_HOLDER,
                message="El telefono no coincide con la reserva indicada.",
            )

        if reservation.status not in self.ATTACHABLE_RESERVATION_STATUSES:
            raise ApiError(
                status_code=409,
                code=ErrorCode.RESERVATION_CONFIRMATION_NOT_ALLOWED,
                message="Esta reserva no admite nuevos comprobantes.",
            )

        return reservation

    async def find_existing_by_whatsapp_message(
        self,
        *,
        reservation_id: PydanticObjectId,
        whatsapp_message_id: str,
    ) -> PaymentProofDocument | None:
        storage_key = f"whatsapp/{whatsapp_message_id}"
        return await PaymentProofDocument.find_one(
            {
                "reservation_id": reservation_id,
                "storage_key": storage_key,
            }
        )

    async def find_existing_by_hash(
        self,
        *,
        reservation_id: PydanticObjectId,
        media_id: str,
    ) -> PaymentProofDocument | None:
        proof_hash = sha256(media_id.encode("utf-8")).hexdigest()
        return await PaymentProofDocument.find_one(
            {
                "reservation_id": reservation_id,
                "sha256": proof_hash,
            }
        )

    async def create_metadata_only(
        self,
        *,
        reservation: ReservationDocument,
        storage_key: str,
        filename: str,
        content_type: str,
        media_id: str,
    ) -> PaymentProofDocument:
        if content_type not in ALLOWED_CONTENT_TYPES:
            raise ApiError(
                status_code=400,
                code=ErrorCode.PAYMENT_PROOF_INVALID_CONTENT_TYPE,
                message="El tipo de contenido no esta permitido.",
            )

        proof_hash = sha256(media_id.encode("utf-8")).hexdigest()
        doc = PaymentProofDocument(
            reservation_id=reservation.id,
            storage_key=storage_key,
            filename=filename,
            content_type=content_type,
            size_bytes=1,
            sha256=proof_hash,
            status=PaymentStatus.RECEIVED,
        )
        await doc.insert()
        reservation.payment_proof_ids.append(doc.id)
        reservation.payment_status = PaymentStatus.RECEIVED
        await reservation.save()
        return doc
