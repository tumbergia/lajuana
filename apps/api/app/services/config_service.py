from __future__ import annotations

from datetime import UTC, datetime

from beanie import PydanticObjectId

from app.config.emergency_contacts import EMERGENCY_CONTACTS
from app.core.errors import ApiError
from app.core.secret_crypto import encrypt_secret
from app.documents import (
    AiConfigurationConfig,
    AiRouteConfig,
    AppConfigDocument,
    BusinessLocationConfig,
    ConfigurationAuditDocument,
    PaymentInstructionsConfig,
    ReservationRules,
)
from app.schemas.config import (
    AiConfigurationSchema,
    AiConfigurationUpdateSchema,
    AiRouteSchema,
    BusinessLocationSchema,
    BusinessLocationUpdateSchema,
    ConfigurationSummarySchema,
    EmergencyCatalogContactSchema,
    EmergencyContactsResponseSchema,
    PaymentInstructionsSchema,
    PaymentInstructionsUpdateSchema,
    ReservationRulesSchema,
    ReservationRulesUpdateSchema,
)
from app.services.sync_change_recorder import record_change

RESERVATION_RULES_KEY = "reservation_rules"
PAYMENT_INSTRUCTIONS_KEY = "payment_instructions"
BUSINESS_LOCATION_KEY = "business_location"
AI_CONFIGURATION_KEY = "ai_configuration"


