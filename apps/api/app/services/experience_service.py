from __future__ import annotations

from beanie import PydanticObjectId
from pymongo.errors import DuplicateKeyError

from app.common.labels import ErrorCode
from app.core.errors import ApiError
from app.documents import ExperienceDocument
from app.documents.schedule_document import ScheduleDocument
from app.schemas.experience import (
    ExperienceCreateSchema,
    ExperiencePricingSchema,
    ExperiencePricingTierSchema,
    ExperienceQuoteRequestSchema,
    ExperienceQuoteResponseSchema,
    ExperienceUpdateSchema,
)


class ExperienceService:
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
        if not isinstance(items, list) or len(items) == 0:
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
        return doc

    async def list(self, is_active: bool | None = None) -> list[ExperienceDocument]:
        if is_active is None:
            return await ExperienceDocument.find_all().to_list()
        return await ExperienceDocument.find(ExperienceDocument.is_active == is_active).to_list()

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
        return doc

    async def deactivate(self, experience_id: str) -> ExperienceDocument:
        doc = await self.get(experience_id)
        doc.is_active = False
        await doc.save()
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
            )

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

        if payload.schedule_id:
            schedule = await ScheduleDocument.get(PydanticObjectId(payload.schedule_id))
            if schedule is None:
                raise ApiError(
                    status_code=404,
                    code=ErrorCode.SCHEDULE_NOT_FOUND,
                    message="El horario especificado no existe.",
                )
            if schedule.experience_id != object_id:
                raise ApiError(
                    status_code=409,
                    code=ErrorCode.SCHEDULE_EXPERIENCE_MISMATCH,
                    message="El horario no corresponde a esta experiencia.",
                )

        pricing = experience.pricing
        if pricing is None or not pricing.tiers:
            raise ApiError(
                status_code=400,
                code=ErrorCode.EXPERIENCE_PRICING_MISSING,
                message="Esta experiencia no tiene tarifas configuradas.",
            )

        participants_count = payload.participants_count
        matching_tier = None

        for tier in pricing.tiers:
            if tier.min_participants <= participants_count <= tier.max_participants:
                matching_tier = tier
                break

        if matching_tier is None:
            raise ApiError(
                status_code=409,
                code=ErrorCode.EXPERIENCE_PRICING_TIER_NOT_FOUND,
                message=f"No hay una tarifa disponible para {participants_count} participantes.",
            )

        unit_price = matching_tier.price_per_person
        subtotal = unit_price * participants_count
        currency = pricing.currency

        notes_parts = []
        if pricing.pricing_notes:
            notes_parts.append(pricing.pricing_notes)
        if payload.special_conditions:
            notes_parts.append("Condiciones especiales: " + ", ".join(payload.special_conditions))
        notes = " | ".join(notes_parts) if notes_parts else None

        return ExperienceQuoteResponseSchema(
            experience_id=str(experience.id),
            participants_count=participants_count,
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
