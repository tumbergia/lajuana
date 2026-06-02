"""Push-operation handler for experiences and schedules.

Dependencies
------------
* ``ExperienceService`` — experience CRUD
* ``ScheduleService`` — schedule CRUD
"""

from app.documents import ExperienceDocument, ScheduleDocument
from app.schemas.experience import ExperienceCreateSchema, ExperienceUpdateSchema
from app.schemas.schedule import ScheduleCreateSchema, ScheduleUpdateSchema
from app.schemas.sync import SyncPushOperationSchema
from app.services.experience_service import ExperienceService
from app.services.schedule_service import ScheduleService
from app.services.sync_handlers._shared import ensure_base_version, require_remote_id


class ExperienceSyncHandler:
    """Handles push operations for ``experience`` and ``schedule`` entities."""

    def __init__(
        self,
        experience_service: ExperienceService,
        schedule_service: ScheduleService,
    ) -> None:
        self.experience_service = experience_service
        self.schedule_service = schedule_service

    async def handle(
        self,
        *,
        entity: str,
        op_type: str,
        operation: SyncPushOperationSchema,
        current_user,  # UserDocument — kept for interface compatibility
    ):
        if entity == "experience":
            return await self._handle_experience(operation, op_type)
        if entity == "schedule":
            return await self._handle_schedule(operation, op_type)
        return None  # not handled here

    async def _handle_experience(self, operation, op_type):
        if op_type == "create":
            schema = ExperienceCreateSchema(**operation.payload)
            return await self.experience_service.create(schema)
        if op_type == "update":
            require_remote_id(operation)
            await ensure_base_version(ExperienceDocument, operation.entity_remote_id, operation.base_version)
            schema = ExperienceUpdateSchema(**operation.payload)
            return await self.experience_service.update(operation.entity_remote_id, schema)
        if op_type == "delete":
            require_remote_id(operation)
            await ensure_base_version(ExperienceDocument, operation.entity_remote_id, operation.base_version)
            return await self.experience_service.deactivate(operation.entity_remote_id)
        return None

    async def _handle_schedule(self, operation, op_type):
        if op_type == "create":
            schema = ScheduleCreateSchema(**operation.payload)
            return await self.schedule_service.create(schema)
        if op_type == "update":
            require_remote_id(operation)
            await ensure_base_version(ScheduleDocument, operation.entity_remote_id, operation.base_version)
            schema = ScheduleUpdateSchema(**operation.payload)
            return await self.schedule_service.update(operation.entity_remote_id, schema)
        if op_type == "delete":
            require_remote_id(operation)
            await ensure_base_version(ScheduleDocument, operation.entity_remote_id, operation.base_version)
            return await self.schedule_service.deactivate(operation.entity_remote_id)
        return None
