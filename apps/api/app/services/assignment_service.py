"""Servicio de asignaciones operativas con validación de dominio completa."""

import asyncio
from datetime import UTC, datetime

from beanie import PydanticObjectId

from typing import Any

from app.common.enums import AssignmentSource, AssignmentStatus, ReservationStatus, UserRole
from app.common.labels import ErrorCode
from app.core.errors import ApiError
from app.documents import (
    AssignmentDocument,
    EquineDocument,
    ParticipantDocument,
    ReservationDocument,
    SaddleDocument,
)
from app.schemas.assignment import (
    AssignmentBoardParticipantSchema,
    AssignmentBoardResponseSchema,
    AssignmentBoardSummarySchema,
    AssignmentCreateSchema,
    AssignmentOnBoardSchema,
    AssignmentUpdateSchema,
)
from app.schemas.equine import EquineListItemSchema
from app.schemas.saddle import SaddleListItemSchema
from app.services.equine_service import EquineService
from app.services.mappers import equine_to_list_item, saddle_to_list_item
from app.services.saddle_service import SaddleService


def _safe_str(oid: object) -> str | None:
    return str(oid) if oid is not None else None


def _age_from_birth_date(birth_date) -> int | None:
    """Calculate approximate age in years from birth date."""
    if birth_date is None:
        return None
    today = datetime.now(UTC).date()
    return today.year - birth_date.year - (
        (today.month, today.day) < (birth_date.month, birth_date.day)
    )


class AssignmentService:
    def __init__(
        self,
        equine_service: EquineService | None = None,
        saddle_service: SaddleService | None = None,
    ) -> None:
        self._equine_service = equine_service
        self._saddle_service = saddle_service

    # ── Core CRUD ──

    async def create(
        self,
        payload: AssignmentCreateSchema,
        actor_id: PydanticObjectId | None = None,
        actor_role: UserRole | None = None,
    ) -> AssignmentDocument:
        reservation, participant, equine = await asyncio.gather(
            ReservationDocument.get(payload.reservation_id),
            ParticipantDocument.get(payload.participant_id),
            EquineDocument.get(payload.equine_id),
        )

        self._validate_reservation(reservation)
        self._validate_participant_belongs(participant, reservation)
        self._validate_participant_data(participant)
        self._validate_equine(equine)
        await self._validate_equine_not_duplicate(reservation.id, equine.id)

        saddle_obj = None
        if payload.saddle_id:
            saddle_obj = await SaddleDocument.get(payload.saddle_id)
            self._validate_saddle(saddle_obj)
            await self._validate_saddle_not_duplicate(reservation.id, saddle_obj.id)

        self._validate_rider_weight(participant, equine)
        await self._validate_no_active_assignment(participant.id, reservation.id)

        age = _age_from_birth_date(participant.birth_date)
        safety_flags, warnings = self._check_safety(participant, equine, age)

        now = datetime.now(UTC)
        doc = AssignmentDocument(
            reservation_id=reservation.id,
            participant_id=participant.id,
            equine_id=equine.id,
            saddle_id=saddle_obj.id if saddle_obj else None,
            status=payload.status,
            source=self._resolve_source(actor_id, actor_role),
            notes=payload.notes,
            safety_flags=safety_flags,
            validation_warnings=warnings,
            assigned_by_user_id=actor_id,
            assigned_at=now,
            is_active=True,
            # Deprecated fields (backward compat)
            priority="standard",
            assigned_manually=actor_id is not None,
        )
        await doc.insert()
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
                doc.reservation_id, equine.id, exclude_assignment_id=doc.id,
            )
            doc.equine_id = equine.id

        if "saddle_id" in updates:
            if updates["saddle_id"] is not None:
                saddle = await SaddleDocument.get(updates["saddle_id"])
                self._validate_saddle(saddle)
                await self._validate_saddle_not_duplicate(
                    doc.reservation_id, saddle.id, exclude_assignment_id=doc.id,
                )
                doc.saddle_id = saddle.id
            else:
                doc.saddle_id = None

        if "status" in updates:
            doc.status = updates["status"]

        if "notes" in updates:
            doc.notes = updates["notes"]

        await doc.save()
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
        return doc

    # ── Board ──

    async def get_board(self, reservation_id: str) -> dict[str, Any]:
        """Construye el tablero de asignación para una reserva."""
        from datetime import date

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

        # Equinos disponibles
        available_equines: list[EquineListItemSchema] = []
        if self._equine_service:
            for eq_doc, reason in await self._equine_service.list_available_for_reservation(reservation_id):
                item = equine_to_list_item(eq_doc)
                item.block_reason = reason
                available_equines.append(item)

        # Sillas disponibles
        available_saddles: list[SaddleListItemSchema] = []
        if self._saddle_service:
            for sa_doc, reason in await self._saddle_service.list_available_for_reservation(reservation_id):
                item = saddle_to_list_item(sa_doc)
                item.block_reason = reason
                available_saddles.append(item)

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
            if age is not None and age < 12:
                blocking_reasons.append("Menor de 12 años — requiere verificación")
            if age is not None and age > 65:
                blocking_reasons.append("Mayor de 65 años — requiere verificación")

            assignment_on_board = None
            if assignment_doc:
                equine = await EquineDocument.get(assignment_doc.equine_id)
                saddle = None
                if assignment_doc.saddle_id:
                    saddle = await SaddleDocument.get(assignment_doc.saddle_id)

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

    async def validate_assignment_candidate(
        self,
        reservation_id: str,
        participant_id: str,
        equine_id: str,
        saddle_id: str | None = None,
    ) -> tuple[list[str], list[str]]:
        """Retorna (safety_flags, warnings) sin crear la asignación.

        Lanza ApiError si hay errores bloqueantes.
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
        if saddle_id:
            saddle = await SaddleDocument.get(saddle_id)
            self._validate_saddle(saddle)
        self._validate_rider_weight(participant, equine)
        age = _age_from_birth_date(participant.birth_date)
        return self._check_safety(participant, equine, age)

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

    def _validate_participant_belongs(self, participant: object | None, reservation: object) -> None:
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
        existing = await AssignmentDocument.find_one({
            "participant_id": participant_id,
            "reservation_id": reservation_id,
            "is_active": True,
            "status": {
                "$nin": [
                    AssignmentStatus.CANCELLED.value,
                    AssignmentStatus.REPLACED.value,
                ],
            },
        })
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
    ) -> tuple[list[str], list[str]]:
        safety_flags: list[str] = []
        warnings: list[str] = []

        if age is not None and age < 12:
            safety_flags.append("child_rider")
            warnings.append("Jinete menor de 12 años — verificar equino adecuado")
        if age is not None and age > 65:
            safety_flags.append("senior_rider")
            warnings.append("Jinete mayor de 65 años — verificar condición física")

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
