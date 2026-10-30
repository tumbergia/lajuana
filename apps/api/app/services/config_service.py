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
    AiEnvProviderSchema,
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
        await self._notify_config_changed(
            section="Reglas de reserva",
            actor_id=actor_id,
            version=config.version,
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
        await self._notify_config_changed(
            section="Instrucciones de pago",
            actor_id=actor_id,
            version=config.version,
        )
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
        await self._notify_config_changed(
            section="Ubicación del negocio",
            actor_id=actor_id,
            version=config.version,
        )
        return await self.get_business_location()

    async def get_ai_configuration_document(self) -> AppConfigDocument | None:
        return await AppConfigDocument.find_one({"key": AI_CONFIGURATION_KEY})

    def _env_provider_schema(self) -> AiEnvProviderSchema:
        from app.core.config import settings

        keys = [
            settings.gemini_api_key,
            settings.gemini_api_key_2,
            settings.gemini_api_key_3,
        ]
        keys_configured = sum(1 for key in keys if (key or "").strip())
        fallbacks = [
            part.strip()
            for part in (settings.gemini_fallback_models or "").split(",")
            if part.strip()
        ]
        return AiEnvProviderSchema(
            available=bool((settings.gemini_api_key or "").strip()),
            provider="gemini",
            model=settings.gemini_model or None,
            fallback_models=fallbacks,
            keys_configured=keys_configured,
        )

    async def get_ai_configuration(self) -> AiConfigurationSchema:
        from app.core.config import settings

        env_provider = self._env_provider_schema()
        config = await self.get_ai_configuration_document()
        if config and config.ai_configuration:
            ai = config.ai_configuration
            return AiConfigurationSchema(
                enabled=ai.enabled,
                source="database",
                provider_mode=getattr(ai, "provider_mode", None) or "env",
                muted_phones=list(ai.muted_phones),
                routes=[
                    AiRouteSchema(
                        position=r.position,
                        service=r.service,
                        model=r.model,
                        credential_configured=bool(r.encrypted_api_key),
                    )
                    for r in sorted(ai.routes, key=lambda item: item.position)
                ],
                env_provider=env_provider,
                version=config.version,
                updated_at=config.updated_at,
            )
        if settings.gemini_api_key:
            return AiConfigurationSchema(
                enabled=True,
                source="legacy_env",
                provider_mode="env",
                muted_phones=[],
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
                env_provider=env_provider,
            )
        return AiConfigurationSchema(
            enabled=False,
            source="unconfigured",
            provider_mode="env",
            muted_phones=[],
            routes=[AiRouteSchema(position=i) for i in range(1, 4)],
            env_provider=env_provider,
        )

    async def update_ai_configuration(
        self,
        payload: AiConfigurationUpdateSchema,
        *,
        actor_id: PydanticObjectId | None = None,
    ) -> AiConfigurationSchema:
        from app.channels.whatsapp.normalizer import normalize_phone
        from app.core.config import settings

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
        existing_ai = config.ai_configuration
        existing = {r.position: r for r in (existing_ai.routes if existing_ai else [])}
        provider_mode = (
            payload.provider_mode or (existing_ai.provider_mode if existing_ai else None) or "env"
        )
        if payload.routes is None:
            routes = [existing.get(i) or AiRouteConfig(position=i) for i in range(1, 4)]
        else:
            routes = []
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
        if payload.enabled:
            if provider_mode == "env":
                if not (settings.gemini_api_key or "").strip():
                    raise ApiError(
                        status_code=422,
                        code="config.ai_env_unavailable",
                        message=(
                            "No hay GEMINI_API_KEY en el servidor. "
                            "Configura el entorno o usa modelos personalizados."
                        ),
                    )
            else:
                complete = [r for r in routes if r.service and r.model and r.encrypted_api_key]
                if not complete:
                    raise ApiError(
                        status_code=422,
                        code="config.ai_incomplete",
                        message=(
                            "Configura al menos un modelo con servicio, nombre y clave "
                            "para usar el modo personalizado."
                        ),
                    )
        muted: list[str] = []
        seen: set[str] = set()
        for raw in payload.muted_phones:
            try:
                phone = normalize_phone(raw)
            except ValueError:
                raise ApiError(
                    status_code=422,
                    code="config.invalid_muted_phone",
                    message=f"Número de teléfono inválido: {raw!r}",
                ) from None
            if phone not in seen:
                seen.add(phone)
                muted.append(phone)
        config.ai_configuration = AiConfigurationConfig(
            enabled=payload.enabled,
            provider_mode=provider_mode,
            muted_phones=muted,
            routes=routes,
        )
        await self._persist(config)
        await self._audit(
            actor_id,
            "ai_configuration",
            ["enabled", "provider_mode", "muted_phones", "routes"],
            config.version,
        )
        await self._notify_config_changed(
            section="Configuración de IA",
            actor_id=actor_id,
            version=config.version,
        )
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

    async def _notify_config_changed(
        self,
        *,
        section: str,
        actor_id: PydanticObjectId | None,
        version: int,
    ) -> None:
        try:
            from app.common.enums import NotificationEventType
            from app.core.di import Container
            from app.core.logging import logger
            from app.documents import UserDocument

            actor_name = "Alguien"
            if actor_id is not None:
                actor = await UserDocument.get(actor_id)
                if actor is not None:
                    actor_name = actor.full_name or actor.email or actor_name

            await Container.get_instance().notification_service.enqueue_admin_in_app(
                event_type=NotificationEventType.CONFIGURATION_CHANGED,
                title="Configuración actualizada",
                body=f"{actor_name} actualizó: {section}",
                actor_user_id=str(actor_id) if actor_id else None,
                dedup_suffix=f"{section}:{version}",
            )
        except Exception:
            from app.core.logging import logger

            logger.exception("[config] Failed to enqueue configuration_changed")
