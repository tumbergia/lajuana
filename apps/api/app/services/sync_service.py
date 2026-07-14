"""Synchronisation orchestrator — bootstrap, pull, push.

``SyncService`` is the public entry point.  It delegates push operations to
specialised handlers under ``sync_handlers/``, each responsible for a group
of related entity types (≤5 service dependencies per handler).

Architecture
------------
::

    SyncService
     ├── build_bootstrap()    — full initial sync snapshot
     ├── pull_changes()       — incremental changes via cursor
     └── push_operations()    — apply offline mutations
          └── SyncOperationExecutor
               ├── ExperienceSyncHandler  (experience, schedule)
               ├── ReservationSyncHandler (reservation, participant, …)
               ├── ResourceSyncHandler    (provider, policy)
               └── ConfigSyncHandler      (reservation_rules)
"""

from datetime import UTC, datetime

from beanie import PydanticObjectId
from pydantic import ValidationError

from app.common.enums import ROLE_PERMISSIONS, Permission
from app.common.labels import ErrorCode
from app.core.errors import ApiError
from app.documents import (
    SyncChangeDocument,
    SyncOperationReceiptDocument,
    UserDocument,
)
from app.schemas.sync import (
    SyncPullRequestSchema,
    SyncPullResponseSchema,
    SyncPullStreamResponseSchema,
    SyncPushOperationSchema,
    SyncPushRequestSchema,
    SyncPushResponseSchema,
    SyncPushResultSchema,
)
from app.services.config_service import ConfigService
from app.services.mappers import (
    equine_to_response,
    experience_to_response,
    reservation_to_response,
    saddle_to_response,
    user_to_response,
)
from app.services.sync_change_recorder import entity_to_response_dict
from app.services.sync_handlers import (
    ConfigSyncHandler,
    ExperienceSyncHandler,
    ReservationSyncHandler,
    ResourceSyncHandler,
)

# ──────────────────────────────────────────────────────────────────────
# Permission map — (entity_type, operation_type) → required Permission
# ──────────────────────────────────────────────────────────────────────

SYNC_REQUIRED_PERMISSION: dict[tuple[str, str], Permission] = {
    ("experience", "create"): Permission.EXPERIENCE_CREATE,
    ("experience", "update"): Permission.EXPERIENCE_UPDATE,
    ("experience", "delete"): Permission.EXPERIENCE_DELETE,
    ("reservation_rules", "update"): Permission.CONFIG_UPDATE,
    ("reservation", "create"): Permission.RESERVATION_CREATE,
    ("reservation", "update"): Permission.RESERVATION_UPDATE,
    ("participant", "create"): Permission.PARTICIPANT_CREATE,
    ("participant", "update"): Permission.PARTICIPANT_UPDATE,
    ("payment_proof", "create"): Permission.PAYMENT_PROOF_CREATE,
    ("payment_proof", "update"): Permission.PAYMENT_VERIFY,
    ("assignment", "create"): Permission.ASSIGNMENT_CREATE,
    ("assignment", "update"): Permission.ASSIGNMENT_UPDATE,
    ("assignment", "delete"): Permission.ASSIGNMENT_UPDATE,
    ("service_log", "create"): Permission.LOG_CREATE,
    ("service_log", "update"): Permission.LOG_UPDATE,
    ("service_log", "delete"): Permission.LOG_UPDATE,
    ("provider", "create"): Permission.PROVIDER_CREATE,
    ("provider", "update"): Permission.PROVIDER_UPDATE,
    ("policy", "create"): Permission.POLICY_CREATE,
    ("policy", "update"): Permission.POLICY_UPDATE,
    ("saddle", "create"): Permission.SADDLE_CREATE,
    ("saddle", "update"): Permission.SADDLE_UPDATE,
    ("saddle", "delete"): Permission.SADDLE_DELETE,
    ("saddle", "restore"): Permission.SADDLE_DELETE,
}


def _ensure_operation_permission(
    *, current_user: UserDocument, operation: SyncPushOperationSchema
) -> None:
    """Raise ``403`` if *current_user* lacks the permission for *operation*."""
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
    """Convert a domain document to a JSON-safe response dict.

    Delegado al recorder para mantener un único punto de verdad del mapeo
    entidad → payload (compartido con el change feed).
    """
    return await entity_to_response_dict(entity_type, doc)


