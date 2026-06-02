"""Sync operation handlers.

Each handler encapsulates push-operation logic for a group of related
entity types.  Handlers are instantiated by ``SyncService`` and called
from ``SyncOperationExecutor.execute()``.

Every handler exposes the same interface::

    async def handle(
        self,
        *,
        entity: str,
        op_type: str,
        operation: SyncPushOperationSchema,
        current_user: UserDocument,
    ) -> Document:
        ...
"""

from app.services.sync_handlers.experience_handler import ExperienceSyncHandler
from app.services.sync_handlers.reservation_handler import ReservationSyncHandler
from app.services.sync_handlers.resource_handler import ResourceSyncHandler
from app.services.sync_handlers.config_handler import ConfigSyncHandler

__all__ = [
    "ConfigSyncHandler",
    "ExperienceSyncHandler",
    "ReservationSyncHandler",
    "ResourceSyncHandler",
]
