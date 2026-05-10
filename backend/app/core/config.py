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
    max_upload_bytes: int = 10_737_418_240

    # Google OAuth (F8). Todas opcionales: si `google_client_id` esta vacio,
    # el frontend oculta el boton y los endpoints /api/auth/google/* devuelven
    # 503. Asi se puede usar la app solo con email+password sin credenciales
    # de Google Cloud (degradacion elegante).
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://127.0.0.1:8001/api/auth/google/callback"
    frontend_url: str = "http://127.0.0.1:8001"

    # SMTP para password reset (F14). Si smtp_user / smtp_password
    # estan vacios, el envio de email se hace no-op con log error.
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 465
    smtp_user: str | None = None
    smtp_password: str | None = None

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
