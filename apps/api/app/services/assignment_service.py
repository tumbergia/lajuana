"""Servicio de asignaciones operativas con validación de dominio completa."""

import asyncio
from datetime import UTC, datetime
from typing import Any

from beanie import PydanticObjectId
from pymongo import UpdateOne

from app.common.enums import AssignmentSource, AssignmentStatus, ReservationStatus, UserRole
from app.common.labels import ErrorCode
from app.core.errors import ApiError
from app.core.logging import logger
from app.documents import (
    AssignmentDocument,
    EquineDocument,
    ParticipantDocument,
    ReservationAuditLogDocument,
    ReservationDocument,
    SaddleDocument,
    ServiceLogDocument,
    ServiceLogEventType,
)
from app.documents.audit_metadata_models import (
    AssignmentMetadata,
    ReplacementMetadata,
)
from app.schemas.assignment import (
    AssignmentBoardParticipantSchema,
    AssignmentBoardResponseSchema,
    AssignmentBoardSummarySchema,
    AssignmentCreateSchema,
    AssignmentOnBoardSchema,
    AssignmentUpdateSchema,
)
from app.services.config_service import ConfigService
from app.services.equine_service import EquineService
from app.services.saddle_service import SaddleService


def _safe_str(oid: object) -> str | None:
    return str(oid) if oid is not None else None


def _age_from_birth_date(birth_date) -> int | None:
    """Calculate approximate age in years from birth date."""
    if birth_date is None:
        return None
    today = datetime.now(UTC).date()
    return (
        today.year
        - birth_date.year
        - ((today.month, today.day) < (birth_date.month, birth_date.day))
    )


