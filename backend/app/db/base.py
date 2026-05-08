"""Clase base declarativa de SQLAlchemy compartida por todos los modelos."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base comun para los modelos del backend."""
