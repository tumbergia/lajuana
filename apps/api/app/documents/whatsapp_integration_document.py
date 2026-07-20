from datetime import UTC, datetime

from beanie import Document
from pydantic import Field


class WhatsAppIntegrationDocument(Document):
    """Un número de WhatsApp conectado al backend (Cloud API o Coexistence).

    Reemplaza el supuesto anterior de un único número global en `settings`.
    Mientras no exista un gestor de secretos, `access_token`/`api_version`
    quedan opcionales: si no se configuran aquí, se usa el valor heredado de
    `settings.whatsapp_access_token` / `settings.whatsapp_api_version` — así
    el número histórico sigue funcionando sin requerir esta tabla poblada.
    """

    business_id: str | None = None
    waba_id: str | None = None
    phone_number_id: str
    display_phone_number: str | None = None
    verified_name: str | None = None

    connection_mode: str = "cloud_api"  # cloud_api | coexistence
    status: str = "active"  # pending | active | degraded | revoked | disconnected
    is_default: bool = False
    is_enabled: bool = True

    access_token: str | None = None
    api_version: str | None = None

    granted_permissions: list[str] = Field(default_factory=list)
    webhook_subscribed: bool = False
    coexistence_enabled: bool = False

    connected_by_user_id: str | None = None
    connected_at: datetime | None = None
    last_validated_at: datetime | None = None
    last_error_code: str | None = None
    last_error_message: str | None = None

    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    deleted_at: datetime | None = None

    class Settings:
        name = "whatsapp_integrations"
        indexes = [
            "phone_number_id",
            "waba_id",
            "status",
            "is_default",
        ]
