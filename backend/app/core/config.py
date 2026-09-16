from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    APP_NAME: str = "Superadmin API"
    ENV: str = "development"
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 8

    COOLIFY_API_URL: str
    COOLIFY_API_TOKEN: str
    COOLIFY_SERVER_UUID: str
    COOLIFY_PROJECT_ERP_UUID: str
    DOMINIO_BASE: str
    BOOTSTRAP_SECRET: str = "CAMBIAR_ESTO_EN_PRODUCCION"

    class Config:
        env_file = ".env"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()