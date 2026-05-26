from datetime import UTC, datetime

from beanie import PydanticObjectId

from app.common.enums import ROLE_PERMISSIONS, Permission
from app.common.labels import ErrorCode
from app.core.errors import ApiError
from app.documents import (
    AppConfigDocument,
    AssignmentDocument,
    ExperienceDocument,
    ParticipantDocument,
    PaymentProofDocument,
    PolicyDocument,
    ProviderDocument,
    ReservationDocument,
    ScheduleDocument,
    ServiceLogDocument,
    SyncChangeDocument,
    SyncOperationReceiptDocument,
    UserDocument,
)
from app.schemas.assignment import AssignmentCreateSchema, AssignmentUpdateSchema
from app.schemas.config import ReservationRulesUpdateSchema
from app.schemas.experience import ExperienceCreateSchema, ExperienceUpdateSchema
from app.schemas.participant import ParticipantCreateSchema, ParticipantUpdateSchema
from app.schemas.payment_proof import PaymentProofCreateSchema, PaymentProofUpdateSchema
from app.schemas.policy import PolicyCreateSchema, PolicyUpdateSchema
from app.schemas.provider import ProviderCreateSchema, ProviderUpdateSchema
from app.schemas.reservation import (
    ReservationCreateSchema,
    ReservationUpdateSchema,
)
from app.schemas.schedule import ScheduleCreateSchema, ScheduleUpdateSchema
from app.schemas.service_log import ServiceLogCreateSchema, ServiceLogUpdateSchema
from app.schemas.sync import (
    SyncPullRequestSchema,
    SyncPullResponseSchema,
    SyncPullStreamResponseSchema,
    SyncPushOperationSchema,
    SyncPushRequestSchema,
    SyncPushResponseSchema,
    SyncPushResultSchema,
)
from app.services.assignment_service import AssignmentService
from app.services.config_service import RESERVATION_RULES_KEY, ConfigService
from app.services.equine_service import EquineService
from app.services.experience_service import ExperienceService
from app.services.mappers import (
    assignment_to_response,
    equine_to_response,
    experience_to_response,
    participant_to_response,
    payment_proof_to_response,
    policy_to_response,
    provider_to_response,
    reservation_to_response,
    schedule_to_response,
    service_log_to_response,
    user_to_response,
)
from app.services.participant_service import ParticipantService
from app.services.payment_proof_service import PaymentProofService
from app.services.policy_service import PolicyService
from app.services.provider_service import ProviderService
from app.services.reservation_service import ReservationService
from app.services.schedule_service import ScheduleService
from app.services.service_log_service import ServiceLogService


