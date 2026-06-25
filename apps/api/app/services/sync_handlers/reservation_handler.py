"""Push-operation handler for reservations, participants, payment proofs,
assignments, and service logs.

Dependencies
------------
* ``ReservationService``
* ``ParticipantService``
* ``PaymentProofService``
* ``AssignmentService``
* ``ServiceLogService``
"""

from app.documents import (
    AssignmentDocument,
    ParticipantDocument,
    PaymentProofDocument,
    ReservationDocument,
    ServiceLogDocument,
)
from app.schemas.assignment import AssignmentCreateSchema, AssignmentUpdateSchema
from app.schemas.participant import ParticipantCreateSchema, ParticipantUpdateSchema
from app.schemas.payment_proof import PaymentProofCreateSchema, PaymentProofUpdateSchema
from app.schemas.reservation import ReservationCreateSchema, ReservationUpdateSchema
from app.schemas.service_log import ServiceLogCreateSchema, ServiceLogUpdateSchema
from app.schemas.sync import SyncPushOperationSchema
from app.services.assignment_service import AssignmentService
from app.services.participant_service import ParticipantService
from app.services.payment_proof_service import PaymentProofService
from app.services.reservation_service import ReservationService
from app.services.service_log_service import ServiceLogService
from app.services.sync_handlers._shared import ensure_base_version, require_field, require_remote_id


class ReservationSyncHandler:
    """Handles push operations for reservation-related entities."""

    def __init__(
        self,
        reservation_service: ReservationService,
        participant_service: ParticipantService,
        payment_proof_service: PaymentProofService,
        assignment_service: AssignmentService,
        service_log_service: ServiceLogService,
    ) -> None:
        self.reservation_service = reservation_service
        self.participant_service = participant_service
        self.payment_proof_service = payment_proof_service
        self.assignment_service = assignment_service
        self.service_log_service = service_log_service

    async def handle(
        self,
        *,
        entity: str,
        op_type: str,
        operation: SyncPushOperationSchema,
        current_user,
    ):
        if entity == "reservation":
            return await self._handle_reservation(operation, op_type, current_user)
        if entity == "participant":
            return await self._handle_participant(operation, op_type)
        if entity == "payment_proof":
            return await self._handle_payment_proof(operation, op_type, current_user)
        if entity == "assignment":
            return await self._handle_assignment(operation, op_type, current_user)
        if entity == "service_log":
            return await self._handle_service_log(operation, op_type, current_user)
        return None

    async def _handle_reservation(self, operation, op_type, current_user):
        if op_type == "create":
            schema = ReservationCreateSchema(**operation.payload)
            return await self.reservation_service.create(schema.model_dump(), actor_id=current_user.id)
        if op_type == "update":
            require_remote_id(operation)
            await ensure_base_version(ReservationDocument, operation.entity_remote_id, operation.base_version)
            schema = ReservationUpdateSchema(**operation.payload)
            return await self.reservation_service.update(
                operation.entity_remote_id,
                schema.model_dump(exclude_none=True),
                actor_id=current_user.id,
            )
        return None

    async def _handle_participant(self, operation, op_type):
        if op_type == "create":
            reservation_id = require_field(operation.payload, "reservation_id")
            schema = ParticipantCreateSchema(**operation.payload)
            return await self.participant_service.create(reservation_id, schema)
        if op_type == "update":
            require_remote_id(operation)
            await ensure_base_version(ParticipantDocument, operation.entity_remote_id, operation.base_version)
            schema = ParticipantUpdateSchema(**operation.payload)
            return await self.participant_service.update(operation.entity_remote_id, schema)
        return None

    async def _handle_payment_proof(self, operation, op_type, current_user):
        if op_type == "create":
            reservation_id = require_field(operation.payload, "reservation_id")
            schema = PaymentProofCreateSchema(**operation.payload)
            return await self.payment_proof_service.create(reservation_id, schema, actor_id=current_user.id)
        if op_type == "update":
            require_remote_id(operation)
            await ensure_base_version(PaymentProofDocument, operation.entity_remote_id, operation.base_version)
            schema = PaymentProofUpdateSchema(**operation.payload)
            return await self.payment_proof_service.update(operation.entity_remote_id, schema)
        return None

    async def _handle_assignment(self, operation, op_type, current_user):
        if op_type == "create":
            schema = AssignmentCreateSchema(**operation.payload)
            return await self.assignment_service.create(
                schema, actor_id=current_user.id, actor_role=current_user.role,
            )
        if op_type == "update":
            require_remote_id(operation)
            await ensure_base_version(AssignmentDocument, operation.entity_remote_id, operation.base_version)
            schema = AssignmentUpdateSchema(**operation.payload)
            return await self.assignment_service.update(
                operation.entity_remote_id, schema, actor_id=current_user.id,
            )
        return None

    async def _handle_service_log(self, operation, op_type, current_user):
        if op_type == "create":
            schema = ServiceLogCreateSchema(**operation.payload)
            return await self.service_log_service.create(
                schema,
                actor_id=current_user.id,
            )
        if op_type == "update":
            require_remote_id(operation)
            await ensure_base_version(ServiceLogDocument, operation.entity_remote_id, operation.base_version)
            schema = ServiceLogUpdateSchema(**operation.payload)
            return await self.service_log_service.update(
                operation.entity_remote_id,
                schema,
                actor_role=current_user.role,
            )
        if op_type == "delete":
            require_remote_id(operation)
            return await self.service_log_service.soft_delete(
                operation.entity_remote_id,
                actor_role=current_user.role,
            )
        return None
