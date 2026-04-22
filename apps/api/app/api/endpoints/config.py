from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.deps import require_permissions
from app.api.docs import ENDPOINT_DOCS, endpoint_description, endpoint_responses
from app.common.enums import Permission
from app.documents import UserDocument
from app.schemas.config import (
    EmergencyContactsResponseSchema,
    ReservationRulesSchema,
    ReservationRulesUpdateSchema,
)
from app.services import ConfigService

router = APIRouter(prefix="/config", tags=["Configuracion"])
service = ConfigService()


@router.get(
    "/emergency-contacts",
    response_model=EmergencyContactsResponseSchema,
    status_code=status.HTTP_200_OK,
    summary=ENDPOINT_DOCS["config_emergency_contacts"]["summary"],
    description=endpoint_description("config_emergency_contacts"),
    operation_id="getEmergencyContacts",
    responses=endpoint_responses("config_emergency_contacts"),
)
async def get_emergency_contacts() -> EmergencyContactsResponseSchema:
    return await service.get_emergency_contacts()


@router.get(
    "/reservation-rules",
    response_model=ReservationRulesSchema,
    status_code=status.HTTP_200_OK,
    summary=ENDPOINT_DOCS["config_get"]["summary"],
    description=endpoint_description("config_get"),
    operation_id="getReservationRules",
    responses=endpoint_responses("config_get"),
)
async def get_reservation_rules(
    _: Annotated[UserDocument, Depends(require_permissions(Permission.CONFIG_READ))],
) -> ReservationRulesSchema:
    return await service.get_reservation_rules()


@router.patch(
    "/reservation-rules",
    response_model=ReservationRulesSchema,
    status_code=status.HTTP_200_OK,
    summary=ENDPOINT_DOCS["config_update"]["summary"],
    description=endpoint_description("config_update"),
    operation_id="updateReservationRules",
    responses=endpoint_responses("config_update"),
)
async def update_reservation_rules(
    payload: ReservationRulesUpdateSchema,
    _: Annotated[UserDocument, Depends(require_permissions(Permission.CONFIG_UPDATE))],
) -> ReservationRulesSchema:
    return await service.update_reservation_rules(payload)
