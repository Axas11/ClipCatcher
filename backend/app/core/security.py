"""Utilidades de seguridad: hashing de contraseñas y emision/lectura de JWT."""

from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import get_settings

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Genera el hash bcrypt de una contraseña en claro."""
    return _pwd_context.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    """Comprueba que una contraseña en claro coincide con su hash."""
    return _pwd_context.verify(password, hashed)


def create_access_token(subject: str | int, extra: dict[str, Any] | None = None) -> str:
    """Crea un JWT firmado con el secreto y algoritmo configurados."""
    settings = get_settings()
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": str(subject),
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=settings.jwt_expire_minutes)).timestamp()),
    }
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict[str, Any]:
    """Devuelve el payload del JWT si es valido. Lanza `JWTError` si no lo es."""
    settings = get_settings()
    return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])


__all__ = ["JWTError", "create_access_token", "decode_token", "hash_password", "verify_password"]
