from app.common.labels import ErrorCode
from app.core.errors import ApiError
from app.documents import PolicyDocument, ProviderDocument, ReservationDocument
from app.schemas.policy import PolicyCreateSchema, PolicyUpdateSchema


class PolicyService:
    async def create(self, payload: PolicyCreateSchema) -> PolicyDocument:
        reservation = await ReservationDocument.get(payload.reservation_id)
        if reservation is None:
            raise ApiError(
                status_code=404,
                code=ErrorCode.RESERVATION_NOT_FOUND,
                message="Reserva no encontrada.",
            )
        provider_id = None
        if payload.provider_id is not None:
            provider = await ProviderDocument.get(payload.provider_id)
            if provider is None:
                raise ApiError(
                    status_code=404,
                    code=ErrorCode.PROVIDER_NOT_FOUND,
                    message="Proveedor no encontrado.",
                )
            provider_id = provider.id
        doc = PolicyDocument(
            reservation_id=reservation.id,
            provider_id=provider_id,
            policy_number=payload.policy_number,
            issued_at=payload.issued_at,
            expires_at=payload.expires_at,
            notes=payload.notes,
        )
        await doc.insert()
        return doc

    async def get(self, policy_id: str) -> PolicyDocument:
        doc = await PolicyDocument.get(policy_id)
        if doc is None:
            raise ApiError(
                status_code=404,
                code=ErrorCode.POLICY_NOT_FOUND,
                message="Póliza no encontrada.",
            )
        return doc

    async def update(self, policy_id: str, payload: PolicyUpdateSchema) -> PolicyDocument:
        doc = await self.get(policy_id)
        updates = payload.model_dump(exclude_none=True)
        if "provider_id" in updates and updates["provider_id"] is not None:
            provider = await ProviderDocument.get(updates["provider_id"])
            if provider is None:
                raise ApiError(
                    status_code=404,
                    code=ErrorCode.PROVIDER_NOT_FOUND,
                    message="Proveedor no encontrado.",
                )
            updates["provider_id"] = provider.id
        for field, value in updates.items():
            setattr(doc, field, value)
        await doc.save()
        return doc
