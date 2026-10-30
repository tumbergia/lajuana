"""Push-operation handler for app config and reservation rules.

Dependencies
------------
* ``ConfigService`` (only for reservation_rules updates)
"""

from app.schemas.config import ReservationRulesUpdateSchema
from app.schemas.sync import SyncPushOperationSchema
from app.services.config_service import ConfigService
from app.services.sync_handlers._shared import ensure_reservation_rules_base_version


class ConfigSyncHandler:
    """Handles push operations for config/reservation_rules (no entity prefix needed)."""

    def __init__(self, config_service: ConfigService) -> None:
        self.config_service = config_service

    async def handle(
        self,
        *,
        entity: str,
        op_type: str,
        operation: SyncPushOperationSchema,
        current_user,
    ):
        if entity == "reservation_rules" and op_type == "update":
            await ensure_reservation_rules_base_version(operation.base_version)
            schema = ReservationRulesUpdateSchema(**operation.payload)
            return await self.config_service.update_reservation_rules_document(schema)
        return None
