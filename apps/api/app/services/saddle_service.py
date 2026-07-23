from __future__ import annotations

import re
import unicodedata

from beanie import PydanticObjectId

from app.common.labels import ErrorCode
from app.core.errors import ApiError
from app.documents import AssignmentDocument, SaddleDocument
from app.schemas.saddle import SaddleCreateSchema, SaddleUpdateSchema
from app.services.base_service import BaseService


def _normalize_lookup_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_text = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    cleaned = re.sub(r"[^a-z0-9._-]+", " ", ascii_text.lower()).strip()
    return re.sub(r"\s+", " ", cleaned)


def _build_saddle_label(saddle: SaddleDocument) -> str:
    if saddle.name:
        return f"{saddle.code} ({saddle.name})"
    return saddle.code


class SaddleService(BaseService[SaddleDocument, SaddleCreateSchema, SaddleUpdateSchema]):
    document_class = SaddleDocument
    not_found_code = ErrorCode.SADDLE_NOT_FOUND
    not_found_message = "Silla no encontrada."
    sync_entity_type = "saddle"

    async def resolve_saddle_reference(self, reference: str) -> dict[str, object]:
        query = reference.strip()
        if not query:
            return {"status": "missing"}

        normalized_query = _normalize_lookup_text(query)
        saddles = await self.list(limit=200)
        candidates: list[dict[str, object]] = []

        for saddle in saddles:
            code = _normalize_lookup_text(saddle.code)
            name = _normalize_lookup_text(saddle.name or "")
            name_tokens = [token for token in name.split(" ") if token]
            score = 0

            if normalized_query == code:
                score = 100
            elif name and normalized_query == name:
                score = 92
            elif normalized_query in name_tokens:
                score = 88
            elif code.startswith(normalized_query) or any(token.startswith(normalized_query) for token in name_tokens):
                score = 80
            elif normalized_query in code or (name and normalized_query in name):
                score = 64

            if score == 0:
                continue

            candidates.append(
                {
                    "score": score,
                    "saddle": saddle,
                    "summary": {
                        "saddle_id": str(saddle.id),
                        "code": saddle.code,
                        "name": saddle.name,
                        "is_available": saddle.is_available,
                        "label": _build_saddle_label(saddle),
                    },
                }
            )

        if not candidates:
            return {"status": "not_found", "reference": query, "matches": []}

        candidates.sort(
            key=lambda item: (
                -int(item["score"]),
                not bool(getattr(item["saddle"], "is_available", True)),
                len(getattr(item["saddle"], "code", "")),
            )
        )
        top_score = int(candidates[0]["score"])
        top_candidates = [item for item in candidates if int(item["score"]) == top_score]

        if len(top_candidates) == 1 and top_score >= 80:
            saddle = top_candidates[0]["saddle"]
            return {
                "status": "resolved",
                "reference": query,
                "saddle_id": str(saddle.id),
                "label": _build_saddle_label(saddle),
                "match_score": top_score,
            }

        return {
            "status": "ambiguous",
            "reference": query,
            "matches": [item["summary"] for item in candidates[:5]],
        }

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
