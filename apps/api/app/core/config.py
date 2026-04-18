from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "La Juana API"
    app_version: str = "0.1.0"
    app_env: str = "local"
    app_debug: bool = True

    api_prefix: str = "/api"
    api_version: str = "v1"

    mongodb_uri: str = "mongodb://localhost:27017"
    mongodb_db_name: str = "lajuana"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
