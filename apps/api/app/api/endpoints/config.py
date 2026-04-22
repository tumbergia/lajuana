from fastapi import APIRouter

from app.schemas.config import ReservationRulesSchema, ReservationRulesUpdateSchema
from app.services import ConfigService

router = APIRouter(prefix="/config", tags=["config"])
service = ConfigService()


@router.get("/reservation-rules", response_model=ReservationRulesSchema)
async def get_reservation_rules() -> ReservationRulesSchema:
    return await service.get_reservation_rules()


@router.patch("/reservation-rules", response_model=ReservationRulesSchema)
async def update_reservation_rules(payload: ReservationRulesUpdateSchema) -> ReservationRulesSchema:
    return await service.update_reservation_rules(payload)
