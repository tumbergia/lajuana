from pydantic import AliasChoices, Field
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

    mongodb_uri: str = Field("mongodb://localhost:27017", validation_alias="MONGODB_URI")
    mongodb_db_name: str = Field("lajuana", validation_alias="DATABASE_NAME")
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

    chat_llm_model: str = "stub-extractor-v1"
    chat_llm_provider: str = Field("groq", validation_alias="LLM_PROVIDER")
    chat_llm_base_url: str = Field(
        "https://api.groq.com/openai/v1",
        validation_alias=AliasChoices("LJ_LLM_BASE_URL", "LLM_BASE_URL"),
    )
    chat_llm_model_name: str = Field(
        "llama-3.3-70b-versatile", validation_alias=AliasChoices("LJ_LLM_MODEL", "LLM_MODEL")
    )
    chat_llm_api_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices(
            "LJ_LLM_API_KEY",
            "LLM_API_KEY",
            "GROQ_API_KEY",
            "OPENAI_API_KEY",
        ),
    )
    chat_enable_rag: bool = True
    chat_enable_booking: bool = True
    chat_vector_top_k: int = 3
    chat_vector_index_name: str = "vector_index"
    chat_embedding_model: str = "https://huggingface.co/mixedbread-ai/mxbai-embed-large-v1"
    chat_embedding_base_url: str = "http://127.0.0.1:1234/v1"
    chat_embedding_api_key: str = "lm-studio"
    chat_checkpoint_collection: str = "chat_checkpoints"
    chat_default_channel: str = "whatsapp"

    model_config = SettingsConfigDict(
        env_file=(".env", "apps/api/.env", "prueba-rag/.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