class AssignmentService:
    def __init__(
        self,
        equine_service: EquineService | None = None,
        saddle_service: SaddleService | None = None,
        config_service: ConfigService | None = None,
    ) -> None:
        self._equine_service = equine_service
        self._saddle_service = saddle_service
        self._config_service = config_service

    async def _get_age_limits(self) -> tuple[int, int]:
        """Lee min_age/max_age desde config. Fallback seguro 12/65."""
        if self._config_service is None:
            return 12, 65
        try:
            rules = await self._config_service.get_reservation_rules()
            return rules.min_age, rules.max_age
        except Exception:
            logger.warning("Failed to read age config, using defaults", exc_info=True)
        return 12, 65

    # ── Core CRUD ──

    async def create(
        self,
        payload: AssignmentCreateSchema,
        actor_id: PydanticObjectId | None = None,
        actor_role: UserRole | None = None,
    ) -> AssignmentDocument:
        doc_kwargs, _, _ = await self._validate_and_prepare(
            reservation_id=payload.reservation_id,
            participant_id=payload.participant_id,
            equine_id=payload.equine_id,
            saddle_id=payload.saddle_id,
            notes=payload.notes,
            status=payload.status,
            actor_id=actor_id,
            actor_role=actor_role,
        )
        doc = AssignmentDocument(**doc_kwargs)
        await doc.insert()
        await self._log_audit(
            reservation_id=doc.reservation_id,
            assignment_id=doc.id,
            actor_user_id=actor_id,
            actor_role=actor_role,
            action="assignment.created",
            previous_status=None,
            new_status=doc.status.value,
        )
        await self._notify_assignment_changed(
            reservation_id=str(doc.reservation_id),
            actor_id=actor_id,
            action="creada",
            dedup_suffix=f"create:{doc.id}",
        )
        return doc

    async def get(self, assignment_id: str) -> AssignmentDocument:
        doc = await AssignmentDocument.get(assignment_id)
        if doc is None:
            raise ApiError(
                status_code=404,
                code=ErrorCode.ASSIGNMENT_NOT_FOUND,
                message="Asignación no encontrada.",
            )
        return doc

    async def update(
        self,
        assignment_id: str,
        payload: AssignmentUpdateSchema,
        actor_id: PydanticObjectId | None = None,
    ) -> AssignmentDocument:
        doc = await self.get(assignment_id)

        if doc.status == AssignmentStatus.FINAL:
            if payload.model_dump(exclude_none=True, exclude={"notes"}):
                raise ApiError(
                    status_code=409,
                    code=ErrorCode.ASSIGNMENT_INVALID_PRIORITY,
                    message="No se puede modificar una asignación finalizada. Cree un reemplazo.",
                )
            if payload.notes is not None:
                doc.notes = payload.notes
            await doc.save()
            return doc

        updates = payload.model_dump(exclude_none=True)

        if "equine_id" in updates:
            equine = await EquineDocument.get(updates["equine_id"])
            self._validate_equine(equine)
            await self._validate_equine_not_duplicate(
                doc.reservation_id,
                equine.id,
                exclude_assignment_id=doc.id,
            )
            doc.equine_id = equine.id

        if "saddle_id" in updates:
            if updates["saddle_id"] is not None:
                saddle = await SaddleDocument.get(updates["saddle_id"])
                self._validate_saddle(saddle)
                await self._validate_saddle_not_duplicate(
                    doc.reservation_id,
                    saddle.id,
                    exclude_assignment_id=doc.id,
                )
                doc.saddle_id = saddle.id
            else:
                doc.saddle_id = None

        if "status" in updates:
            doc.status = updates["status"]

        if "notes" in updates:
            doc.notes = updates["notes"]

        await doc.save()
        await self._log_audit(
            reservation_id=doc.reservation_id,
            assignment_id=doc.id,
            actor_user_id=actor_id,
            actor_role=None,
            action="assignment.updated",
            previous_status=None,
            new_status=doc.status.value,
        )
        await self._notify_assignment_changed(
            reservation_id=str(doc.reservation_id),
            actor_id=actor_id,
            action="actualizada",
            dedup_suffix=f"update:{doc.id}:{doc.version}",
        )
        return doc

    async def finalize(
        self,
        assignment_id: str,
        actor_id: PydanticObjectId | None = None,
    ) -> AssignmentDocument:
        doc = await self.get(assignment_id)

        if doc.status != AssignmentStatus.CONFIRMED:
            raise ApiError(
                status_code=409,
                code=ErrorCode.ASSIGNMENT_RESERVATION_NOT_CONFIRMED,
                message="Solo se puede finalizar una asignación confirmada.",
            )

        now = datetime.now(UTC)
        doc.status = AssignmentStatus.FINAL
        doc.finalized_by_user_id = actor_id
        doc.finalized_at = now
        await doc.save()
        await self._log_audit(
            reservation_id=doc.reservation_id,
            assignment_id=doc.id,
            actor_user_id=actor_id,
            actor_role=None,
            action="assignment.finalized",
            previous_status=AssignmentStatus.CONFIRMED.value,
            new_status=AssignmentStatus.FINAL.value,
        )
        return doc

    async def unfinalize(
        self,
        assignment_id: str,
        actor_id: PydanticObjectId | None = None,
    ) -> AssignmentDocument:
        doc = await self.get(assignment_id)

        if doc.status != AssignmentStatus.FINAL:
            raise ApiError(
                status_code=409,
                code=ErrorCode.ASSIGNMENT_INVALID_PRIORITY,
                message="Solo se puede revertir una asignación finalizada.",
            )

        doc.status = AssignmentStatus.CONFIRMED
        doc.finalized_by_user_id = None
        doc.finalized_at = None
        await doc.save()
        await self._log_audit(
            reservation_id=doc.reservation_id,
            assignment_id=doc.id,
            actor_user_id=actor_id,
            actor_role=None,
            action="assignment.unfinalized",
            previous_status=AssignmentStatus.FINAL.value,
            new_status=AssignmentStatus.CONFIRMED.value,
        )
        return doc

    async def finalize_all(
        self,
        reservation_id: str,
        actor_id: PydanticObjectId | None = None,
        notes: str | None = None,
    ) -> dict[str, Any]:
        """Finalize all CONFIRMED assignments for a reservation.

        Optionally creates an observation log entry with [notes].
        Returns the updated board.
        """
        assignments = await AssignmentDocument.find(
            {
                "reservation_id": reservation_id,
                "is_active": True,
                "status": AssignmentStatus.CONFIRMED.value,
            },
        ).to_list()

        now = datetime.now(UTC)
        if assignments:
            collection = AssignmentDocument.get_motor_collection()
            operations = [
                UpdateOne(
                    {"_id": doc.id},
                    {
                        "$set": {
                            "status": AssignmentStatus.FINAL.value,
                            "finalized_by_user_id": actor_id,
                            "finalized_at": now,
                        }
                    },
                )
                for doc in assignments
            ]
            await collection.bulk_write(operations)
            audit_logs = [
                ReservationAuditLogDocument(
                    reservation_id=doc.reservation_id,
                    actor_user_id=actor_id,
                    actor_role=UserRole.ADMIN,
                    action="assignment.finalized",
                    previous_status=AssignmentStatus.CONFIRMED.value,
                    new_status=AssignmentStatus.FINAL.value,
                    source="assignment_service",
                    metadata=AssignmentMetadata(assignment_id=str(doc.id)),
                )
                for doc in assignments
            ]
            if audit_logs:
                try:
                    await ReservationAuditLogDocument.insert_many(audit_logs)
                except Exception:
                    logger.exception("Failed to bulk-insert audit logs for finalize_all")

        if notes:
            try:
                await ServiceLogDocument(
                    reservation_id=reservation_id,
                    event_type=ServiceLogEventType.NOTE,
                    notes=notes,
                ).insert()
            except Exception:
                logger.exception("Failed to insert service log note (finalize_all)")

        return await self.get_board(reservation_id)

    async def unfinalize_all(
        self,
        reservation_id: str,
        actor_id: PydanticObjectId | None = None,
        notes: str | None = None,
    ) -> dict[str, Any]:
        """Revert all FINAL assignments back to CONFIRMED for a reservation.

        Optionally creates an observation log entry with [notes].
        Returns the updated board.
        """
        assignments = await AssignmentDocument.find(
            {
                "reservation_id": reservation_id,
                "is_active": True,
                "status": AssignmentStatus.FINAL.value,
            },
        ).to_list()

        now = datetime.now(UTC)
        if assignments:
            collection = AssignmentDocument.get_motor_collection()
            operations = [
                UpdateOne(
                    {"_id": doc.id},
                    {
                        "$set": {
                            "status": AssignmentStatus.CONFIRMED.value,
                            "finalized_by_user_id": None,
                            "finalized_at": None,
                        }
                    },
                )
                for doc in assignments
            ]
            await collection.bulk_write(operations)
            audit_logs = [
                ReservationAuditLogDocument(
                    reservation_id=doc.reservation_id,
                    actor_user_id=actor_id,
                    actor_role=UserRole.ADMIN,
                    action="assignment.unfinalized",
                    previous_status=AssignmentStatus.FINAL.value,
                    new_status=AssignmentStatus.CONFIRMED.value,
                    source="assignment_service",
                    metadata=AssignmentMetadata(assignment_id=str(doc.id)),
                )
                for doc in assignments
            ]
            if audit_logs:
                try:
                    await ReservationAuditLogDocument.insert_many(audit_logs)
                except Exception:
                    logger.exception("Failed to bulk-insert audit logs for unfinalize_all")

        if notes:
            try:
                await ServiceLogDocument(
                    reservation_id=reservation_id,
                    event_type=ServiceLogEventType.NOTE,
                    notes=notes,
                ).insert()
            except Exception:
                logger.exception("Failed to insert service log note (unfinalize_all)")

        return await self.get_board(reservation_id)

    async def batch_update(
        self,
        reservation_id: str,
        assignments: list[dict[str, Any]],
        removals: list[str] | None = None,
        notes: str | None = None,
        actor_id: PydanticObjectId | None = None,
    ) -> dict[str, Any]:
        """Process a batch of assignment changes (local-first flow).

        - Process removals (cancel assignments), tracking which were skipped.
        - Process assignments (create or update each, set to FINAL).
        - Create observation log if notes provided.
        - Return updated board with skipped_removals metadata.
        """
        reservation = await ReservationDocument.get(reservation_id)
        if reservation is None:
            raise ApiError(
                status_code=404,
                code=ErrorCode.RESERVATION_NOT_FOUND,
                message="Reserva no encontrada.",
            )

        now = datetime.now(UTC)
        skipped_removals: list[str] = []

        # ── Process removals ──
        if removals:
            for aid in removals:
                doc = await AssignmentDocument.get(aid)
                if doc is None:
                    continue
                if doc.status in (AssignmentStatus.FINAL, AssignmentStatus.CANCELLED):
                    skipped_removals.append(aid)
                    continue
                prev = doc.status.value
                doc.status = AssignmentStatus.CANCELLED
                doc.is_active = False
                await doc.save()
                await self._log_audit(
                    reservation_id=doc.reservation_id,
                    assignment_id=doc.id,
                    actor_user_id=actor_id,
                    actor_role=None,
                    action="assignment.removed",
                    previous_status=prev,
                    new_status=AssignmentStatus.CANCELLED.value,
                )

        # ── Process assignments ──
        for item in assignments:
            pid = item.get("participant_id")
            eid = item.get("equine_id")
            sid = item.get("saddle_id")
            if not pid or not eid:
                continue

            participant = await ParticipantDocument.get(pid)
            equine = await EquineDocument.get(eid)
            if participant is None or equine is None:
                continue

            # Check if participant already has an active assignment
            existing = await AssignmentDocument.find_one(
                {
                    "reservation_id": reservation.id,
                    "participant_id": participant.id,
                    "is_active": True,
                    "status": {
                        "$nin": [AssignmentStatus.CANCELLED.value, AssignmentStatus.REPLACED.value]
                    },
                }
            )

            if existing:
                # Update existing → validate saddle, then patch equine/saddle + set FINAL
                if sid:
                    saddle_obj = await SaddleDocument.get(sid)
                    self._validate_saddle(saddle_obj)
                    await self._validate_saddle_not_duplicate(
                        reservation.id,
                        saddle_obj.id,
                        exclude_assignment_id=existing.id,
                    )

                existing.equine_id = equine.id
                existing.saddle_id = sid
                existing.status = AssignmentStatus.FINAL
                existing.finalized_by_user_id = actor_id
                existing.finalized_at = now
                await existing.save()
                await self._log_audit(
                    reservation_id=existing.reservation_id,
                    assignment_id=existing.id,
                    actor_user_id=actor_id,
                    actor_role=None,
                    action="assignment.updated_and_finalized",
                    previous_status=existing.status.value,
                    new_status=AssignmentStatus.FINAL.value,
                )
            else:
                # Create new → use shared validation pipeline
                doc_kwargs, _, _ = await self._validate_and_prepare(
                    reservation_id=reservation_id,
                    participant_id=pid,
                    equine_id=eid,
                    saddle_id=sid,
                    notes=None,
                    status=AssignmentStatus.FINAL,
                    actor_id=actor_id,
                    actor_role=None,
                )
                doc_kwargs["finalized_by_user_id"] = actor_id
                doc_kwargs["finalized_at"] = now
                doc = AssignmentDocument(**doc_kwargs)
                await doc.insert()
                await self._log_audit(
                    reservation_id=doc.reservation_id,
                    assignment_id=doc.id,
                    actor_user_id=actor_id,
                    actor_role=None,
                    action="assignment.created_and_finalized",
                    previous_status=None,
                    new_status=AssignmentStatus.FINAL.value,
                )

        # ── Observation log ──
        if notes:
            try:
                await ServiceLogDocument(
                    reservation_id=reservation_id,
                    event_type=ServiceLogEventType.NOTE,
                    notes=notes,
                ).insert()
            except Exception:
                logger.exception("Failed to insert service log note (batch_update)")

        result = await self.get_board(reservation_id)
        result["skipped_removals"] = skipped_removals
        return result

    async def remove(
        self,
        assignment_id: str,
        actor_id: PydanticObjectId | None = None,
    ) -> AssignmentDocument:
        doc = await self.get(assignment_id)

        if doc.status in (AssignmentStatus.FINAL, AssignmentStatus.CANCELLED):
            raise ApiError(
                status_code=409,
                code=ErrorCode.ASSIGNMENT_INVALID_PRIORITY,
                message="La asignación no puede quitarse en su estado actual.",
            )

        previous_status = doc.status.value
        doc.status = AssignmentStatus.CANCELLED
        doc.is_active = False
        await doc.save()
        await self._log_audit(
            reservation_id=doc.reservation_id,
            assignment_id=doc.id,
            actor_user_id=actor_id,
            actor_role=None,
            action="assignment.removed",
            previous_status=previous_status,
            new_status=AssignmentStatus.CANCELLED.value,
        )
        return doc

    async def replace(
        self,
        assignment_id: str,
        payload: Any,
        actor_id: PydanticObjectId | None = None,
        actor_role: UserRole | None = None,
    ) -> AssignmentDocument:
        """Reemplaza una asignación finalizada: desactiva la actual y crea una nueva."""
        from app.schemas.assignment import AssignmentCreateSchema

        old = await self.get(assignment_id)

        if old.status != AssignmentStatus.FINAL:
            raise ApiError(
                status_code=409,
                code=ErrorCode.ASSIGNMENT_INVALID_PRIORITY,
                message="Solo se puede reemplazar una asignación finalizada.",
            )

        # Crear la nueva asignación con los mismos participant/reservation
        create_payload = AssignmentCreateSchema(
            reservation_id=str(old.reservation_id),
            participant_id=str(old.participant_id),
            equine_id=payload.equine_id,
            saddle_id=payload.saddle_id,
            notes=payload.notes or old.notes,
        )
        new_doc = await self.create(
            create_payload,
            actor_id=actor_id,
            actor_role=actor_role,
        )

        # Desactivar la asignación anterior
        now = datetime.now(UTC)
        old.status = AssignmentStatus.REPLACED
        old.is_active = False
        old.replaced_by_assignment_id = new_doc.id
        await old.save()

        await self._log_audit(
            reservation_id=old.reservation_id,
            assignment_id=old.id,
            actor_user_id=actor_id,
            actor_role=actor_role,
            action="assignment.replaced",
            previous_status=AssignmentStatus.FINAL.value,
            new_status=AssignmentStatus.REPLACED.value,
            metadata=ReplacementMetadata(replaced_by=str(new_doc.id)),
        )

        return new_doc

    # ── Board ──

    async def get_board(self, reservation_id: str) -> dict[str, Any]:
        """Construye el tablero de asignación para una reserva."""
        from datetime import date

        min_age, max_age = await self._get_age_limits()
        reservation = await ReservationDocument.get(reservation_id)
        if reservation is None:
            raise ApiError(
                status_code=404,
                code=ErrorCode.RESERVATION_NOT_FOUND,
                message="Reserva no encontrada.",
            )

        # Cargar participantes
        participant_docs: list[ParticipantDocument] = []
        if reservation.participant_ids:
            participant_docs = await ParticipantDocument.find(
                {"_id": {"$in": reservation.participant_ids}},
            ).to_list()

        # Cargar asignaciones activas de esta reserva
        assignments = await AssignmentDocument.find(
            {"reservation_id": reservation.id, "is_active": True},
        ).to_list()
        assignment_map: dict[str, AssignmentDocument] = {}
        for a in assignments:
            assignment_map[str(a.participant_id)] = a

        # Batch fetch equinos y sillas de las asignaciones activas
        assigned_equine_ids = [a.equine_id for a in assignments if a.equine_id]
        assigned_saddle_ids = [a.saddle_id for a in assignments if a.saddle_id]

        assigned_equines_list = (
            await EquineDocument.find({"_id": {"$in": assigned_equine_ids}}).to_list()
            if assigned_equine_ids
            else []
        )
        assigned_saddles_list = (
            await SaddleDocument.find({"_id": {"$in": assigned_saddle_ids}}).to_list()
            if assigned_saddle_ids
            else []
        )
        equine_map: dict[str, object] = {str(e.id): e for e in assigned_equines_list}
        saddle_map: dict[str, object] = {str(s.id): s for s in assigned_saddles_list}

        # Equinos disponibles — version minimalista para el board
        available_equines: list = []
        if self._equine_service:
            for eq_doc, reason in await self._equine_service.list_available_for_reservation(
                reservation_id,
                limit=200,
                skip=0,
            ):
                available_equines.append(
                    {
                        "id": _safe_str(eq_doc.id) or "",
                        "name": getattr(eq_doc, "name", ""),
                        "max_rider_weight_kg": getattr(eq_doc, "max_rider_weight_kg", None),
                        "image_base64": getattr(eq_doc, "image_base64", None),
                        "block_reason": reason,
                    }
                )

        # Sillas disponibles — version minimalista para el board
        available_saddles: list = []
        if self._saddle_service:
            for sa_doc, reason in await self._saddle_service.list_available_for_reservation(
                reservation_id,
                limit=200,
                skip=0,
            ):
                available_saddles.append(
                    {
                        "id": _safe_str(sa_doc.id) or "",
                        "code": getattr(sa_doc, "code", ""),
                        "name": getattr(sa_doc, "name", None),
                        "block_reason": reason,
                    }
                )

        # Armar participantes del board
        board_participants = []
        assigned_count = 0
        pending_count = 0
        blocking_count = 0

        for p in participant_docs:
            pid = str(p.id)
            age = _age_from_birth_date(p.birth_date)
            assignment_doc = assignment_map.get(pid)

            blocking_reasons: list[str] = []
            if not p.is_completed:
                blocking_reasons.append("Participante no ha completado formulario")
            if not p.weight_kg:
                blocking_reasons.append("Falta peso del participante")
            if not p.experience_level:
                blocking_reasons.append("Falta nivel de experiencia")
            if age is not None and age < min_age:
                blocking_reasons.append(f"Menor de {min_age} años — requiere verificación")
            if age is not None and age > max_age:
                blocking_reasons.append(f"Mayor de {max_age} años — requiere verificación")

            assignment_on_board = None
            if assignment_doc:
                equine = (
                    equine_map.get(str(assignment_doc.equine_id))
                    if assignment_doc.equine_id
                    else None
                )
                saddle = (
                    saddle_map.get(str(assignment_doc.saddle_id))
                    if assignment_doc.saddle_id
                    else None
                )

                assignment_on_board = AssignmentOnBoardSchema(
                    assignment_id=_safe_str(assignment_doc.id),
                    equine_id=_safe_str(assignment_doc.equine_id),
                    equine_name=equine.name if equine else None,
                    saddle_id=_safe_str(assignment_doc.saddle_id),
                    saddle_label=(
                        f"{saddle.code} - {saddle.name}"
                        if saddle and saddle.code
                        else (saddle.name if saddle else None)
                    ),
                    status=assignment_doc.status,
                    warnings=assignment_doc.validation_warnings,
                )
                assigned_count += 1
            else:
                if blocking_reasons:
                    blocking_count += 1
                else:
                    pending_count += 1

            board_participants.append(
                AssignmentBoardParticipantSchema(
                    participant_id=pid,
                    full_name=f"{p.first_name} {p.last_name}",
                    age_years=age,
                    weight_kg=p.weight_kg,
                    height_cm=p.height_cm,
                    experience_level=p.experience_level.value if p.experience_level else None,
                    assignment=assignment_on_board,
                    blocking_reasons=blocking_reasons,
                ),
            )

        scheduled_date_str: str | None = None
        if reservation.requested_date:
            if isinstance(reservation.requested_date, date):
                scheduled_date_str = reservation.requested_date.isoformat()
            else:
                scheduled_date_str = str(reservation.requested_date)

        return AssignmentBoardResponseSchema(
            reservation_id=_safe_str(reservation.id),
            reservation_status=reservation.status.value,
            scheduled_date=scheduled_date_str,
            participants=board_participants,
            available_equines=available_equines,
            available_saddles=available_saddles,
            summary=AssignmentBoardSummarySchema(
                participants_total=len(participant_docs),
                assigned_total=assigned_count,
                pending_total=pending_count,
                blocking_total=blocking_count,
            ),
        ).model_dump(mode="json")

    # ── Validation helper (without creating) ──

    async def _validate_and_prepare(
        self,
        reservation_id: str,
        participant_id: str,
        equine_id: str,
        saddle_id: str | None = None,
        notes: str | None = None,
        status: AssignmentStatus = AssignmentStatus.CONFIRMED,
        actor_id: PydanticObjectId | None = None,
        actor_role: UserRole | None = None,
        *,
        exclude_assignment_id: object | None = None,
        dry_run: bool = False,
    ) -> tuple[dict[str, Any], object, object] | tuple[list[str], list[str], None, None]:
        """Validate ALL constraints. Single validation pipeline for create/update/replace.

        When dry_run=True, returns (safety_flags, warnings, None, None) without building
        document kwargs. Used by validate_assignment_candidate().

        When dry_run=False (default), returns (doc_kwargs, reservation, participant).
        Raises ApiError on any violation.
        """
        reservation, participant, equine = await asyncio.gather(
            ReservationDocument.get(reservation_id),
            ParticipantDocument.get(participant_id),
            EquineDocument.get(equine_id),
        )

        self._validate_reservation(reservation)
        self._validate_participant_belongs(participant, reservation)
        self._validate_participant_data(participant)
        self._validate_equine(equine)
        await self._validate_equine_not_duplicate(
            reservation.id,
            equine.id,
            exclude_assignment_id=exclude_assignment_id,
        )

        saddle_obj = None
        if saddle_id:
            saddle_obj = await SaddleDocument.get(saddle_id)
            self._validate_saddle(saddle_obj)
            await self._validate_saddle_not_duplicate(
                reservation.id,
                saddle_obj.id,
                exclude_assignment_id=exclude_assignment_id,
            )

        self._validate_rider_weight(participant, equine)
        await self._validate_no_active_assignment(participant.id, reservation.id)

        age = _age_from_birth_date(participant.birth_date)
        min_age, max_age = await self._get_age_limits()
        safety_flags, warnings = self._check_safety(participant, equine, age, min_age, max_age)

        if dry_run:
            return safety_flags, warnings, None, None

        now = datetime.now(UTC)
        doc_kwargs: dict[str, Any] = dict(
            reservation_id=reservation.id,
            participant_id=participant.id,
            equine_id=equine.id,
            saddle_id=saddle_obj.id if saddle_obj else None,
            status=status,
            source=self._resolve_source(actor_id, actor_role),
            notes=notes,
            safety_flags=safety_flags,
            validation_warnings=warnings,
            assigned_by_user_id=actor_id,
            assigned_at=now,
            is_active=True,
        )
        return doc_kwargs, reservation, participant

    async def validate_assignment_candidate(
        self,
        reservation_id: str,
        participant_id: str,
        equine_id: str,
        saddle_id: str | None = None,
    ) -> tuple[list[str], list[str]]:
        """Retorna (safety_flags, warnings) sin crear la asignación.

        Delega a _validate_and_prepare con dry_run=True.
        Lanza ApiError si hay errores bloqueantes.
        """
        flags, warnings, _, _ = await self._validate_and_prepare(
            reservation_id=reservation_id,
            participant_id=participant_id,
            equine_id=equine_id,
            saddle_id=saddle_id,
            dry_run=True,
        )
        return flags, warnings

    # ── Internal validations ──

    def _validate_reservation(self, reservation: object | None) -> None:
        if reservation is None:
            raise ApiError(
                status_code=404,
                code=ErrorCode.RESERVATION_NOT_FOUND,
                message="Reserva no encontrada.",
            )
        if reservation.status != ReservationStatus.CONFIRMED:
            raise ApiError(
                status_code=409,
                code=ErrorCode.ASSIGNMENT_RESERVATION_NOT_CONFIRMED,
                message="La reserva debe estar confirmada para asignar.",
                details={
                    "reservation_id": _safe_str(getattr(reservation, "id", None)),
                    "status": getattr(reservation, "status", None),
                },
            )

    def _validate_participant_belongs(
        self, participant: object | None, reservation: object
    ) -> None:
        if participant is None:
            raise ApiError(
                status_code=404,
                code=ErrorCode.PARTICIPANT_NOT_FOUND,
                message="Participante no encontrado.",
            )
        if str(participant.reservation_id) != str(reservation.id):
            raise ApiError(
                status_code=400,
                code=ErrorCode.ASSIGNMENT_PARTICIPANT_NOT_IN_RESERVATION,
                message="El participante no pertenece a la reserva.",
            )

    def _validate_participant_data(self, participant: object) -> None:
        missing: list[str] = []
        if getattr(participant, "weight_kg", None) is None:
            missing.append("weight_kg")
        if getattr(participant, "birth_date", None) is None:
            missing.append("birth_date")
        if getattr(participant, "experience_level", None) is None:
            missing.append("experience_level")
        if missing:
            raise ApiError(
                status_code=409,
                code=ErrorCode.ASSIGNMENT_PARTICIPANT_MISSING_REQUIRED_DATA,
                message="El participante no tiene los datos mínimos requeridos.",
                details={
                    "participant_id": _safe_str(getattr(participant, "id", None)),
                    "missing_fields": missing,
                },
            )

    def _validate_equine(self, equine: object | None) -> None:
        if equine is None:
            raise ApiError(
                status_code=404,
                code=ErrorCode.EQUINE_NOT_FOUND,
                message="Equino no encontrado.",
            )
        if not equine.is_active or not equine.is_available:
            raise ApiError(
                status_code=409,
                code=ErrorCode.ASSIGNMENT_EQUINE_NOT_AVAILABLE,
                message="Equino no disponible para asignación.",
                details={"equine_id": _safe_str(getattr(equine, "id", None))},
            )

    async def _validate_equine_not_duplicate(
        self,
        reservation_id: object,
        equine_id: object,
        exclude_assignment_id: object | None = None,
    ) -> None:
        query: dict = {
            "reservation_id": reservation_id,
            "equine_id": equine_id,
            "is_active": True,
        }
        if exclude_assignment_id:
            query["_id"] = {"$ne": exclude_assignment_id}
        dup = await AssignmentDocument.find_one(query)
        if dup is not None:
            raise ApiError(
                status_code=409,
                code=ErrorCode.ASSIGNMENT_EQUINE_ALREADY_ASSIGNED,
                message="El equino ya está asignado para esta salida.",
                details={
                    "equine_id": _safe_str(equine_id),
                    "reservation_id": _safe_str(reservation_id),
                },
            )

    def _validate_saddle(self, saddle: object | None) -> None:
        if saddle is None:
            raise ApiError(
                status_code=404,
                code=ErrorCode.SADDLE_NOT_FOUND,
                message="Silla no encontrada.",
            )
        if getattr(saddle, "deleted_at", None) is not None:
            raise ApiError(
                status_code=409,
                code=ErrorCode.ASSIGNMENT_SADDLE_NOT_AVAILABLE,
                message="Silla eliminada — no disponible para asignación.",
                details={"saddle_id": _safe_str(getattr(saddle, "id", None))},
            )
        if not saddle.is_available:
            raise ApiError(
                status_code=409,
                code=ErrorCode.ASSIGNMENT_SADDLE_NOT_AVAILABLE,
                message="Silla no disponible para asignación.",
                details={"saddle_id": _safe_str(getattr(saddle, "id", None))},
            )

    async def _validate_saddle_not_duplicate(
        self,
        reservation_id: object,
        saddle_id: object,
        exclude_assignment_id: object | None = None,
    ) -> None:
        query: dict = {
            "reservation_id": reservation_id,
            "saddle_id": saddle_id,
            "is_active": True,
        }
        if exclude_assignment_id:
            query["_id"] = {"$ne": exclude_assignment_id}
        dup = await AssignmentDocument.find_one(query)
        if dup is not None:
            raise ApiError(
                status_code=409,
                code=ErrorCode.ASSIGNMENT_SADDLE_ALREADY_ASSIGNED,
                message="La silla ya está asignada para esta salida.",
                details={
                    "saddle_id": _safe_str(saddle_id),
                    "reservation_id": _safe_str(reservation_id),
                },
            )

    def _validate_rider_weight(self, participant: object, equine: object) -> None:
        rider_weight = getattr(participant, "weight_kg", None)
        max_weight = getattr(equine, "max_rider_weight_kg", None)
        if rider_weight and max_weight:
            if rider_weight > max_weight:
                raise ApiError(
                    status_code=409,
                    code=ErrorCode.ASSIGNMENT_RIDER_WEIGHT_EXCEEDS_LIMIT,
                    message="El peso del jinete excede el límite del equino.",
                    details={
                        "participant_id": _safe_str(getattr(participant, "id", None)),
                        "equine_id": _safe_str(getattr(equine, "id", None)),
                        "weight_kg": str(rider_weight),
                        "max_rider_weight_kg": str(max_weight),
                    },
                )

    async def _validate_no_active_assignment(
        self,
        participant_id: object,
        reservation_id: object,
    ) -> None:
        existing = await AssignmentDocument.find_one(
            {
                "participant_id": participant_id,
                "reservation_id": reservation_id,
                "is_active": True,
                "status": {
                    "$nin": [
                        AssignmentStatus.CANCELLED.value,
                        AssignmentStatus.REPLACED.value,
                    ],
                },
            }
        )
        if existing is not None:
            raise ApiError(
                status_code=409,
                code=ErrorCode.ASSIGNMENT_DUPLICATE_FOR_PARTICIPANT,
                message="El participante ya tiene una asignación activa en esta reserva.",
                details={
                    "participant_id": _safe_str(participant_id),
                    "reservation_id": _safe_str(reservation_id),
                    "existing_assignment_id": _safe_str(existing.id),
                },
            )

    def _check_safety(
        self,
        participant: object,
        equine: object,
        age: int | None,
        min_age: int = 12,
        max_age: int = 65,
    ) -> tuple[list[str], list[str]]:
        safety_flags: list[str] = []
        warnings: list[str] = []

        if age is not None and age < min_age:
            safety_flags.append("child_rider")
            warnings.append(f"Jinete menor de {min_age} años — verificar equino adecuado")
        if age is not None and age > max_age:
            safety_flags.append("senior_rider")
            warnings.append(f"Jinete mayor de {max_age} años — verificar condición física")

        max_weight = getattr(equine, "max_rider_weight_kg", None)
        rider_weight = getattr(participant, "weight_kg", None)
        if rider_weight and not max_weight:
            warnings.append(
                f"El equino no tiene límite de peso definido (jinete: {rider_weight} kg)",
            )

        return safety_flags, warnings

    def _resolve_source(
        self,
        actor_id: object | None,
        actor_role: UserRole | None = None,
    ) -> AssignmentSource:
        if actor_id is None:
            return AssignmentSource.SYSTEM_SUGGESTED
        if actor_role == UserRole.GUIDE:
            return AssignmentSource.MANUAL_GUIDE
        return AssignmentSource.MANUAL_ADMIN

    async def _notify_assignment_changed(
        self,
        *,
        reservation_id: str,
        actor_id: PydanticObjectId | None,
        action: str,
        dedup_suffix: str,
    ) -> None:
        try:
            from app.common.enums import NotificationEventType
            from app.core.di import Container

            reservation = await ReservationDocument.get(reservation_id)
            holder = (
                reservation.holder_name
                if reservation is not None and reservation.holder_name
                else "Cliente"
            )
            code = reservation.code if reservation is not None else reservation_id
            await Container.get_instance().notification_service.enqueue_admin_in_app(
                event_type=NotificationEventType.ASSIGNMENT_CHANGED,
                title="Asignaciones actualizadas",
                body=f"Asignación {action} — {holder} · reserva {code}",
                reservation_id=reservation_id,
                actor_user_id=str(actor_id) if actor_id else None,
                dedup_suffix=dedup_suffix,
                contact_phone=reservation.holder_phone if reservation is not None else None,
            )
        except Exception:
            logger.exception(
                "[assignment] Failed to enqueue assignment_changed | reservation=%s",
                reservation_id,
            )

    async def _log_audit(
        self,
        reservation_id: object,
        assignment_id: object,
        actor_user_id: object | None,
        actor_role: UserRole | None,
        action: str,
        previous_status: str | None,
        new_status: str,
        metadata: dict | None = None,
    ) -> None:
        """Registra auditoría para operaciones de asignación."""
        try:
            await ReservationAuditLogDocument(
                reservation_id=reservation_id,
                actor_user_id=actor_user_id,
                actor_role=actor_role or UserRole.ADMIN,
                action=action,
                previous_status=previous_status or "",
                new_status=new_status,
                source="assignment_service",
                metadata=metadata or AssignmentMetadata(assignment_id=str(assignment_id)),
            ).insert()
        except Exception:
            logger.exception("Audit log insert failed — non-blocking")
