"""Push-operation handler for experiences.

Dependencies
------------
* ``ExperienceService`` — experience CRUD
"""

from app.documents import ExperienceDocument
from app.schemas.experience import ExperienceCreateSchema, ExperienceUpdateSchema
from app.schemas.sync import SyncPushOperationSchema
from app.services.experience_service import ExperienceService
from app.services.sync_handlers._shared import (
    ensure_base_version,
    require_remote_id,
    strip_null_values,
)


class ExperienceSyncHandler:
    """Handles push operations for ``experience`` entities."""

    def __init__(
        self,
        experience_service: ExperienceService,
    ) -> None:
        self.experience_service = experience_service

    async def handle(
        self,
        *,
        entity: str,
        op_type: str,
        operation: SyncPushOperationSchema,
        current_user,  # UserDocument — kept for interface compatibility
    ):
        if entity != "experience":
            return None
        return await self._handle_experience(operation, op_type)

    async def _handle_experience(self, operation, op_type):
        if op_type == "create":
            schema = ExperienceCreateSchema(**strip_null_values(operation.payload))
            return await self.experience_service.create(schema)
        if op_type == "update":
            require_remote_id(operation)
            await ensure_base_version(
                ExperienceDocument, operation.entity_remote_id, operation.base_version
            )
            schema = ExperienceUpdateSchema(**operation.payload)
            return await self.experience_service.update(operation.entity_remote_id, schema)
        if op_type == "delete":
            require_remote_id(operation)
            await ensure_base_version(
                ExperienceDocument, operation.entity_remote_id, operation.base_version
            )
            return await self.experience_service.deactivate(operation.entity_remote_id)
        if op_type == "purge":
            require_remote_id(operation)
            await ensure_base_version(
                ExperienceDocument, operation.entity_remote_id, operation.base_version
            )
            return await self.experience_service.purge(operation.entity_remote_id)
        return None
