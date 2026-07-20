from dataclasses import dataclass
from datetime import UTC, datetime

from app.core.config import settings
from app.core.logging import logger
from app.documents.whatsapp_integration_document import WhatsAppIntegrationDocument

INACTIVE_STATUSES = {"revoked", "disconnected"}


@dataclass(frozen=True)
class WhatsAppSendCredentials:
    integration_id: str
    phone_number_id: str
    access_token: str
    api_version: str


class WhatsAppIntegrationService:
    """Resuelve y administra los números de WhatsApp conectados.

    Es el punto único que sabe traducir un `phone_number_id` (el número de
    *negocio* que recibió/enviará el mensaje) a credenciales de envío y a un
    registro trazable. Antes de que exista Embedded Signup configurado en
    Meta, se auto-crea (bootstrap) una integración "legacy" a partir de
    `settings.whatsapp_phone_number_id`, para que el número actual de La
    Juana siga funcionando exactamente igual que hoy. Cuando se conecte un
    número nuevo vía Embedded Signup, basta con crear otro
    `WhatsAppIntegrationDocument` — no se requiere tocar código.
    """

    async def resolve_by_phone_number_id(
        self, phone_number_id: str | None
    ) -> WhatsAppIntegrationDocument | None:
        if not phone_number_id:
            return await self.resolve_default()

        integration = await WhatsAppIntegrationDocument.find_one(
            {"phone_number_id": phone_number_id, "deleted_at": None}
        )
        if integration:
            return integration

        if (
            settings.whatsapp_phone_number_id
            and phone_number_id == settings.whatsapp_phone_number_id
        ):
            return await self._bootstrap_legacy_integration()

        return None

    async def resolve_default(self) -> WhatsAppIntegrationDocument | None:
        integration = await WhatsAppIntegrationDocument.find_one(
            {"is_default": True, "deleted_at": None}
        )
        if integration:
            return integration
        if settings.whatsapp_phone_number_id:
            return await self._bootstrap_legacy_integration()
        return None

    async def resolve_by_id(self, integration_id: str | None) -> WhatsAppIntegrationDocument | None:
        if not integration_id:
            return None
        return await WhatsAppIntegrationDocument.get(integration_id)

    async def _bootstrap_legacy_integration(self) -> WhatsAppIntegrationDocument:
        phone_number_id = settings.whatsapp_phone_number_id
        existing = await WhatsAppIntegrationDocument.find_one(
            {"phone_number_id": phone_number_id}
        )
        if existing:
            return existing

        integration = WhatsAppIntegrationDocument(
            phone_number_id=phone_number_id,
            display_phone_number=phone_number_id,
            connection_mode="cloud_api",
            status="active",
            is_default=True,
            is_enabled=True,
            webhook_subscribed=True,
            connected_at=datetime.now(UTC),
        )
        await integration.insert()
        logger.info(
            "[whatsapp_integration] Bootstrapped legacy integration from settings | "
            "phone_number_id=%s",
            phone_number_id,
        )
        return integration

    def is_usable(self, integration: WhatsAppIntegrationDocument | None) -> bool:
        if integration is None:
            return False
        return integration.is_enabled and integration.status not in INACTIVE_STATUSES

    def get_send_credentials(
        self, integration: WhatsAppIntegrationDocument
    ) -> WhatsAppSendCredentials:
        return WhatsAppSendCredentials(
            integration_id=str(integration.id),
            phone_number_id=integration.phone_number_id,
            access_token=integration.access_token or settings.whatsapp_access_token,
            api_version=integration.api_version or settings.whatsapp_api_version,
        )

    async def mark_degraded(self, integration_id: str | None, error: str) -> None:
        if not integration_id:
            return
        integration = await WhatsAppIntegrationDocument.get(integration_id)
        if not integration:
            return
        integration.status = "degraded"
        integration.last_error_message = error[:500]
        integration.updated_at = datetime.now(UTC)
        await integration.save()
        logger.warning(
            "[whatsapp_integration] Marked degraded | integration_id=%s | error=%s",
            integration_id,
            error,
        )

    # ── Administración (Embedded Signup / panel) ──

    async def list_integrations(self) -> list[WhatsAppIntegrationDocument]:
        return await WhatsAppIntegrationDocument.find({"deleted_at": None}).to_list()

    async def register_integration(
        self,
        *,
        phone_number_id: str,
        waba_id: str | None = None,
        business_id: str | None = None,
        display_phone_number: str | None = None,
        verified_name: str | None = None,
        connection_mode: str = "coexistence",
        access_token: str | None = None,
        api_version: str | None = None,
        is_default: bool = False,
        connected_by_user_id: str | None = None,
    ) -> WhatsAppIntegrationDocument:
        existing = await WhatsAppIntegrationDocument.find_one(
            {"phone_number_id": phone_number_id}
        )
        if existing:
            raise ValueError(f"phone_number_id already registered: {phone_number_id}")

        if is_default:
            await self._clear_default()

        integration = WhatsAppIntegrationDocument(
            phone_number_id=phone_number_id,
            waba_id=waba_id,
            business_id=business_id,
            display_phone_number=display_phone_number,
            verified_name=verified_name,
            connection_mode=connection_mode,
            status="active",
            is_default=is_default,
            is_enabled=True,
            access_token=access_token,
            api_version=api_version,
            coexistence_enabled=connection_mode == "coexistence",
            connected_by_user_id=connected_by_user_id,
            connected_at=datetime.now(UTC),
        )
        await integration.insert()
        logger.info(
            "[whatsapp_integration] Registered | phone_number_id=%s | mode=%s",
            phone_number_id,
            connection_mode,
        )
        return integration

    async def set_default(self, integration_id: str) -> WhatsAppIntegrationDocument:
        integration = await WhatsAppIntegrationDocument.get(integration_id)
        if not integration:
            raise ValueError(f"integration not found: {integration_id}")
        await self._clear_default()
        integration.is_default = True
        integration.updated_at = datetime.now(UTC)
        await integration.save()
        return integration

    async def disconnect(self, integration_id: str) -> WhatsAppIntegrationDocument:
        integration = await WhatsAppIntegrationDocument.get(integration_id)
        if not integration:
            raise ValueError(f"integration not found: {integration_id}")
        integration.status = "disconnected"
        integration.is_enabled = False
        integration.is_default = False
        integration.updated_at = datetime.now(UTC)
        await integration.save()
        return integration

    async def _clear_default(self) -> None:
        current = await WhatsAppIntegrationDocument.find_one({"is_default": True})
        if current:
            current.is_default = False
            current.updated_at = datetime.now(UTC)
            await current.save()
