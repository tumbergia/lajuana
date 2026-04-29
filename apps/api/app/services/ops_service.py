from app.documents import ServiceLogDocument
from app.schemas.service_log import ServiceLogCreateSchema
from app.services.service_log_service import ServiceLogService


class OpsService:
    def __init__(self, service_log_service: ServiceLogService | None = None) -> None:
        self.service_log_service = service_log_service or ServiceLogService()

    async def create_log(self, payload: ServiceLogCreateSchema) -> ServiceLogDocument:
        return await self.service_log_service.create(payload)
