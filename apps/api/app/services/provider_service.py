from app.common.labels import ErrorCode
from app.documents import ProviderDocument
from app.schemas.provider import ProviderCreateSchema, ProviderUpdateSchema
from app.services.base_service import BaseService


class ProviderService(BaseService[ProviderDocument, ProviderCreateSchema, ProviderUpdateSchema]):
    document_class = ProviderDocument
    not_found_code = ErrorCode.PROVIDER_NOT_FOUND
    not_found_message = "Proveedor no encontrado."
    sync_entity_type = "provider"

    async def delete(self, provider_id: str) -> None:
        """Desactiva un proveedor sin borrarlo lógicamente."""
        doc = await self.get(provider_id)
        doc.is_active = False
        await doc.save()