class ConfigService:
    async def get_emergency_contacts(self) -> EmergencyContactsResponseSchema:
        items = [EmergencyCatalogContactSchema.model_validate(item) for item in EMERGENCY_CONTACTS]
        return EmergencyContactsResponseSchema(items=items)

    async def get_reservation_rules(self) -> ReservationRulesSchema:
        config = await self.get_reservation_rules_document()
        rules = (
            config.reservation_rules if config and config.reservation_rules else ReservationRules()
        )
        return ReservationRulesSchema.model_validate(rules.model_dump())

    async def get_reservation_rules_document(self) -> AppConfigDocument | None:
        return await AppConfigDocument.find_one({"key": RESERVATION_RULES_KEY})

    async def update_reservation_rules_document(
        self,
        payload: ReservationRulesUpdateSchema,
        *,
        actor_id: PydanticObjectId | None = None,
    ) -> AppConfigDocument:
        current = await self.get_reservation_rules()
        updated = ReservationRulesSchema.model_validate(
            current.model_copy(update=payload.model_dump(exclude_none=True)).model_dump()
        )
        if updated.min_age > updated.max_age:
            raise ApiError(
                status_code=422,
                code="config.invalid_age_range",
                message="La edad mínima no puede superar la máxima.",
            )
        config = await self.get_reservation_rules_document()
        if config is None:
            config = AppConfigDocument(key=RESERVATION_RULES_KEY)
        config.reservation_rules = ReservationRules(**updated.model_dump())
        await self._persist(config)
        await record_change(entity_type="reservation_rules", doc=config)
        await self._audit(
            actor_id,
            "reservation_rules",
            list(payload.model_dump(exclude_none=True)),
            config.version,
        )
        return config

    async def update_reservation_rules(
        self,
        payload: ReservationRulesUpdateSchema,
        *,
        actor_id: PydanticObjectId | None = None,
    ) -> ReservationRulesSchema:
        doc = await self.update_reservation_rules_document(payload, actor_id=actor_id)
        return ReservationRulesSchema.model_validate(doc.reservation_rules.model_dump())

    async def get_payment_instructions_document(self) -> AppConfigDocument | None:
        return await AppConfigDocument.find_one({"key": PAYMENT_INSTRUCTIONS_KEY})

    async def get_payment_instructions(self) -> PaymentInstructionsSchema:
        config = await self.get_payment_instructions_document()
        value = (
            config.payment_instructions
            if config and config.payment_instructions
            else PaymentInstructionsConfig()
        )
        return PaymentInstructionsSchema.model_validate(value.model_dump())

    async def update_payment_instructions(
        self,
        payload: PaymentInstructionsUpdateSchema,
        *,
        actor_id: PydanticObjectId | None = None,
    ) -> PaymentInstructionsSchema:
        config = await self.get_payment_instructions_document()
        if config is None:
            config = AppConfigDocument(key=PAYMENT_INSTRUCTIONS_KEY)
        current = (
            config.payment_instructions
            if config.payment_instructions is not None
            else PaymentInstructionsConfig()
        )
        updates = payload.model_dump(
            mode="json",
            include=payload.model_fields_set,
        )
        data = current.model_dump(mode="json") | updates
        if not data["manual_transfer_enabled"] and not data["bold_enabled"]:
            raise ApiError(
                status_code=422,
                code="config.payment_method_required",
                message="Debe existir al menos un método de pago activo.",
            )
        if data["bold_enabled"] and not data["bold_checkout_url"]:
            raise ApiError(
                status_code=422,
                code="config.bold_url_required",
                message="El enlace Bold es obligatorio cuando Bold está activo.",
            )
        config.payment_instructions = PaymentInstructionsConfig(**data)
        await self._persist(config)
        await self._audit(actor_id, "payment_instructions", list(updates), config.version)
        return PaymentInstructionsSchema.model_validate(config.payment_instructions.model_dump())

    async def get_business_location_document(self) -> AppConfigDocument | None:
        return await AppConfigDocument.find_one({"key": BUSINESS_LOCATION_KEY})

    @staticmethod
    def google_maps_url(latitude: float, longitude: float) -> str:
        return f"https://maps.google.com/?q={latitude:.6f},{longitude:.6f}"

    async def get_business_location(self) -> BusinessLocationSchema:
        config = await self.get_business_location_document()
        value = (
            config.business_location
            if config and config.business_location
            else BusinessLocationConfig()
        )
        return BusinessLocationSchema(
            **value.model_dump(),
            google_maps_url=self.google_maps_url(value.latitude, value.longitude),
        )

    async def update_business_location(
        self,
        payload: BusinessLocationUpdateSchema,
        *,
        actor_id: PydanticObjectId | None = None,
    ) -> BusinessLocationSchema:
        config = await self.get_business_location_document()
        if config is None:
            config = AppConfigDocument(key=BUSINESS_LOCATION_KEY)
        current = (
            config.business_location
            if config.business_location is not None
            else BusinessLocationConfig()
        )
        updates = payload.model_dump(include=payload.model_fields_set)
        data = current.model_dump() | updates
        config.business_location = BusinessLocationConfig(**data)
        await self._persist(config)
        await self._audit(actor_id, "business_location", list(updates), config.version)
        return await self.get_business_location()

    async def get_ai_configuration_document(self) -> AppConfigDocument | None:
        return await AppConfigDocument.find_one({"key": AI_CONFIGURATION_KEY})

    async def get_ai_configuration(self) -> AiConfigurationSchema:
        from app.core.config import settings

        config = await self.get_ai_configuration_document()
        if config and config.ai_configuration:
            ai = config.ai_configuration
            return AiConfigurationSchema(
                enabled=ai.enabled,
                source="database",
                routes=[
                    AiRouteSchema(
                        position=r.position,
                        service=r.service,
                        model=r.model,
                        credential_configured=bool(r.encrypted_api_key),
                    )
                    for r in sorted(ai.routes, key=lambda item: item.position)
                ],
                version=config.version,
                updated_at=config.updated_at,
            )
        if settings.gemini_api_key:
            return AiConfigurationSchema(
                enabled=True,
                source="legacy_env",
                routes=[
                    AiRouteSchema(
                        position=1,
                        service="gemini",
                        model=settings.gemini_model,
                        credential_configured=True,
                    ),
                    AiRouteSchema(position=2),
                    AiRouteSchema(position=3),
                ],
            )
        return AiConfigurationSchema(
            enabled=False,
            source="unconfigured",
            routes=[AiRouteSchema(position=i) for i in range(1, 4)],
        )

    async def update_ai_configuration(
        self,
        payload: AiConfigurationUpdateSchema,
        *,
        actor_id: PydanticObjectId | None = None,
    ) -> AiConfigurationSchema:
        config = await self.get_ai_configuration_document()
        if config is None:
            config = AppConfigDocument(key=AI_CONFIGURATION_KEY)
        if (
            payload.expected_version is not None
            and getattr(config, "id", None) is not None
            and config.version != payload.expected_version
        ):
            raise ApiError(
                status_code=409,
                code="config.version_conflict",
                message="La configuración cambió en otro dispositivo.",
            )
        existing = {
            r.position: r
            for r in (config.ai_configuration.routes if config.ai_configuration else [])
        }
        routes: list[AiRouteConfig] = []
        for incoming in sorted(payload.routes, key=lambda item: item.position):
            encrypted = (
                existing.get(incoming.position).encrypted_api_key
                if existing.get(incoming.position)
                else None
            )
            if incoming.clear_api_key:
                encrypted = None
            if incoming.api_key is not None and incoming.api_key.get_secret_value():
                encrypted = encrypt_secret(incoming.api_key.get_secret_value())
            routes.append(
                AiRouteConfig(
                    position=incoming.position,
                    service=incoming.service,
                    model=(incoming.model or "").strip() or None,
                    encrypted_api_key=encrypted,
                )
            )
        if payload.enabled and any(
            not (r.service and r.model and r.encrypted_api_key) for r in routes
        ):
            raise ApiError(
                status_code=422,
                code="config.ai_incomplete",
                message="Las tres rutas requieren servicio, modelo y clave.",
            )
        config.ai_configuration = AiConfigurationConfig(enabled=payload.enabled, routes=routes)
        await self._persist(config)
        await self._audit(actor_id, "ai_configuration", ["enabled", "routes"], config.version)
        return await self.get_ai_configuration()

    async def get_summary(self) -> ConfigurationSummarySchema:
        ai = await self.get_ai_configuration()
        payment = await self.get_payment_instructions()
        enabled = []
        if payment.manual_transfer_enabled:
            enabled.append("manual_transfer")
        if payment.bold_enabled:
            enabled.append("bold")
        return ConfigurationSummarySchema(
            reservation_rules_configured=await self.get_reservation_rules_document() is not None,
            ai_enabled=ai.enabled,
            ai_source=ai.source,
            payment_methods_enabled=enabled,
            location_configured=await self.get_business_location_document() is not None,
        )

    async def _persist(self, config: AppConfigDocument) -> None:
        config.version = (getattr(config, "version", 1) or 1) + (
            1 if getattr(config, "id", None) is not None else 0
        )
        config.updated_at = datetime.now(UTC)
        if getattr(config, "id", None) is None:
            await config.insert()
        else:
            await config.save()

    async def _audit(
        self,
        actor_id: PydanticObjectId | None,
        section: str,
        changed_fields: list[str],
        version: int,
    ) -> None:
        if actor_id is None:
            return
        await ConfigurationAuditDocument(
            actor_user_id=actor_id,
            section=section,
            changed_fields=changed_fields,
            config_version=version,
        ).insert()
