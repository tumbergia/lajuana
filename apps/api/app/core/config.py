from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "La Juana API"
    app_version: str = "0.1.0"
    app_env: str = "local"
    app_debug: bool = True
    cors_allowed_origins: str = "http://localhost:3000,http://localhost:5173,http://localhost:8080,http://127.0.0.1:3000,http://127.0.0.1:5173,http://127.0.0.1:8080,https://formulario-la-juana.vercel.app"
    cors_allow_origin_regex: str = r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$"
    cors_allow_credentials: bool = False

    api_prefix: str = "/api"
    api_version: str = "v1"

    mongodb_uri: str = Field("mongodb://localhost:27017", validation_alias="MONGODB_URI")
    mongodb_db_name: str = Field("lajuana", validation_alias="DATABASE_NAME")
    mongodb_connect_timeout_ms: int = 2000
    app_skip_db_init: bool = False

    app_base_url: str = "http://localhost:8080"

    auth_jwt_secret: str = (
        "change-me"  # TODO: rotar a 32+ chars (invalida tokens existentes); ver ADR-JWT
    )
    auth_jwt_algorithm: str = "HS256"
    auth_access_token_minutes: int = 30
    auth_refresh_token_days: int = 30

    storage_local_root: str = "./storage"
    storage_local_payment_proofs_prefix: str = "payment-proofs"
    storage_s3_bucket: str = "lajuana-files"
    storage_s3_region: str = "us-east-1"
    storage_s3_endpoint_url: str | None = None
    storage_s3_access_key_id: str | None = None
    storage_s3_secret_access_key: str | None = None
    storage_s3_presign_expiration_seconds: int = 900

    chat_default_channel: str = "whatsapp"
    assistant_enable_llm: bool = False
    assistant_default_min_notice_days: int = 7
    llm_provider: str = "gemini"
    gemini_api_key: str = ""
    gemini_api_key_2: str = ""
    gemini_api_key_3: str = ""
    gemini_model: str = "gemini-2.5-flash"
    gemini_fallback_models: str = "gemini-3-flash,gemini-3.1-flash-lite,gemini-2.5-flash-lite"
    gemini_temperature: float = 0.2
    gemini_timeout_seconds: int = 60
    ai_config_encryption_key: str = ""

    assistant_min_plan_confidence: float = 0.55

    whisper_model_size: str = "base"
    whisper_device: str = "cpu"
    whisper_compute_type: str = "int8"

    whatsapp_verify_token: str = "change-me"
    whatsapp_app_secret: str = ""
    whatsapp_access_token: str = ""
    whatsapp_phone_number_id: str = ""
    whatsapp_api_version: str = "v23.0"
    whatsapp_send_enabled: bool = False

    participant_form_base_url: str = "https://formulario-la-juana.vercel.app"
    participant_form_token_expiry_days: int = 14
    participant_form_token_secret: str = "change-me"

    email_service: str = "gmail"
    email_host: str | None = None
    email_port: int | None = None
    email_user: str = ""
    email_pass: str = ""
    email_from_address: str = "noreply@lajuana.com"
    email_from_name: str = "La Juana"

    notification_outbox_poll_interval: int = 30
    notification_max_retries: int = 3
    notification_retry_delay_seconds: int = 300

    buffer_debounce_seconds: int = 10
    buffer_max_seconds: int = 30
    buffer_max_messages: int = 15
    # Lock TTL para un turno. Debe ser MAYOR que gemini_timeout_seconds para
    # que un turno largo legítimo no pierda el lock; el doble es seguro.
    buffer_lock_seconds: int = 90
    # Cualquier lock más viejo que esto se considera muerto y se libera solo.
    buffer_stale_lock_seconds: int = 300
    # Timeout duro para la llamada al orchestrator.ask: si el LLM cuelga
    # más allá de esto, el turno se aborta, el lock se libera y el bot
    # responde con un fallback. Protege contra LLMs atascados.
    orchestrator_turn_timeout_seconds: int = 75
    scheduler_loop_seconds: int = 1

    @model_validator(mode="after")
    def _validate_production_secrets(self) -> "Settings":
        if self.app_env in ("production", "prod", "staging"):
            if self.auth_jwt_secret in ("change-me", ""):
                raise ValueError("AUTH_JWT_SECRET must be set in production/staging environment")
            if self.whatsapp_verify_token in ("change-me", ""):
                raise ValueError(
                    "WHATSAPP_VERIFY_TOKEN must be set in production/staging environment"
                )
            if self.participant_form_token_secret in ("change-me", ""):
                raise ValueError(
                    "PARTICIPANT_FORM_TOKEN_SECRET must be set in production/staging environment"
                )
            if not self.ai_config_encryption_key:
                raise ValueError("AI_CONFIG_ENCRYPTION_KEY must be set in production/staging")
            if not self.whatsapp_app_secret:
                raise ValueError("WHATSAPP_APP_SECRET must be set in production/staging")
        return self

    model_config = SettingsConfigDict(
        env_file=(".env", "apps/api/.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