async def _latest_stream_cursors() -> dict[str, str]:
    """Return the latest cursor for every tracked change stream."""
    streams = (
        "reservations", "participants", "payment_proofs", "assignments",
        "logs", "experiences", "config", "equines",
        "providers", "policies", "saddles",
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


# ──────────────────────────────────────────────────────────────────────
# SyncOperationExecutor
# ──────────────────────────────────────────────────────────────────────


class SyncOperationExecutor:
    """Executes individual push operations by delegating to handlers.

    Each handler owns a group of entity types and returns the created/updated
    document, or ``None`` if the entity type isn't its responsibility.
    """

    def __init__(
        self,
        experience_handler: ExperienceSyncHandler,
        reservation_handler: ReservationSyncHandler,
        resource_handler: ResourceSyncHandler,
        config_handler: ConfigSyncHandler,
    ) -> None:
        self._handlers = [
            experience_handler,
            reservation_handler,
            resource_handler,
            config_handler,
        ]

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
        except ValidationError as exc:
            return SyncPushResultSchema(
                operation_id=operation.operation_id,
                status="rejected",
                entity_type=operation.entity_type,
                entity_local_id=operation.entity_local_id,
                entity_remote_id=operation.entity_remote_id,
                version=None,
                updated_at=None,
                payload=None,
                error={
                    "code": ErrorCode.VALIDATION_ERROR,
                    "message": "La solicitud contiene datos inválidos.",
                    "details": {"fields": exc.errors(include_url=False)},
                },
            )

    async def _execute_doc(
        self, *, current_user: UserDocument, operation: SyncPushOperationSchema
    ):
        entity = operation.entity_type
        op_type = operation.operation_type

        # Try each handler — the first one that recognises the entity type
        # returns a document, others return None.
        for handler in self._handlers:
            doc = await handler.handle(
                entity=entity, op_type=op_type, operation=operation, current_user=current_user,
            )
            if doc is not None:
                return doc

        raise ApiError(
            status_code=400,
            code=ErrorCode.SYNC_UNSUPPORTED_OPERATION,
            message="Operacion de sincronizacion no soportada.",
            details={"entity_type": entity, "operation_type": op_type},
        )


# ──────────────────────────────────────────────────────────────────────
# SyncService — public API
# ──────────────────────────────────────────────────────────────────────


class SyncService:
    """Top-level sync orchestrator — bootstrap, pull, push.

    Takes all needed services directly and constructs handlers internally.
    External callers pass services; SyncService wires the handlers.
    """

    def __init__(
        self,
        config_service: ConfigService,
        experience_service=None,
        equine_service=None,
        reservation_service=None,
        participant_service=None,
        payment_proof_service=None,
        assignment_service=None,
        service_log_service=None,
        provider_service=None,
        policy_service=None,
        saddle_service=None,
    ) -> None:
        self.config_service = config_service

        # Build handlers (services are passed from DI container)
        self._experience_handler = ExperienceSyncHandler(
            experience_service=experience_service,
        )
        self._reservation_handler = ReservationSyncHandler(
            reservation_service=reservation_service,
            participant_service=participant_service,
            payment_proof_service=payment_proof_service,
            assignment_service=assignment_service,
            service_log_service=service_log_service,
        )
        self._resource_handler = ResourceSyncHandler(
            provider_service=provider_service,
            policy_service=policy_service,
            saddle_service=saddle_service,
        )
        self._config_handler = ConfigSyncHandler(config_service=config_service)

        # Keep references needed by build_bootstrap (read operations)
        self._experience_service = experience_service
        self._equine_service = equine_service
        self._saddle_service = saddle_service
        self._reservation_service = reservation_service

        self.executor = SyncOperationExecutor(
            experience_handler=self._experience_handler,
            reservation_handler=self._reservation_handler,
            resource_handler=self._resource_handler,
            config_handler=self._config_handler,
        )

    async def build_bootstrap(self, *, current_user: UserDocument) -> dict:
        """Full initial sync snapshot — experiences, equines, reservas activas+recientes, etc."""
        can_read_config = Permission.CONFIG_READ in ROLE_PERMISSIONS[current_user.role]
        experiences = await self._experience_service.list()
        equines = await self._equine_service.list()
        saddles = await self._saddle_service.list() if self._saddle_service else []
        reservations = (
            await self._reservation_service.list_for_bootstrap(actor_role=current_user.role)
            if self._reservation_service
            else []
        )
        reservations_response = [await reservation_to_response(r) for r in reservations]
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
            "equines": [equine_to_response(item).model_dump(mode="json") for item in equines],
            "saddles": [saddle_to_response(item).model_dump(mode="json") for item in saddles],
            # Nested participants/payment_proofs por reserva — coincide con lo que
            # ReservationDetailDto.fromJson (mobile) espera para cachear offline.
            "reservations": [item.model_dump(mode="json") for item in reservations_response],
            "cursors": cursors,
        }

    async def pull_changes(
        self, *, current_user: UserDocument, body: SyncPullRequestSchema
    ) -> SyncPullResponseSchema:
        """Incremental pull — fetch changes since cursor per stream."""
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
        """Apply offline mutations with idempotency dedup."""
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
