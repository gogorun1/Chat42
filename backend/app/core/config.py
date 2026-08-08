from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Chat 42 API"
    cors_origins: list[str] = ["https://localhost"]
    database_url: str = "postgresql+asyncpg://chat42:changeme@postgres:5432/chat42"

    jwt_secret_key: str = "dev-secret-change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7  # 7 days

    ft_client_id: str = ""
    ft_client_secret: str = ""
    ft_redirect_uri: str = "https://localhost/auth/42/callback"

    frontend_url: str = "https://localhost"

    upload_dir: str = "/app/uploads"
    cat_detection_model: str = "google/owlvit-base-patch32"
    cat_detection_threshold: float = 0.15


@lru_cache
def get_settings() -> Settings:
    return Settings()
