"""Dependencias FastAPI compartidas: autenticacion y acceso a sesion DB."""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.security import JWTError, decode_token
from app.db.session import get_db
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

_credentials_error = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Credenciales invalidas",
    headers={"WWW-Authenticate": "Bearer"},
)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Resuelve el usuario actual a partir del JWT del header Authorization."""
    try:
        payload = decode_token(token)
        subject = payload.get("sub")
        if subject is None:
            raise _credentials_error
        user_id = int(subject)
    except (JWTError, ValueError) as exc:
        raise _credentials_error from exc

    user = db.get(User, user_id)
    if user is None:
        raise _credentials_error
    return user
