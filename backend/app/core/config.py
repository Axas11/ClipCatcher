"""Configuracion de la aplicacion cargada desde el archivo `.env`."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Variables de entorno tipadas del backend de ClipCatcher."""

    app_secret_key: str
    database_url: str = "sqlite:///./data/clipcatcher.db"
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440
    storage_path: str = "./data/storage"
    max_upload_bytes: int = 2_147_483_648

    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Devuelve una instancia cacheada de `Settings` para inyeccion."""
    return Settings()
