"""Endpoints de autenticacion con Google OAuth (F8).

Diseño:

- Aditivo: el flujo email+password sigue funcionando. Estos endpoints
  son una alternativa para usuarios que prefieren entrar con su cuenta
  de Google.
- Degradacion elegante: si `settings.google_client_id` esta vacio, los
  endpoints devuelven 503 y `/available` informa al frontend para que
  oculte el boton.
- Stateless desde el cliente: terminamos generando NUESTRO JWT con el
  mismo formato que `auth.login`, asi el resto de la API (que valida
  Bearer JWT) no necesita conocer Google para nada.
- State CSRF gestionado por authlib + SessionMiddleware: la cookie de
  sesion firmada con `app_secret_key` guarda el state generado en
  `authorize_redirect` y lo valida en `authorize_access_token`. No
  almacenamos nada en BD para esto.
"""

from __future__ import annotations

import logging
from urllib.parse import urlencode

from authlib.integrations.starlette_client import OAuth, OAuthError
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.security import create_access_token
from app.db.session import get_db
from app.models.user import User

logger = logging.getLogger("clipcatcher.oauth")

router = APIRouter(prefix="/auth/google", tags=["oauth"])

# Cliente OAuth global. Se registra en el primer uso si las credenciales
# estan disponibles. authlib resuelve el discovery OIDC de Google
# automaticamente desde el server_metadata_url, lo que incluye los
# endpoints de authorize / token / userinfo y las claves para validar
# el id_token.
_oauth: OAuth | None = None
_GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"


def _get_oauth(settings: Settings) -> OAuth:
    """Devuelve un cliente OAuth con Google registrado, o lanza 503.

    Se inicializa perezosamente: si el usuario nunca toca los endpoints
    OAuth, no se hace ninguna llamada de red al discovery URL.
    """
    global _oauth
    if not settings.google_client_id or not settings.google_client_secret:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google OAuth no configurado",
        )
    if _oauth is None:
        oauth = OAuth()
        oauth.register(
            name="google",
            client_id=settings.google_client_id,
            client_secret=settings.google_client_secret,
            server_metadata_url=_GOOGLE_DISCOVERY_URL,
            client_kwargs={"scope": "openid email profile"},
        )
        _oauth = oauth
    return _oauth


def _frontend_redirect(settings: Settings, **params: str) -> RedirectResponse:
    """Redirige al frontend con los `params` como query string."""
    url = settings.frontend_url.rstrip("/") + "/"
    if params:
        url = f"{url}?{urlencode(params)}"
    return RedirectResponse(url=url, status_code=status.HTTP_302_FOUND)


@router.get("/available")
def google_available(settings: Settings = Depends(get_settings)) -> dict[str, bool]:
    """Indica al frontend si el login con Google esta configurado.

    No revela el `client_id` (no es secreto, pero tampoco hace falta
    exponerlo); solo si la feature esta activa o no.
    """
    return {"available": bool(settings.google_client_id and settings.google_client_secret)}


@router.get("/login")
async def google_login(
    request: Request,
    settings: Settings = Depends(get_settings),
):
    """Inicia el flujo OAuth: redirige al consent screen de Google.

    authlib genera un state aleatorio y un nonce, los firma en la
    cookie de sesion, y construye la URL con scope+redirect_uri+state.
    """
    oauth = _get_oauth(settings)
    return await oauth.google.authorize_redirect(request, settings.google_redirect_uri)


@router.get("/callback")
async def google_callback(
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    """Recibe el `code` de Google, lo intercambia por tokens y loguea.

    Estados posibles del User en BD:
    1. Existe con `google_id == sub` -> login directo (caso normal en
       reentradas con Google).
    2. Existe con mismo email pero `auth_provider == "email"` -> NO
       fusionamos cuentas automaticamente. Redirigimos al frontend
       con un mensaje de error explicito para que el usuario use su
       contraseña; asi evitamos hijack de cuentas si alguien crease
       una cuenta de Google con un email que ya esta registrado por
       password.
    3. No existe -> creamos cuenta nueva con auth_provider="google".

    En cualquier exito redirigimos a `{FRONTEND_URL}/?token=...&login=google`.
    En error, redirigimos a `{FRONTEND_URL}/?error=...`.
    """
    oauth = _get_oauth(settings)
    try:
        token = await oauth.google.authorize_access_token(request)
    except OAuthError as exc:
        logger.warning("OAuth error en callback: %s", exc)
        return _frontend_redirect(settings, error="No se pudo completar el login con Google.")

    userinfo = token.get("userinfo")
    if userinfo is None:
        # authlib normalmente extrae userinfo del id_token; fallback
        # explicito si no esta presente.
        try:
            userinfo = await oauth.google.userinfo(token=token)
        except Exception as exc:  # pragma: no cover - red externa
            logger.warning("No se pudo obtener userinfo de Google: %s", exc)
            return _frontend_redirect(settings, error="No se pudieron leer los datos de Google.")

    sub = userinfo.get("sub")
    email = userinfo.get("email")
    name = userinfo.get("name") or (email.split("@")[0] if email else "Usuario")
    email_verified = userinfo.get("email_verified", True)

    if not sub or not email:
        return _frontend_redirect(settings, error="Respuesta de Google sin datos suficientes.")
    if not email_verified:
        return _frontend_redirect(settings, error="Tu email de Google no esta verificado.")

    # 1. Match por google_id (caso normal: usuario que ya entro antes).
    user = db.query(User).filter(User.google_id == sub).first()

    # 2. Conflicto: existe el email pero como cuenta email+password.
    if user is None:
        existing_email = db.query(User).filter(User.email == email).first()
        if existing_email is not None and existing_email.auth_provider == "email":
            return _frontend_redirect(
                settings,
                error=(
                    "Ya existe una cuenta con este email registrada con contraseña. "
                    "Inicia sesion con tu contraseña."
                ),
            )
        # Caso defensivo: existe email con auth_provider="google" pero
        # google_id distinto. No deberia pasar (Google `sub` es estable),
        # pero si pasa, no creamos otro user con el mismo email.
        if existing_email is not None:
            return _frontend_redirect(
                settings,
                error="Ya existe una cuenta con este email vinculada a otra identidad de Google.",
            )

        # 3. Usuario nuevo: lo creamos con auth_provider="google".
        user = User(
            email=email,
            hashed_password=None,
            name=name,
            auth_provider="google",
            google_id=sub,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    jwt_token = create_access_token(user.id)
    return _frontend_redirect(settings, token=jwt_token, login="google")
