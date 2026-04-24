from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "La Juana API"
    app_version: str = "0.1.0"
    app_env: str = "local"
    app_debug: bool = True
    cors_allowed_origins: str = "http://localhost:3000,http://localhost:5173,http://localhost:8080,http://127.0.0.1:3000,http://127.0.0.1:5173,http://127.0.0.1:8080"
    cors_allow_origin_regex: str = r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$"
    cors_allow_credentials: bool = False

    api_prefix: str = "/api"
    api_version: str = "v1"

    mongodb_uri: str = "mongodb://localhost:27017"
    mongodb_db_name: str = "lajuana"
    mongodb_connect_timeout_ms: int = 2000
    app_skip_db_init: bool = False

    auth_jwt_secret: str = "change-me"
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

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