class SyncOperationExecutor:
    def __init__(self) -> None:
        self.config_service = ConfigService()
        self.experience_service = ExperienceService()
        self.schedule_service = ScheduleService()
        self.reservation_service = ReservationService()
        self.participant_service = ParticipantService()
        self.payment_proof_service = PaymentProofService()
        self.assignment_service = AssignmentService()
        self.service_log_service = ServiceLogService()
        self.provider_service = ProviderService()
        self.policy_service = PolicyService()

    async def execute(
        self, *, current_user: UserDocument, operation: SyncPushOperationSchema
    ) -> SyncPushResultSchema:
        try:
            _ensure_operation_permission(current_user=current_user, operation=operation)
            doc = await self._execute_doc(current_user=current_user, operation=operation)
            return SyncPushResultSchema(
                operation_id=operation.operation_id,
                status="applied",
                entity_type=operation.entity_type,
                entity_local_id=operation.entity_local_id,
                entity_remote_id=str(doc.id),
                version=doc.version,
                updated_at=doc.updated_at,
                payload=await _entity_to_response_dict(operation.entity_type, doc),
                error=None,
            )
        except ApiError as exc:
            return SyncPushResultSchema(
                operation_id=operation.operation_id,
                status="conflict" if exc.status_code == 409 else "rejected",
                entity_type=operation.entity_type,
                entity_local_id=operation.entity_local_id,
                entity_remote_id=operation.entity_remote_id,
                version=None,
                updated_at=None,
                payload=None,
                error={
                    "code": exc.code,
                    "message": exc.message,
                    "details": exc.details,
                },
            )

    async def _execute_doc(self, *, current_user: UserDocument, operation: SyncPushOperationSchema):
        entity = operation.entity_type
        op_type = operation.operation_type

        if entity == "experience" and op_type == "create":
            schema = ExperienceCreateSchema(**operation.payload)
            return await self.experience_service.create(schema)
        if entity == "experience" and op_type == "update":
            _require_remote_id(operation)
            await _ensure_base_version(
                ExperienceDocument,
                operation.entity_remote_id,
                operation.base_version,
            )
            schema = ExperienceUpdateSchema(**operation.payload)
            return await self.experience_service.update(operation.entity_remote_id, schema)
        if entity == "experience" and op_type == "delete":
            _require_remote_id(operation)
            await _ensure_base_version(
                ExperienceDocument,
                operation.entity_remote_id,
                operation.base_version,
            )
            return await self.experience_service.deactivate(operation.entity_remote_id)
        if entity == "schedule" and op_type == "create":
            schema = ScheduleCreateSchema(**operation.payload)
            return await self.schedule_service.create(schema)
        if entity == "schedule" and op_type == "update":
            _require_remote_id(operation)
            await _ensure_base_version(
                ScheduleDocument,
                operation.entity_remote_id,
                operation.base_version,
            )
            schema = ScheduleUpdateSchema(**operation.payload)
            return await self.schedule_service.update(operation.entity_remote_id, schema)
        if entity == "schedule" and op_type == "delete":
            _require_remote_id(operation)
            await _ensure_base_version(
                ScheduleDocument,
                operation.entity_remote_id,
                operation.base_version,
            )
            return await self.schedule_service.deactivate(operation.entity_remote_id)
        if entity == "reservation_rules" and op_type == "update":
            await _ensure_reservation_rules_base_version(operation.base_version)
            schema = ReservationRulesUpdateSchema(**operation.payload)
            return await self.config_service.update_reservation_rules_document(schema)
        if entity == "reservation" and op_type == "create":
            schema = ReservationCreateSchema(**operation.payload)
            return await self.reservation_service.create(
                schema.model_dump(), actor_id=current_user.id
            )
        if entity == "reservation" and op_type == "update":
            _require_remote_id(operation)
            await _ensure_base_version(
                ReservationDocument,
                operation.entity_remote_id,
                operation.base_version,
            )
            schema = ReservationUpdateSchema(**operation.payload)
            return await self.reservation_service.update(
                operation.entity_remote_id,
                schema.model_dump(exclude_none=True),
                actor_id=current_user.id,
            )
        if entity == "participant" and op_type == "create":
            reservation_id = _require_field(operation.payload, "reservation_id")
            schema = ParticipantCreateSchema(**operation.payload)
            return await self.participant_service.create(reservation_id, schema)
        if entity == "participant" and op_type == "update":
            _require_remote_id(operation)
            await _ensure_base_version(
                ParticipantDocument,
                operation.entity_remote_id,
                operation.base_version,
            )
            schema = ParticipantUpdateSchema(**operation.payload)
            return await self.participant_service.update(operation.entity_remote_id, schema)
        if entity == "payment_proof" and op_type == "create":
            reservation_id = _require_field(operation.payload, "reservation_id")
            schema = PaymentProofCreateSchema(**operation.payload)
            return await self.payment_proof_service.create(
                reservation_id, schema, actor_id=current_user.id
            )
        if entity == "payment_proof" and op_type == "update":
            _require_remote_id(operation)
            await _ensure_base_version(
                PaymentProofDocument,
                operation.entity_remote_id,
                operation.base_version,
            )
            schema = PaymentProofUpdateSchema(**operation.payload)
            return await self.payment_proof_service.update(operation.entity_remote_id, schema)
        if entity == "assignment" and op_type == "create":
            schema = AssignmentCreateSchema(**operation.payload)
            return await self.assignment_service.create(schema)
        if entity == "assignment" and op_type == "update":
            _require_remote_id(operation)
            await _ensure_base_version(
                AssignmentDocument,
                operation.entity_remote_id,
                operation.base_version,
            )
            schema = AssignmentUpdateSchema(**operation.payload)
            return await self.assignment_service.update(operation.entity_remote_id, schema)
        if entity == "service_log" and op_type == "create":
            schema = ServiceLogCreateSchema(**operation.payload)
            return await self.service_log_service.create(schema)
        if entity == "service_log" and op_type == "update":
            _require_remote_id(operation)
            await _ensure_base_version(
                ServiceLogDocument,
                operation.entity_remote_id,
                operation.base_version,
            )
            schema = ServiceLogUpdateSchema(**operation.payload)
            return await self.service_log_service.update(operation.entity_remote_id, schema)
        if entity == "provider" and op_type == "create":
            schema = ProviderCreateSchema(**operation.payload)
            return await self.provider_service.create(schema)
        if entity == "provider" and op_type == "update":
            _require_remote_id(operation)
            await _ensure_base_version(
                ProviderDocument,
                operation.entity_remote_id,
                operation.base_version,
            )
            schema = ProviderUpdateSchema(**operation.payload)
            return await self.provider_service.update(operation.entity_remote_id, schema)
        if entity == "policy" and op_type == "create":
            schema = PolicyCreateSchema(**operation.payload)
            return await self.policy_service.create(schema)
        if entity == "policy" and op_type == "update":
            _require_remote_id(operation)
            await _ensure_base_version(
                PolicyDocument,
                operation.entity_remote_id,
                operation.base_version,
            )
            schema = PolicyUpdateSchema(**operation.payload)
            return await self.policy_service.update(operation.entity_remote_id, schema)

        raise ApiError(
            status_code=400,
            code=ErrorCode.SYNC_UNSUPPORTED_OPERATION,
            message="Operacion de sincronizacion no soportada.",
            details={"entity_type": entity, "operation_type": op_type},
        )


