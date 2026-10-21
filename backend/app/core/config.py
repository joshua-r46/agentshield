from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"

    database_url: str = (
        "postgresql+psycopg://agentshield:agentshield"
        "@localhost:5433/agentshield"
    )

    backend_url: str = "http://localhost:8000"
    frontend_url: str = "http://localhost:3000"

    openai_api_key: str = ""
    jwt_secret: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()