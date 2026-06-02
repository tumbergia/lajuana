import asyncio
from datetime import datetime
from hashlib import sha256

from beanie import PydanticObjectId

from app.common.enums import PaymentStatus, ReservationStatus, UserRole
from app.common.labels import ErrorCode
from app.core.errors import ApiError
from app.core.logging import logger
from app.documents import (
    ExperienceDocument,
    FileUploadDocument,
    PaymentProofDocument,
    ReservationAuditLogDocument,
    ReservationDocument,
)
from app.schemas.payment_proof import (
    PaymentProofApproveSchema,
    PaymentProofCreateSchema,
    PaymentProofRejectSchema,
    PaymentProofUnrejectSchema,
    PaymentProofUnverifySchema,
    PaymentProofUpdateSchema,
    PaymentProofVerifySchema,
)
from app.services.storage import get_storage_adapter

ALLOWED_CONTENT_TYPES = {
    "image/jpeg",
    "image/png",
    "application/pdf",
}

ALLOWED_PAYMENT_PROOF_TRANSITIONS = {
    PaymentStatus.RECEIVED: {PaymentStatus.VERIFIED, PaymentStatus.REJECTED},
    PaymentStatus.VERIFIED: {PaymentStatus.RECEIVED},
    PaymentStatus.REJECTED: {PaymentStatus.RECEIVED},
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
            {"storage_key": payload.storage_key}
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

    async def approve_payment(
        self,
        payment_proof_id: str,
        payload: PaymentProofApproveSchema,
        *,
        actor_id: PydanticObjectId | None,
        actor_role: UserRole,
    ) -> PaymentProofDocument:
        if actor_role != UserRole.ADMIN:
            raise ApiError(
                status_code=403,
                code=ErrorCode.AUTH_FORBIDDEN,
                message="No tienes permisos para aprobar comprobantes.",
            )
        if payload.confirmation_token != "APPROVE_PAYMENT":
            raise ApiError(
                status_code=400,
                code=ErrorCode.VALIDATION_ERROR,
                message="Token de confirmación inválido para aprobar pago.",
            )

        doc = await self.get(payment_proof_id)
        previous_status = str(doc.status.value)
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

        reservation.status = ReservationStatus.PAYMENT_RECEIVED
        reservation.updated_by = actor_id
        await reservation.save()

        # Audit log — best-effort (non-critical, won't roll back on failure)
        await self._create_audit_log(
            reservation_id=reservation.id,
            payment_proof_id=doc.id,
            actor_user_id=actor_id,
            actor_role=actor_role,
            action="payment_proof.approved",
            previous_status=previous_status,
            new_status=str(doc.status.value),
            reason=payload.note,
        )

        # Enqueue WhatsApp with participant form link (via outbox)
        try:
            from app.core.di import Container
            experience = await ExperienceDocument.get(reservation.experience_id)
            notif = Container.get_instance().notification_service
            await notif.enqueue_payment_approved_form(
                reservation=reservation,
                experience_name=experience.name if experience else "",
            )
        except Exception:
            logger.exception(
                "[reservation=%s] Failed to enqueue payment approved WhatsApp",
                reservation.id,
            )

        return doc

    @staticmethod
    def _format_date_es(d: datetime.date) -> str:
        days = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
        months = [
            "enero", "febrero", "marzo", "abril", "mayo", "junio",
            "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
        ]
        return f"{days[d.weekday()]} {d.day} de {months[d.month - 1]} de {d.year}"

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
        previous_status = str(doc.status.value)
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

        # Audit log — best-effort, won't roll back on failure
        await self._create_audit_log(
            reservation_id=reservation.id,
            payment_proof_id=doc.id,
            actor_user_id=actor_id,
            actor_role=actor_role,
            action="payment_proof.rejected",
            previous_status=previous_status,
            new_status=str(doc.status.value),
            reason=payload.reason,
        )

        # Enqueue WhatsApp with rejection reason (via outbox)
        try:
            from app.core.di import Container
            experience = await ExperienceDocument.get(reservation.experience_id)
            notif = Container.get_instance().notification_service
            await notif.enqueue_payment_rejected(
                reservation=reservation,
                experience_name=experience.name if experience else "",
                rejection_reason=payload.reason,
            )
        except Exception:
            logger.exception(
                "[reservation=%s] Failed to enqueue payment rejected WhatsApp",
                reservation.id,
            )

        return doc

    async def unverify_payment(
        self,
        payment_proof_id: str,
        payload: PaymentProofUnverifySchema,
        *,
        actor_id: PydanticObjectId | None,
        actor_role: UserRole,
    ) -> PaymentProofDocument:
        if actor_role != UserRole.ADMIN:
            raise ApiError(
                status_code=403,
                code=ErrorCode.AUTH_FORBIDDEN,
                message="No tienes permisos para deshacer verificacion de comprobantes.",
            )
        if payload.confirmation_token != "UNVERIFY_PAYMENT":
            raise ApiError(
                status_code=400,
                code=ErrorCode.VALIDATION_ERROR,
                message="Token de confirmacion invalido para deshacer verificacion.",
            )

        doc = await self.get(payment_proof_id)
        previous_status = str(doc.status.value)
        self._ensure_transition_allowed(doc.status, PaymentStatus.RECEIVED)
        reservation = await ReservationDocument.get(doc.reservation_id)
        if reservation is None:
            raise ApiError(
                status_code=404,
                code=ErrorCode.RESERVATION_NOT_FOUND,
                message="Reserva no encontrada.",
            )

        # Revert proof + reservation payment_status to RECEIVED
        await self._sync_proof_and_reservation_payment_status(
            doc=doc,
            reservation=reservation,
            target_status=PaymentStatus.RECEIVED,
            actor_id=actor_id,
        )

        # Revert reservation status to PENDING_PAYMENT (undo approve transition)
        reservation.status = ReservationStatus.PENDING_PAYMENT
        reservation.updated_by = actor_id
        await reservation.save()

        # Audit log — best-effort
        await self._create_audit_log(
            reservation_id=reservation.id,
            payment_proof_id=doc.id,
            actor_user_id=actor_id,
            actor_role=actor_role,
            action="payment_proof.unverified",
            previous_status=previous_status,
            new_status=str(doc.status.value),
            reason=payload.note,
        )

        return doc

    async def unreject_payment(
        self,
        payment_proof_id: str,
        payload: PaymentProofUnrejectSchema,
        *,
        actor_id: PydanticObjectId | None,
        actor_role: UserRole,
    ) -> PaymentProofDocument:
        if actor_role != UserRole.ADMIN:
            raise ApiError(
                status_code=403,
                code=ErrorCode.AUTH_FORBIDDEN,
                message="No tienes permisos para deshacer rechazo de comprobantes.",
            )
        if payload.confirmation_token != "UNREJECT_PAYMENT":
            raise ApiError(
                status_code=400,
                code=ErrorCode.VALIDATION_ERROR,
                message="Token de confirmacion invalido para deshacer rechazo.",
            )

        doc = await self.get(payment_proof_id)
        previous_status = str(doc.status.value)
        self._ensure_transition_allowed(doc.status, PaymentStatus.RECEIVED)
        reservation = await ReservationDocument.get(doc.reservation_id)
        if reservation is None:
            raise ApiError(
                status_code=404,
                code=ErrorCode.RESERVATION_NOT_FOUND,
                message="Reserva no encontrada.",
            )

        # Revert proof + reservation payment_status to RECEIVED
        await self._sync_proof_and_reservation_payment_status(
            doc=doc,
            reservation=reservation,
            target_status=PaymentStatus.RECEIVED,
            actor_id=actor_id,
        )

        # Reject does NOT change reservation.status, so no revert needed here

        # Audit log — best-effort
        await self._create_audit_log(
            reservation_id=reservation.id,
            payment_proof_id=doc.id,
            actor_user_id=actor_id,
            actor_role=actor_role,
            action="payment_proof.unrejected",
            previous_status=previous_status,
            new_status=str(doc.status.value),
            reason=payload.note,
        )

        return doc

    async def _create_audit_log(
        self,
        *,
        reservation_id: PydanticObjectId,
        payment_proof_id: PydanticObjectId | None,
        actor_user_id: PydanticObjectId | None,
        actor_role: UserRole,
        action: str,
        previous_status: str,
        new_status: str,
        reason: str | None = None,
    ) -> None:
        try:
            log = ReservationAuditLogDocument(
                reservation_id=reservation_id,
                payment_proof_id=payment_proof_id,
                actor_user_id=actor_user_id,
                actor_role=actor_role,
                action=action,
                previous_status=previous_status,
                new_status=new_status,
                reason=reason,
                source="mobile_app",
            )
            await log.insert()
        except Exception as exc:
            logger.warning(
                "[audit] Failed to create audit log: %s | action=%s reservation=%s",
                exc,
                action,
                reservation_id,
            )

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
                logger.exception(
                    "[payment_proof=%s] Failed to rollback payment proof save",
                    doc.id,
                )
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

        proof_id = str(doc.id)
        task = asyncio.create_task(self._background_download(proof_id))
        task.add_done_callback(lambda t: self._on_background_download_done(t, proof_id))

        return doc

    async def _background_download(self, proof_id: str) -> None:
        from app.services.whatsapp_media_downloader import download_and_store

        await download_and_store(proof_id)

    def _on_background_download_done(
        self, task: asyncio.Task[None], proof_id: str
    ) -> None:
        try:
            exc = task.exception()
            if exc:
                logger.error(
                    "[payment_proof] Background download failed | proof_id=%s | error=%s",
                    proof_id,
                    exc,
                    exc_info=exc,
                )
        except asyncio.CancelledError:
            logger.warning(
                "[payment_proof] Background download cancelled | proof_id=%s",
                proof_id,
            )

    async def get_download(
        self,
        payment_proof_id: str,
    ) -> tuple[str, bytes | None]:
        doc = await self.get(payment_proof_id)

        # 1. Serve from document field (MongoDB storage) — preferred path
        if doc.file_data is not None:
            return doc.content_type, doc.file_data

        # 2. WhatsApp proof still pending download from Meta API
        if doc.storage_key.startswith("whatsapp/") and doc.size_bytes == 1:
            return "pending", None

        # 3. Fallback: read from file storage adapter (legacy proofs)
        adapter = get_storage_adapter()
        file_bytes = await adapter.read_bytes(doc.storage_key)
        if file_bytes is None:
            raise ApiError(
                status_code=404,
                code=ErrorCode.PAYMENT_PROOF_FILE_NOT_FOUND,
                message="Archivo no encontrado en el almacenamiento.",
                details={"storage_key": doc.storage_key},
            )

        return doc.content_type, file_bytes
