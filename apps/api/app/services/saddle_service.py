from __future__ import annotations

from beanie import PydanticObjectId

from app.common.labels import ErrorCode
from app.core.errors import ApiError
from app.documents import AssignmentDocument, SaddleDocument
from app.schemas.saddle import SaddleCreateSchema, SaddleUpdateSchema
from app.services.base_service import BaseService


class SaddleService(BaseService[SaddleDocument, SaddleCreateSchema, SaddleUpdateSchema]):
    document_class = SaddleDocument
    not_found_code = ErrorCode.SADDLE_NOT_FOUND
    not_found_message = "Silla no encontrada."
    sync_entity_type = "saddle"

    async def create(self, payload: SaddleCreateSchema) -> SaddleDocument:
        existing = await SaddleDocument.find_one({"code": payload.code})
        if existing is not None:
            raise ApiError(
                status_code=409,
                code=ErrorCode.SADDLE_CODE_ALREADY_EXISTS,
                message="El código de silla ya existe.",
            )
        return await super().create(payload)

    async def update(self, saddle_id: str, payload: SaddleUpdateSchema) -> SaddleDocument:
        updates = payload.model_dump(exclude_none=True)
        if "code" in updates:
            existing = await SaddleDocument.find_one({"code": updates["code"]})
            if existing is not None and str(existing.id) != saddle_id:
                raise ApiError(
                    status_code=409,
                    code=ErrorCode.SADDLE_CODE_ALREADY_EXISTS,
                    message="El código de silla ya existe.",
                )
        return await super().update(saddle_id, payload)

    async def list_available_for_reservation(
        self,
        reservation_id: str,
        limit: int = 200,
        skip: int = 0,
    ) -> list[tuple[object, str | None]]:
        """Retorna (saddle_doc, block_reason) para cada silla.

        block_reason is None → asignable.
        block_reason is set → explica por qué NO puede asignarse.
        """
        my_assignments = await AssignmentDocument.find(
            {"reservation_id": PydanticObjectId(reservation_id), "is_active": True},
        ).to_list()
        my_assigned_saddle_ids = {
            str(a.saddle_id) for a in my_assignments if a.saddle_id
        }

        all_saddles = await SaddleDocument.find({}).skip(skip).limit(limit).to_list()

        result: list[tuple[object, str | None]] = []
        for saddle in all_saddles:
            reason: str | None = None
            sid_str = str(saddle.id)

            if saddle.deleted_at is not None:
                reason = "Silla eliminada"
            elif not saddle.is_available:
                reason = "Silla no disponible"
            elif sid_str in my_assigned_saddle_ids:
                reason = "Ya asignada a esta reserva"

            result.append((saddle, reason))
        return result
