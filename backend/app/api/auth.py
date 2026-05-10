"""Endpoints de autenticacion: registro, login, password reset."""

import logging
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import create_access_token, hash_password, verify_password
from app.db.session import get_db
from app.models.password_reset_token import PasswordResetToken
from app.models.user import User
from app.schemas.user import Token, UserCreate, UserOut
from app.services.email_service import send_password_reset_email

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])

# TTL del token de reset. 1 hora es lo recomendado por OWASP para
# self-service password reset (corto pero suficiente para que el
# usuario abra el email con calma).
_RESET_TOKEN_TTL = timedelta(hours=1)
_GENERIC_FORGOT_DETAIL = (
    "Si existe una cuenta con ese email, recibiras un enlace para "
    "restablecer la contraseña."
)


class RegisterResponse(BaseModel):
    """Respuesta del registro: datos publicos del usuario y token de acceso."""

    user: UserOut
    token: Token


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(payload: UserCreate, db: Session = Depends(get_db)) -> RegisterResponse:
    """Registra un usuario nuevo y devuelve su token JWT."""
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe un usuario con ese email",
        )
    user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        name=payload.name,
        auth_provider="email",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    token = Token(access_token=create_access_token(user.id))
    return RegisterResponse(user=UserOut.model_validate(user), token=token)


@router.post("/login", response_model=Token)
def login(
    form: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> Token:
    """Autentica por email + password (OAuth2 password flow) y devuelve JWT."""
    user = db.query(User).filter(User.email == form.username).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales invalidas",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # Cuenta creada via Google OAuth: no tiene password local. Mensaje
    # especifico para que el frontend pueda guiar al usuario al boton de
    # Google en lugar de dejar que pruebe contrasenas a ciegas.
    if user.auth_provider != "email" or user.hashed_password is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="esta cuenta usa Google para iniciar sesion",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not verify_password(form.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales invalidas",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return Token(access_token=create_access_token(user.id))


# ============ Password reset (F14) ============

class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str = Field(min_length=1, max_length=64)
    new_password: str = Field(min_length=8, max_length=128)


class GenericMessage(BaseModel):
    detail: str


@router.post("/forgot-password", response_model=GenericMessage)
def forgot_password(
    payload: ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> GenericMessage:
    """Solicita un email de reset de contraseña.

    Anti-enumeration: SIEMPRE devuelve 200 con el mismo detail
    independientemente de si el email existe, si la cuenta es Google
    o si el SMTP falla. Nunca filtramos al cliente si una direccion
    esta registrada o no.
    """
    settings = get_settings()
    normalized = payload.email.strip().lower()
    user = db.query(User).filter(User.email == normalized).first()

    # Solo email+password tiene sentido aqui: las cuentas Google las
    # gestiona Google. Para Google: silencio (no email, no token), pero
    # el response es identico para no filtrar la rama.
    if user is not None and user.auth_provider == "email":
        token_value = uuid.uuid4().hex
        prt = PasswordResetToken(
            token=token_value,
            user_id=user.id,
            expires_at=datetime.now(timezone.utc) + _RESET_TOKEN_TTL,
        )
        db.add(prt)
        db.commit()

        reset_url = (
            settings.frontend_url.rstrip("/")
            + f"/reset-password.html?token={token_value}"
        )
        # Background task: no bloqueamos la respuesta esperando al SMTP.
        # Si el SMTP falla, el email_service lo loggea en error pero el
        # endpoint ya habra devuelto 200.
        background_tasks.add_task(
            send_password_reset_email, normalized, reset_url
        )
        logger.info(
            "forgot_password: token emitido para user_id=%d (auth_provider=email)",
            user.id,
        )
    else:
        # Caso enumeration-safe: email no encontrado o cuenta no-email.
        # Log silencioso, ningun side effect visible al cliente.
        logger.info(
            "forgot_password: no-op (user %s, auth_provider=%s)",
            "found" if user else "not found",
            user.auth_provider if user else "n/a",
        )

    return GenericMessage(detail=_GENERIC_FORGOT_DETAIL)


@router.post("/reset-password", response_model=GenericMessage)
def reset_password(
    payload: ResetPasswordRequest,
    db: Session = Depends(get_db),
) -> GenericMessage:
    """Consume un token de reset y actualiza la contraseña del usuario.

    Mensajes de error especificos para que el frontend pueda guiar al
    usuario:
    - Token inexistente o malformado -> "Token invalido"
    - Token ya consumido -> "Este enlace ya ha sido utilizado"
    - Token expirado -> "Este enlace ha expirado. Solicita uno nuevo"
    - User borrado o convertido a Google despues de emitir token ->
      "Token invalido" (caso defensivo)
    """
    prt = db.get(PasswordResetToken, payload.token)
    if prt is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token invalido",
        )
    if prt.used_at is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Este enlace ya ha sido utilizado",
        )
    # SQLite devuelve los DateTime(timezone=True) como naive al leer,
    # asi que para comparar con un aware now() asumimos UTC explicito.
    expires_at = prt.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Este enlace ha expirado. Solicita uno nuevo",
        )

    user = db.get(User, prt.user_id)
    if user is None or user.auth_provider != "email":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token invalido",
        )

    user.hashed_password = hash_password(payload.new_password)
    prt.used_at = datetime.now(timezone.utc)
    db.commit()

    logger.info(
        "reset_password: contraseña actualizada para user_id=%d",
        user.id,
    )
    return GenericMessage(detail="Contraseña actualizada")
