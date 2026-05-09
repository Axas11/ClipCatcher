"""Schemas Pydantic relacionados con usuarios y autenticacion."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    """Datos requeridos para registrar un nuevo usuario."""

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    name: str = Field(min_length=1, max_length=120)


class UserOut(BaseModel):
    """Datos publicos de un usuario (sin contraseña)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    name: str
    created_at: datetime
    # Provider de autenticacion: "email" o "google". El frontend lo usa
    # para decidir si mostrar el form de cambio de password (solo email)
    # o el badge "vinculada a Google" en /account.html.
    auth_provider: str


class Token(BaseModel):
    """Token JWT devuelto tras login o registro."""

    access_token: str
    token_type: str = "bearer"


class UserSettings(BaseModel):
    """Configuracion del detector personalizable por el usuario."""

    model_config = ConfigDict(from_attributes=True)

    chain_window_seconds: float = Field(ge=1.0, le=60.0)
    clip_margin_seconds: float = Field(ge=0.0, le=10.0)
    clip_duration_seconds: float = Field(ge=1.0, le=60.0)


class UserSettingsUpdate(BaseModel):
    """Actualizacion parcial (PATCH-like) de la configuracion del detector.

    Cada campo es opcional: solo se actualizan los enviados por el cliente.
    """

    chain_window_seconds: float | None = Field(default=None, ge=1.0, le=60.0)
    clip_margin_seconds: float | None = Field(default=None, ge=0.0, le=10.0)
    clip_duration_seconds: float | None = Field(default=None, ge=1.0, le=60.0)


class UserStats(BaseModel):
    """Estadisticas agregadas de uso del usuario actual (F9.4)."""

    videos_count: int
    clips_count: int
    avg_processing_seconds: float | None = None  # None si aun no hay videos done
