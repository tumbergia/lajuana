"""Push-operation handler for providers, policies and saddles.

Dependencies
------------
* ``ProviderService``
* ``PolicyService``
* ``SaddleService``
"""

from app.documents import PolicyDocument, ProviderDocument, SaddleDocument
from app.schemas.policy import PolicyCreateSchema, PolicyUpdateSchema
from app.schemas.provider import ProviderCreateSchema, ProviderUpdateSchema
from app.schemas.saddle import SaddleCreateSchema, SaddleUpdateSchema
from app.schemas.sync import SyncPushOperationSchema
from app.services.policy_service import PolicyService
from app.services.provider_service import ProviderService
from app.services.saddle_service import SaddleService
from app.services.sync_handlers._shared import ensure_base_version, require_remote_id


class ResourceSyncHandler:
    """Handles push operations for ``provider``, ``policy`` and ``saddle``."""

    def __init__(
        self,
        provider_service: ProviderService,
        policy_service: PolicyService,
        saddle_service: SaddleService | None = None,
    ) -> None:
        self.provider_service = provider_service
        self.policy_service = policy_service
        self.saddle_service = saddle_service

    async def handle(
        self,
        *,
        entity: str,
        op_type: str,
        operation: SyncPushOperationSchema,
        current_user,
    ):
        if entity == "provider":
            return await self._handle_provider(operation, op_type)
        if entity == "policy":
            return await self._handle_policy(operation, op_type)
        if entity == "saddle":
            return await self._handle_saddle(operation, op_type)
        return None

    async def _handle_saddle(self, operation, op_type):
        if self.saddle_service is None:
            return None
        if op_type == "create":
            schema = SaddleCreateSchema(**operation.payload)
            return await self.saddle_service.create(schema)
        if op_type == "update":
            require_remote_id(operation)
            await ensure_base_version(SaddleDocument, operation.entity_remote_id, operation.base_version)
            schema = SaddleUpdateSchema(**operation.payload)
            return await self.saddle_service.update(operation.entity_remote_id, schema)
        if op_type == "delete":
            require_remote_id(operation)
            await ensure_base_version(SaddleDocument, operation.entity_remote_id, operation.base_version)
            return await self.saddle_service.soft_delete(operation.entity_remote_id)
        if op_type == "restore":
            require_remote_id(operation)
            return await self.saddle_service.restore(operation.entity_remote_id)
        return None

    async def _handle_provider(self, operation, op_type):
        if op_type == "create":
            schema = ProviderCreateSchema(**operation.payload)
            return await self.provider_service.create(schema)
        if op_type == "update":
            require_remote_id(operation)
            await ensure_base_version(ProviderDocument, operation.entity_remote_id, operation.base_version)
            schema = ProviderUpdateSchema(**operation.payload)
            return await self.provider_service.update(operation.entity_remote_id, schema)
        return None

    async def _handle_policy(self, operation, op_type):
        if op_type == "create":
            schema = PolicyCreateSchema(**operation.payload)
            return await self.policy_service.create(schema)
        if op_type == "update":
            require_remote_id(operation)
            await ensure_base_version(PolicyDocument, operation.entity_remote_id, operation.base_version)
            schema = PolicyUpdateSchema(**operation.payload)
            return await self.policy_service.update(operation.entity_remote_id, schema)
        return None
