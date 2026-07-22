from __future__ import annotations

import re
import unicodedata

from beanie import PydanticObjectId
from pymongo.errors import DuplicateKeyError

from app.common.labels import ErrorCode
from app.core.errors import ApiError
from app.documents import ExperienceDocument, ReservationDocument
from app.schemas.experience import (
    ExperienceCreateSchema,
    ExperiencePricingSchema,
    ExperiencePricingTierSchema,
    ExperienceQuoteRequestSchema,
    ExperienceQuoteResponseSchema,
    ExperienceUpdateSchema,
)
from app.services.sync_change_recorder import record_change


def _normalize_lookup_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_text = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    cleaned = re.sub(r"[^a-z0-9._-]+", " ", ascii_text.lower()).strip()
    return re.sub(r"\s+", " ", cleaned)


def _build_experience_label(experience: ExperienceDocument) -> str:
    if experience.slug:
        return f"{experience.name} ({experience.slug})"
    return experience.name


class ExperienceService:
    async def resolve_experience_reference(self, reference: str) -> dict[str, object]:
        query = reference.strip()
        if not query:
            return {"status": "missing"}

        normalized_query = _normalize_lookup_text(query)
        query_has_multiple_tokens = " " in normalized_query
        experiences = await self.list(limit=200)
        candidates: list[dict[str, object]] = []

        for experience in experiences:
            name = _normalize_lookup_text(experience.name)
            slug = _normalize_lookup_text(experience.slug)
            aliases = [_normalize_lookup_text(alias) for alias in getattr(experience, "aliases", []) if alias]
            name_tokens = [token for token in name.split(" ") if token]
            alias_tokens = [token for alias in aliases for token in alias.split(" ") if token]
            score = 0

            if normalized_query == slug:
                score = 100
            elif normalized_query in aliases:
                score = 97
            elif query_has_multiple_tokens and normalized_query == name:
                score = 95
            elif normalized_query in name_tokens or normalized_query in alias_tokens:
                score = 88
            elif name.startswith(normalized_query) or slug.startswith(normalized_query):
                score = 80
            elif any(alias.startswith(normalized_query) for alias in aliases):
                score = 80
            elif normalized_query in name or normalized_query in slug or any(normalized_query in alias for alias in aliases):
                score = 64

            if score == 0:
                continue

            candidates.append(
                {
                    "score": score,
                    "experience": experience,
                    "summary": {
                        "experience_id": str(experience.id),
                        "name": experience.name,
                        "slug": experience.slug,
                        "is_active": experience.is_active,
                        "label": _build_experience_label(experience),
                    },
                }
            )

        if not candidates:
            return {"status": "not_found", "reference": query, "matches": []}

        candidates.sort(
            key=lambda item: (
                -int(item["score"]),
                not bool(getattr(item["experience"], "is_active", True)),
                len(getattr(item["experience"], "name", "")),
            )
        )
        top_score = int(candidates[0]["score"])
        top_candidates = [item for item in candidates if int(item["score"]) == top_score]

        if len(top_candidates) == 1 and top_score >= 80:
            experience = top_candidates[0]["experience"]
            return {
                "status": "resolved",
                "reference": query,
                "experience_id": str(experience.id),
                "label": _build_experience_label(experience),
                "match_score": top_score,
            }

        return {
            "status": "ambiguous",
            "reference": query,
            "matches": [item["summary"] for item in candidates[:5]],
        }

    @staticmethod
    def _raise_conflict_from_duplicate(exc: DuplicateKeyError) -> None:
        details = exc.details if isinstance(exc.details, dict) else {}
        key_pattern = details.get("keyPattern", {})
        if "slug" in key_pattern or "slug_1" in str(exc):
            raise ApiError(
                status_code=409,
                code=ErrorCode.EXPERIENCE_SLUG_ALREADY_EXISTS,
                message="Ya existe una experiencia con ese slug.",
                details={"field": "slug"},
            ) from exc
        raise ApiError(
            status_code=409,
            code=ErrorCode.CONFLICT,
            message="Existe un conflicto al guardar la experiencia.",
            details={"collection": "experiences"},
        ) from exc

    def _validate_duration(
        self,
        *,
        duration_hours: int | None,
        duration_days: int | None,
        duration: object | None,
    ) -> None:
        if duration is None and duration_hours is None and duration_days is None:
            raise ApiError(
                status_code=400,
                code=ErrorCode.EXPERIENCE_INVALID_DURATION,
                message="Debes informar duracion estructurada o duracion en horas/dias.",
            )

    def _validate_pricing(self, pricing: ExperiencePricingSchema | None) -> None:
        if pricing is None:
            return
        tiers = sorted(
            pricing.tiers,
            key=lambda tier: (tier.min_participants, tier.max_participants),
        )
        if not tiers:
            raise ApiError(
                status_code=400,
                code=ErrorCode.EXPERIENCE_PRICING_TIERS_REQUIRED,
                message="La experiencia debe definir al menos un rango tarifario.",
            )
        previous: ExperiencePricingTierSchema | None = None
        for tier in tiers:
            if tier.min_participants > tier.max_participants:
                raise ApiError(
                    status_code=400,
                    code=ErrorCode.EXPERIENCE_PRICING_TIER_INVALID_RANGE,
                    message="Rango tarifario invalido: min_participants supera max_participants.",
                    details={
                        "min_participants": tier.min_participants,
                        "max_participants": tier.max_participants,
                    },
                )
            if previous is not None:
                if tier.min_participants <= previous.max_participants:
                    raise ApiError(
                        status_code=400,
                        code=ErrorCode.EXPERIENCE_PRICING_TIERS_OVERLAP,
                        message="Los rangos tarifarios no pueden solaparse.",
                    )
                if (
                    pricing.require_contiguous_tiers
                    and tier.min_participants > previous.max_participants + 1
                ):
                    raise ApiError(
                        status_code=400,
                        code=ErrorCode.EXPERIENCE_PRICING_TIERS_GAP,
                        message="Los rangos tarifarios deben ser continuos sin saltos.",
                    )
            previous = tier

    def _validate_route_duration(self, duration: object | None) -> None:
        if duration is None:
            return
        activity_minutes = getattr(duration, "activity_minutes", None)
        route_minutes = getattr(duration, "route_minutes", None)
        if (
            isinstance(activity_minutes, int)
            and isinstance(route_minutes, int)
            and route_minutes > activity_minutes
        ):
            raise ApiError(
                status_code=400,
                code=ErrorCode.EXPERIENCE_ROUTE_DURATION_EXCEEDS_ACTIVITY_DURATION,
                message=(
                    "La duracion del recorrido no puede superar la duracion total de la actividad."
                ),
                details={
                    "activity_minutes": activity_minutes,
                    "route_minutes": route_minutes,
                },
            )

    def _validate_capacity_covered_by_tiers(
        self,
        *,
        standard_max_participants: int | None,
        pricing: ExperiencePricingSchema | None,
    ) -> None:
        if standard_max_participants is None or pricing is None or not pricing.tiers:
            return
        for tier in pricing.tiers:
            if tier.min_participants <= standard_max_participants <= tier.max_participants:
                return
        raise ApiError(
            status_code=400,
            code=ErrorCode.EXPERIENCE_STANDARD_CAPACITY_OUT_OF_PRICING_RANGE,
            message="La capacidad estandar debe estar cubierta por algun rango tarifario.",
            details={"standard_max_participants": standard_max_participants},
        )

    def _validate_inclusions(self, inclusions: object | None) -> None:
        if inclusions is None:
            return
        items = getattr(inclusions, "items", None)
        display_text = getattr(inclusions, "display_text", None)
        has_display_text = isinstance(display_text, str) and display_text.strip()
        if not isinstance(items, list):
            return
        if len(items) == 0 and not has_display_text:
            raise ApiError(
                status_code=400,
                code=ErrorCode.EXPERIENCE_INCLUSIONS_REQUIRED,
                message="La experiencia debe tener al menos un item incluido.",
            )

    def _validate_experience_payload(
        self, payload: ExperienceCreateSchema | ExperienceUpdateSchema
    ) -> None:
        self._validate_duration(
            duration_hours=payload.duration_hours,
            duration_days=payload.duration_days,
            duration=payload.duration,
        )
        self._validate_pricing(payload.pricing)
        self._validate_route_duration(payload.duration)
        standard_capacity = (
            payload.standard_max_participants
            if payload.standard_max_participants is not None
            else payload.base_capacity
        )
        self._validate_capacity_covered_by_tiers(
            standard_max_participants=standard_capacity,
            pricing=payload.pricing,
        )
        self._validate_inclusions(payload.inclusions)

    def _validate_document_state(self, doc: ExperienceDocument) -> None:
        self._validate_duration(
            duration_hours=getattr(doc, "duration_hours", None),
            duration_days=getattr(doc, "duration_days", None),
            duration=getattr(doc, "duration", None),
        )
        pricing = getattr(doc, "pricing", None)
        if isinstance(pricing, ExperiencePricingSchema):
            pricing_value = pricing
        else:
            pricing_value = None
            if pricing is not None:
                try:
                    pricing_value = ExperiencePricingSchema.model_validate(pricing)
                except Exception:
                    pricing_value = None
        self._validate_pricing(pricing_value)
        self._validate_route_duration(getattr(doc, "duration", None))
        standard_capacity = getattr(doc, "standard_max_participants", None)
        if standard_capacity is None:
            standard_capacity = getattr(doc, "base_capacity", None)
        self._validate_capacity_covered_by_tiers(
            standard_max_participants=standard_capacity,
            pricing=pricing_value,
        )
        self._validate_inclusions(getattr(doc, "inclusions", None))

    async def create(self, payload: ExperienceCreateSchema) -> ExperienceDocument:
        self._validate_experience_payload(payload)
        doc = ExperienceDocument(**payload.model_dump())
        try:
            if doc.standard_max_participants is None:
                doc.standard_max_participants = doc.base_capacity
        except AttributeError:
            pass
        try:
            if doc.min_participants is None:
                doc.min_participants = 1
        except AttributeError:
            pass
        try:
            await doc.insert()
        except DuplicateKeyError as exc:
            self._raise_conflict_from_duplicate(exc)
        await record_change(entity_type="experience", doc=doc)
        return doc

    async def list(
        self,
        is_active: bool | None = None,
        limit: int = 200,
        skip: int = 0,
    ) -> list[ExperienceDocument]:
        if is_active is None:
            return await ExperienceDocument.find_all().skip(skip).limit(limit).to_list()
        return await ExperienceDocument.find({"is_active": is_active}).skip(skip).limit(limit).to_list()

    async def count(self, is_active: bool | None = None) -> int:
        if is_active is None:
            return await ExperienceDocument.find_all().count()
        return await ExperienceDocument.find({"is_active": is_active}).count()

    async def get(self, experience_id: str) -> ExperienceDocument:
        doc = await ExperienceDocument.get(experience_id)
        if doc is None:
            raise ApiError(
                status_code=404,
                code=ErrorCode.EXPERIENCE_NOT_FOUND,
                message="Experiencia no encontrada.",
            )
        return doc

    async def update(
        self,
        experience_id: str,
        payload: ExperienceUpdateSchema,
    ) -> ExperienceDocument:
        doc = await self.get(experience_id)
        updates = payload.model_dump(exclude_none=True)
        for field, value in updates.items():
            setattr(doc, field, value)

        self._validate_document_state(doc)
        try:
            if doc.standard_max_participants is None:
                doc.standard_max_participants = doc.base_capacity
        except AttributeError:
            pass
        try:
            if doc.min_participants is None:
                doc.min_participants = 1
        except AttributeError:
            pass
        try:
            await doc.save()
        except DuplicateKeyError as exc:
            self._raise_conflict_from_duplicate(exc)
        await record_change(entity_type="experience", doc=doc)
        return doc

    async def deactivate(self, experience_id: str) -> ExperienceDocument:
        doc = await self.get(experience_id)
        doc.is_active = False
        await doc.save()
        await record_change(entity_type="experience", doc=doc, change_type="delete")
        return doc

    async def purge(self, experience_id: str) -> ExperienceDocument:
        """Elimina definitivamente una experiencia inactiva.

        Requiere desactivación previa y falla si hay reservas asociadas.
        """
        doc = await self.get(experience_id)
        if doc.is_active:
            raise ApiError(
                status_code=409,
                code=ErrorCode.EXPERIENCE_STILL_ACTIVE,
                message=(
                    "La experiencia debe estar desactivada antes de "
                    "eliminarla definitivamente."
                ),
                details={"experience_id": experience_id},
            )

        reservation_count = await ReservationDocument.find(
            {"experience_id": doc.id}
        ).count()
        if reservation_count > 0:
            raise ApiError(
                status_code=409,
                code=ErrorCode.EXPERIENCE_HAS_RESERVATIONS,
                message=(
                    "No se puede eliminar la experiencia porque tiene "
                    "reservas asociadas."
                ),
                details={
                    "experience_id": experience_id,
                    "reservation_count": reservation_count,
                },
            )

        await record_change(entity_type="experience", doc=doc, change_type="purge")
        await doc.delete()
        return doc

    async def quote(
        self,
        experience_id: str | PydanticObjectId,
        payload: ExperienceQuoteRequestSchema,
    ) -> ExperienceQuoteResponseSchema:
        try:
            object_id = (
                experience_id
                if isinstance(experience_id, PydanticObjectId)
                else PydanticObjectId(str(experience_id))
            )
        except Exception:
            raise ApiError(
                status_code=422,
                code=ErrorCode.VALIDATION_ERROR,
                message="El formato del ID de experiencia no es valido.",
            ) from None

        experience = await ExperienceDocument.get(object_id)

        if experience is None:
            raise ApiError(
                status_code=404,
                code=ErrorCode.EXPERIENCE_NOT_FOUND,
                message="La experiencia solicitada no existe.",
            )

        if experience.is_active is False:
            raise ApiError(
                status_code=409,
                code=ErrorCode.EXPERIENCE_INACTIVE,
                message="La experiencia esta inactiva y no puede cotizarse.",
            )

        pricing = experience.pricing
        if pricing is None or not pricing.tiers:
            raise ApiError(
                status_code=400,
                code=ErrorCode.EXPERIENCE_PRICING_MISSING,
                message="Esta experiencia no tiene tarifas configuradas.",
            )

        participant_count = payload.participant_count
        matching_tier = None

        for tier in pricing.tiers:
            if tier.min_participants <= participant_count <= tier.max_participants:
                matching_tier = tier
                break

        if matching_tier is None:
            raise ApiError(
                status_code=409,
                code=ErrorCode.EXPERIENCE_PRICING_TIER_NOT_FOUND,
                message=f"No hay una tarifa disponible para {participant_count} participantes.",
            )

        unit_price = matching_tier.price_per_person
        subtotal = unit_price * participant_count
        currency = pricing.currency

        notes_parts = []
        if pricing.pricing_notes:
            notes_parts.append(pricing.pricing_notes)
        notes = " | ".join(notes_parts) if notes_parts else None

        return ExperienceQuoteResponseSchema(
            experience_id=str(experience.id),
            participant_count=participant_count,
            unit_price=unit_price,
            subtotal=subtotal,
            currency=currency,
            pricing_tier=ExperiencePricingTierSchema(
                min_participants=matching_tier.min_participants,
                max_participants=matching_tier.max_participants,
                price_per_person=unit_price,
            ),
            notes=notes,
        )