class SyncService:
    def __init__(self) -> None:
        self.config_service = ConfigService()
        self.experience_service = ExperienceService()
        self.schedule_service = ScheduleService()
        self.equine_service = EquineService()
        self.executor = SyncOperationExecutor()

    async def build_bootstrap(self, *, current_user: UserDocument) -> dict:
        can_read_config = Permission.CONFIG_READ in ROLE_PERMISSIONS[current_user.role]
        experiences = await self.experience_service.list()
        schedules = await self.schedule_service.list()
        equines = await self.equine_service.list()
        cursors = await _latest_stream_cursors()
        if not can_read_config:
            cursors.pop("config", None)
        return {
            "server_time": datetime.now(UTC),
            "user": user_to_response(current_user).model_dump(mode="json"),
            "reservation_rules": (
                (await self.config_service.get_reservation_rules()).model_dump(mode="json")
                if can_read_config
                else None
            ),
            "emergency_contacts": (await self.config_service.get_emergency_contacts()).model_dump(
                mode="json"
            ),
            "experiences": [
                experience_to_response(item).model_dump(mode="json") for item in experiences
            ],
            "schedules": [schedule_to_response(item).model_dump(mode="json") for item in schedules],
            "equines": [equine_to_response(item).model_dump(mode="json") for item in equines],
            "cursors": cursors,
        }

    async def pull_changes(
        self, *, current_user: UserDocument, body: SyncPullRequestSchema
    ) -> SyncPullResponseSchema:
        can_read_config = Permission.CONFIG_READ in ROLE_PERMISSIONS[current_user.role]
        streams: list[SyncPullStreamResponseSchema] = []
        for stream_cursor in body.streams:
            if stream_cursor.name == "config" and not can_read_config:
                streams.append(
                    SyncPullStreamResponseSchema(
                        name=stream_cursor.name,
                        next_cursor=stream_cursor.cursor or "",
                        changes=[],
                    )
                )
                continue
            query = SyncChangeDocument.find({"stream": stream_cursor.name})
            if stream_cursor.cursor:
                try:
                    cursor_id = PydanticObjectId(stream_cursor.cursor)
                except Exception as exc:  # pragma: no cover
                    raise ApiError(
                        status_code=400,
                        code=ErrorCode.SYNC_INVALID_CURSOR,
                        message="Cursor invalido.",
                    ) from exc
                query = query.find({"_id": {"$gt": cursor_id}})
            changes = await query.sort("id").limit(500).to_list()
            next_cursor = str(changes[-1].id) if changes else (stream_cursor.cursor or "")
            streams.append(
                SyncPullStreamResponseSchema(
                    name=stream_cursor.name,
                    next_cursor=next_cursor,
                    changes=[
                        {
                            "change_type": change.change_type,
                            "entity_id": change.entity_id,
                            "version": change.version,
                            "updated_at": change.entity_updated_at,
                            "payload": change.payload,
                        }
                        for change in changes
                    ],
                )
            )
        return SyncPullResponseSchema(server_time=datetime.now(UTC), streams=streams)

    async def push_operations(
        self, *, current_user: UserDocument, body: SyncPushRequestSchema
    ) -> SyncPushResponseSchema:
        results: list[SyncPushResultSchema] = []
        for operation in body.operations:
            receipt = await SyncOperationReceiptDocument.find_one(
                {"user_id": str(current_user.id), "idempotency_key": operation.idempotency_key},
            )
            if receipt is not None:
                results.append(
                    SyncPushResultSchema(
                        operation_id=receipt.operation_id,
                        status=receipt.status,
                        entity_type=receipt.entity_type,
                        entity_local_id=receipt.entity_local_id,
                        entity_remote_id=receipt.entity_remote_id,
                        version=receipt.entity_version,
                        updated_at=receipt.entity_updated_at,
                        payload=receipt.payload,
                        error=receipt.error,
                    )
                )
                continue

            result = await self.executor.execute(current_user=current_user, operation=operation)
            receipt = SyncOperationReceiptDocument(
                user_id=str(current_user.id),
                idempotency_key=operation.idempotency_key,
                operation_id=result.operation_id,
                entity_type=result.entity_type,
                entity_local_id=result.entity_local_id,
                entity_remote_id=result.entity_remote_id,
                status=result.status,
                entity_version=result.version,
                entity_updated_at=result.updated_at,
                payload=result.payload,
                error=result.error.model_dump() if result.error else None,
            )
            await receipt.insert()
            results.append(result)
        return SyncPushResponseSchema(results=results)


