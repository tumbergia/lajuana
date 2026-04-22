from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.deps import require_permissions
from app.api.docs import COMMON_AUTH_RESPONSES
from app.common.enums import Permission
from app.documents import UserDocument
from app.schemas.config import ReservationRulesSchema, ReservationRulesUpdateSchema
from app.services import ConfigService

router = APIRouter(prefix="/config", tags=["Configuration"])
service = ConfigService()


@router.get(
    "/reservation-rules",
    response_model=ReservationRulesSchema,
    status_code=status.HTTP_200_OK,
    summary="Consultar reglas de reserva",
    description="Retorna configuración vigente de reglas de confirmación de reserva.",
    operation_id="getReservationRules",
    responses=COMMON_AUTH_RESPONSES,
)
async def get_reservation_rules(
    _: Annotated[UserDocument, Depends(require_permissions(Permission.CONFIG_READ))],
) -> ReservationRulesSchema:
    return await service.get_reservation_rules()


@router.patch(
    "/reservation-rules",
    response_model=ReservationRulesSchema,
    status_code=status.HTTP_200_OK,
    summary="Actualizar reglas de reserva",
    description="Actualiza parámetros sensibles de confirmación de reservas.",
    operation_id="updateReservationRules",
    responses=COMMON_AUTH_RESPONSES,
)
async def update_reservation_rules(
    payload: ReservationRulesUpdateSchema,
    _: Annotated[UserDocument, Depends(require_permissions(Permission.CONFIG_UPDATE))],
) -> ReservationRulesSchema:
    return await service.update_reservation_rules(payload)
