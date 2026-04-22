from app.common.constants import DEFAULT_RESERVATION_MIN_DAYS
from app.common.labels import ErrorCode
from app.core.errors import ApiError
from app.documents import AppConfigDocument, ReservationRules
from app.schemas.config import ReservationRulesSchema, ReservationRulesUpdateSchema

RESERVATION_RULES_KEY = "reservation_rules"


class ConfigService:
    async def get_reservation_rules(self) -> ReservationRulesSchema:
        config = await AppConfigDocument.find_one(AppConfigDocument.key == RESERVATION_RULES_KEY)
        if config is None or config.reservation_rules is None:
            return ReservationRulesSchema(
                min_days_in_advance=DEFAULT_RESERVATION_MIN_DAYS,
                require_payment_proof_for_confirmation=True,
            )
        return ReservationRulesSchema.model_validate(config.reservation_rules.model_dump())

    async def update_reservation_rules(
        self, payload: ReservationRulesUpdateSchema
    ) -> ReservationRulesSchema:
        if (
            payload.min_days_in_advance is not None
            and payload.min_days_in_advance < 0
        ):
            raise ApiError(
                status_code=400,
                code=ErrorCode.CONFIG_INVALID_MIN_DAYS,
                message="min_days_in_advance no puede ser negativo.",
            )
        config = await AppConfigDocument.find_one(AppConfigDocument.key == RESERVATION_RULES_KEY)
        current = await self.get_reservation_rules()
        updated = current.model_copy(update=payload.model_dump(exclude_none=True))

        if config is None:
            config = AppConfigDocument(
                key=RESERVATION_RULES_KEY,
                reservation_rules=ReservationRules(**updated.model_dump()),
            )
            await config.insert()
            return updated

        config.reservation_rules = ReservationRules(**updated.model_dump())
        await config.save()
        return updated