async def _ensure_base_version(
    document_class,
    entity_id: str | None,
    base_version: int | None,
) -> None:
    if entity_id is None or base_version is None:
        return
    doc = await document_class.get(entity_id)
    if doc is None:
        return
    if base_version != doc.version:
        raise ApiError(
            status_code=409,
            code=ErrorCode.SYNC_STALE_VERSION,
            message="Entity version is outdated.",
            details={
                "entity_id": entity_id,
                "expected_version": doc.version,
                "received_version": base_version,
            },
        )


async def _ensure_reservation_rules_base_version(base_version: int | None) -> None:
    if base_version is None:
        return
    config = await AppConfigDocument.find_one({"key": RESERVATION_RULES_KEY})
    if config is None:
        return
    if base_version != config.version:
        raise ApiError(
            status_code=409,
            code=ErrorCode.SYNC_STALE_VERSION,
            message="Entity version is outdated.",
            details={
                "entity_id": str(config.id),
                "expected_version": config.version,
                "received_version": base_version,
            },
        )


def _require_remote_id(operation: SyncPushOperationSchema) -> None:
    if not operation.entity_remote_id:
        raise ApiError(
            status_code=400,
            code=ErrorCode.SYNC_UNSUPPORTED_OPERATION,
            message="entity_remote_id es obligatorio para esta operacion.",
        )


