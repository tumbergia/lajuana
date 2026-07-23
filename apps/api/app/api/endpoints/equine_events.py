"""Router de eventos de cuidado/seguimiento del equino (RF14)."""

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status

from app.api.deps import get_equine_event_service, require_permissions
from app.api.docs import ENDPOINT_DOCS, endpoint_description, endpoint_responses
from app.common.enums import Permission
from app.documents import UserDocument
from app.documents.equine_event_document import EquineEventType
from app.schemas.equine_event import (
    EquineEventCreateSchema,
    EquineEventListFilters,
    EquineEventResponseSchema,
    EquineEventSeverity,
    EquineEventUpdateSchema,
)
from app.services.equine_event_service import EquineEventService
from app.services.mappers import equine_event_to_response

nested_router = APIRouter(tags=["Eventos equino"])
flat_router = APIRouter(prefix="/equine-events", tags=["Eventos equino"])


@nested_router.post(
    "/{equine_id}/events",
    response_model=EquineEventResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary=ENDPOINT_DOCS["equine_events_create"]["summary"],
    description=endpoint_description("equine_events_create"),
    operation_id="createEquineEvent",
    responses=endpoint_responses("equine_events_create"),
)
async def create_equine_event(
    equine_id: str,
    payload: EquineEventCreateSchema,
    _: Annotated[UserDocument, Depends(require_permissions(Permission.EQUINE_UPDATE))],
    service: EquineEventService = Depends(get_equine_event_service),
) -> EquineEventResponseSchema:
    return equine_event_to_response(
        await service.create_for_equine(equine_id, payload),
    )


@nested_router.get(
    "/{equine_id}/events",
    response_model=list[EquineEventResponseSchema],
    summary=ENDPOINT_DOCS["equine_events_list"]["summary"],
    description=endpoint_description("equine_events_list"),
    operation_id="listEquineEvents",
    responses=endpoint_responses("equine_events_list"),
)
async def list_equine_events(
    equine_id: str,
    _: Annotated[UserDocument, Depends(require_permissions(Permission.EQUINE_READ))],
    response: Response,
    event_type: EquineEventType | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    severity: EquineEventSeverity | None = None,
    reservation_id: str | None = None,
    affects_availability: bool | None = None,
    limit: int = Query(default=50, ge=1, le=500),
    service: EquineEventService = Depends(get_equine_event_service),
) -> list[EquineEventResponseSchema]:
    filters = EquineEventListFilters(
        event_type=event_type,
        date_from=date_from,
        date_to=date_to,
        severity=severity,
        reservation_id=reservation_id,
        affects_availability=affects_availability,
        limit=limit,
    )
    response.headers["X-Total-Count"] = str(
        await service.count_for_equine(equine_id, filters),
    )
    return [
        equine_event_to_response(item) for item in await service.list_for_equine(equine_id, filters)
    ]


@flat_router.get(
    "/{event_id}",
    response_model=EquineEventResponseSchema,
    summary=ENDPOINT_DOCS["equine_events_get"]["summary"],
    description=endpoint_description("equine_events_get"),
    operation_id="getEquineEventById",
    responses=endpoint_responses("equine_events_get"),
)
async def get_equine_event(
    event_id: str,
    _: Annotated[UserDocument, Depends(require_permissions(Permission.EQUINE_READ))],
    service: EquineEventService = Depends(get_equine_event_service),
) -> EquineEventResponseSchema:
    return equine_event_to_response(await service.get(event_id))


@flat_router.patch(
    "/{event_id}",
    response_model=EquineEventResponseSchema,
    summary=ENDPOINT_DOCS["equine_events_update"]["summary"],
    description=endpoint_description("equine_events_update"),
    operation_id="updateEquineEventById",
    responses=endpoint_responses("equine_events_update"),
)
async def update_equine_event(
    event_id: str,
    payload: EquineEventUpdateSchema,
    _: Annotated[UserDocument, Depends(require_permissions(Permission.EQUINE_UPDATE))],
    service: EquineEventService = Depends(get_equine_event_service),
) -> EquineEventResponseSchema:
    return equine_event_to_response(await service.update(event_id, payload))


@flat_router.delete(
    "/{event_id}",
    response_model=EquineEventResponseSchema,
    summary=ENDPOINT_DOCS["equine_events_delete"]["summary"],
    description=endpoint_description("equine_events_delete"),
    operation_id="deleteEquineEvent",
    responses=endpoint_responses("equine_events_delete"),
)
async def delete_equine_event(
    event_id: str,
    _: Annotated[UserDocument, Depends(require_permissions(Permission.EQUINE_DELETE))],
    service: EquineEventService = Depends(get_equine_event_service),
) -> EquineEventResponseSchema:
    return equine_event_to_response(await service.soft_delete(event_id))
