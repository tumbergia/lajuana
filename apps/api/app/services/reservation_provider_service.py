from __future__ import annotations

from beanie import PydanticObjectId

from app.common.labels import ErrorCode
from app.core.errors import ApiError
from app.documents import (
    ExperienceDocument,
    ProviderDocument,
    ReservationDocument,
    ReservationProviderDocument,
)
from app.documents.provider_document import ProviderStatus
from app.documents.reservation_provider_document import ReservationProviderStatus
from app.schemas.reservation_provider import (
    ReservationProviderCreateSchema,
    ReservationProviderTabItemSchema,
    ReservationProviderUpdateSchema,
)
from app.services.base_service import BaseService


def _normalize_service_label(value: str | None) -> str:
    return (value or "").strip()


class ReservationProviderService(
    BaseService[
        ReservationProviderDocument,
        ReservationProviderCreateSchema,
        ReservationProviderUpdateSchema,
    ]
):
    document_class = ReservationProviderDocument
    not_found_code = ErrorCode.RESERVATION_PROVIDER_NOT_FOUND
    not_found_message = "Asociación reserva-proveedor no encontrada."

    async def _get_reservation(self, reservation_id: str) -> ReservationDocument:
        reservation = await ReservationDocument.get(reservation_id)
        if reservation is None:
            raise ApiError(
                status_code=404,
                code=ErrorCode.RESERVATION_NOT_FOUND,
                message="Reserva no encontrada.",
            )
        return reservation

    async def _get_provider(self, provider_id: str) -> ProviderDocument:
        provider = await ProviderDocument.get(provider_id)
        if provider is None:
            raise ApiError(
                status_code=404,
                code=ErrorCode.PROVIDER_NOT_FOUND,
                message="Proveedor no encontrado.",
            )
        return provider

    def _ensure_provider_associable(self, provider: ProviderDocument) -> None:
        if not provider.is_active or provider.status in {
            ProviderStatus.INACTIVE,
            ProviderStatus.BLOCKED,
        }:
            raise ApiError(
                status_code=409,
                code=ErrorCode.PROVIDER_NOT_ASSOCIABLE,
                message="El proveedor no puede asociarse a la reserva en su estado actual.",
            )

    async def _ensure_not_duplicate(
        self,
        *,
        reservation_id: PydanticObjectId,
        provider_id: PydanticObjectId,
        service_label: str | None,
        exclude_id: PydanticObjectId | None = None,
    ) -> None:
        normalized = _normalize_service_label(service_label)
        query: dict[str, object] = {
            "reservation_id": reservation_id,
            "provider_id": provider_id,
            "deleted_at": None,
        }
        if normalized:
            query["service_label"] = normalized
        else:
            query["$or"] = [
                {"service_label": None},
                {"service_label": ""},
            ]

        existing = await ReservationProviderDocument.find_one(query)
        if existing is not None and (exclude_id is None or existing.id != exclude_id):
            raise ApiError(
                status_code=409,
                code=ErrorCode.RESERVATION_PROVIDER_DUPLICATE,
                message="El proveedor ya está asociado a esta reserva con el mismo servicio.",
            )

    async def _to_tab_item(
        self,
        link: ReservationProviderDocument,
        reservation: ReservationDocument,
        provider: ProviderDocument,
        experience_name: str | None,
    ) -> ReservationProviderTabItemSchema:
        return ReservationProviderTabItemSchema(
            reservation_provider_id=str(link.id),
            reservation_id=str(reservation.id),
            provider_id=str(provider.id),
            provider_name=provider.name,
            provider_type=provider.type,
            status=link.status,
            service_label=link.service_label,
            contact_name=provider.contact_name,
            email=provider.email,
            whatsapp_phone=provider.whatsapp_phone,
            location_label=provider.location_label,
            capacity_notes=provider.capacity_notes,
            operational_notes=provider.operational_notes,
            tariff_notes=provider.tariff_notes,
            notes=link.notes,
            reservation_code=reservation.code,
            experience_name=experience_name,
            scheduled_date=reservation.requested_date,
            participants_count=reservation.participant_count,
        )

    async def list_for_reservation(
        self,
        reservation_id: str,
    ) -> list[ReservationProviderTabItemSchema]:
        reservation = await self._get_reservation(reservation_id)
        experience_name: str | None = None
        experience = await ExperienceDocument.get(reservation.experience_id)
        if experience is not None:
            experience_name = experience.name

        links = await ReservationProviderDocument.find(
            {"reservation_id": reservation.id, "deleted_at": None}
        ).to_list()

        items: list[ReservationProviderTabItemSchema] = []
        for link in links:
            provider = await ProviderDocument.get(link.provider_id)
            if provider is None:
                continue
            items.append(
                await self._to_tab_item(link, reservation, provider, experience_name)
            )
        return items

    async def create_for_reservation(
        self,
        reservation_id: str,
        payload: ReservationProviderCreateSchema,
    ) -> ReservationProviderTabItemSchema:
        reservation = await self._get_reservation(reservation_id)
        provider = await self._get_provider(payload.provider_id)
        self._ensure_provider_associable(provider)
        await self._ensure_not_duplicate(
            reservation_id=reservation.id,
            provider_id=provider.id,
            service_label=payload.service_label,
        )

        doc = ReservationProviderDocument(
            reservation_id=reservation.id,
            provider_id=provider.id,
            service_label=_normalize_service_label(payload.service_label) or None,
            notes=payload.notes,
            status=payload.status,
        )
        await doc.insert()

        experience_name: str | None = None
        experience = await ExperienceDocument.get(reservation.experience_id)
        if experience is not None:
            experience_name = experience.name
        return await self._to_tab_item(doc, reservation, provider, experience_name)

    async def update_for_reservation(
        self,
        reservation_id: str,
        reservation_provider_id: str,
        payload: ReservationProviderUpdateSchema,
    ) -> ReservationProviderTabItemSchema:
        reservation = await self._get_reservation(reservation_id)
        link = await self.get(reservation_provider_id)
        if link.reservation_id != reservation.id:
            raise ApiError(
                status_code=404,
                code=self.not_found_code,
                message=self.not_found_message,
            )

        updates = payload.model_dump(exclude_none=True)
        if "service_label" in updates:
            updates["service_label"] = _normalize_service_label(updates["service_label"]) or None
            await self._ensure_not_duplicate(
                reservation_id=reservation.id,
                provider_id=link.provider_id,
                service_label=updates["service_label"],
                exclude_id=link.id,
            )

        for field, value in updates.items():
            setattr(link, field, value)
        await link.save()

        provider = await self._get_provider(str(link.provider_id))
        experience_name: str | None = None
        experience = await ExperienceDocument.get(reservation.experience_id)
        if experience is not None:
            experience_name = experience.name
        return await self._to_tab_item(link, reservation, provider, experience_name)

    async def delete_for_reservation(
        self,
        reservation_id: str,
        reservation_provider_id: str,
    ) -> None:
        reservation = await self._get_reservation(reservation_id)
        link = await self.get(reservation_provider_id)
        if link.reservation_id != reservation.id:
            raise ApiError(
                status_code=404,
                code=self.not_found_code,
                message=self.not_found_message,
            )
        await link.delete()
