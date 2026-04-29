from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "La Juana API"
    app_version: str = "0.1.0"
    app_env: str = "local"
    app_debug: bool = True

    api_prefix: str = "/api"
    api_version: str = "v1"

    mongodb_uri: str = "mongodb://localhost:27017"
    mongodb_db_name: str = Field("lajuana", validation_alias="DATABASE_NAME")
    mongodb_connect_timeout_ms: int = 2000
    app_skip_db_init: bool = False

    auth_jwt_secret: str = "change-me"
    auth_jwt_algorithm: str = "HS256"
    auth_access_token_minutes: int = 30
    auth_refresh_token_days: int = 30

    storage_local_root: str = "./storage"
    storage_local_payment_proofs_prefix: str = "payment-proofs"

    chat_llm_model: str = "stub-extractor-v1"
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
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