def _require_field(payload: dict, key: str) -> str:
    value = payload.get(key)
    if not value:
        raise ApiError(
            status_code=400,
            code=ErrorCode.VALIDATION_ERROR,
            message=f"El campo {key} es obligatorio.",
        )
    return str(value)


SYNC_REQUIRED_PERMISSION: dict[tuple[str, str], Permission] = {
    ("experience", "create"): Permission.EXPERIENCE_CREATE,
    ("experience", "update"): Permission.EXPERIENCE_UPDATE,
    ("experience", "delete"): Permission.EXPERIENCE_DELETE,
    ("schedule", "create"): Permission.SCHEDULE_CREATE,
    ("schedule", "update"): Permission.SCHEDULE_UPDATE,
    ("schedule", "delete"): Permission.SCHEDULE_DELETE,
    ("reservation_rules", "update"): Permission.CONFIG_UPDATE,
    ("reservation", "create"): Permission.RESERVATION_CREATE,
    ("reservation", "update"): Permission.RESERVATION_UPDATE,
    ("participant", "create"): Permission.PARTICIPANT_CREATE,
    ("participant", "update"): Permission.PARTICIPANT_UPDATE,
    ("payment_proof", "create"): Permission.PAYMENT_PROOF_CREATE,
    ("payment_proof", "update"): Permission.PAYMENT_VERIFY,
    ("assignment", "create"): Permission.ASSIGNMENT_CREATE,
    ("assignment", "update"): Permission.ASSIGNMENT_UPDATE,
    ("service_log", "create"): Permission.LOG_CREATE,
    ("service_log", "update"): Permission.LOG_UPDATE,
    ("provider", "create"): Permission.PROVIDER_CREATE,
    ("provider", "update"): Permission.PROVIDER_UPDATE,
    ("policy", "create"): Permission.POLICY_CREATE,
    ("policy", "update"): Permission.POLICY_UPDATE,
}


def _ensure_operation_permission(
    *, current_user: UserDocument, operation: SyncPushOperationSchema
) -> None:
    required = SYNC_REQUIRED_PERMISSION.get((operation.entity_type, operation.operation_type))
    if required is None:
        return
    user_permissions = ROLE_PERMISSIONS[current_user.role]
    if required in user_permissions:
        return
    raise ApiError(
        status_code=403,
        code=ErrorCode.AUTH_FORBIDDEN,
        message="No tiene permisos para realizar esta accion.",
        details={"missing_permissions": [required.value]},
    )


async def _entity_to_response_dict(entity_type: str, doc) -> dict:
    if entity_type == "experience":
        return experience_to_response(doc).model_dump(mode="json")
    if entity_type == "schedule":
        return schedule_to_response(doc).model_dump(mode="json")
    if entity_type == "reservation_rules":
        if isinstance(doc, AppConfigDocument) and doc.reservation_rules is not None:
            return doc.reservation_rules.model_dump(mode="json")
        return {}
    if entity_type == "reservation":
        result = await reservation_to_response(doc)
        return result.model_dump(mode="json")
    if entity_type == "participant":
        return participant_to_response(doc).model_dump(mode="json")
    if entity_type == "payment_proof":
        return payment_proof_to_response(doc).model_dump(mode="json")
    if entity_type == "assignment":
        return assignment_to_response(doc).model_dump(mode="json")
    if entity_type == "service_log":
        return service_log_to_response(doc).model_dump(mode="json")
    if entity_type == "provider":
        return provider_to_response(doc).model_dump(mode="json")
    if entity_type == "policy":
        return policy_to_response(doc).model_dump(mode="json")
    return doc.model_dump(mode="json")


async def _latest_stream_cursors() -> dict[str, str]:
    streams = (
        "reservations",
        "participants",
        "payment_proofs",
        "assignments",
        "logs",
        "experiences",
        "schedules",
        "config",
        "equines",
        "providers",
        "policies",
    )
    cursors: dict[str, str] = {}
    for stream in streams:
        latest = (
            await SyncChangeDocument.find({"stream": stream})
            .sort("-id")
            .first_or_none()
        )
        cursors[stream] = str(latest.id) if latest else ""
    return cursors
