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


class Token(BaseModel):
    """Token JWT devuelto tras login o registro."""

    access_token: str
    token_type: str = "bearer"
