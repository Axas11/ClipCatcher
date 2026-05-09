"""Endpoints de gestion del usuario autenticado."""

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.core.security import hash_password, verify_password
from app.db.session import get_db
from app.models.clip import Clip
from app.models.user import User
from app.models.video import VIDEO_STATUS_DONE, Video
from app.schemas.user import (
    PasswordChangeRequest,
    UserOut,
    UserProfileUpdate,
    UserSettings,
    UserSettingsUpdate,
    UserStats,
)

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserOut)
def read_current_user(current_user: User = Depends(get_current_user)) -> User:
    """Devuelve los datos del usuario autenticado a partir del JWT."""
    return current_user


@router.patch("/me", response_model=UserOut)
def update_my_profile(
    payload: UserProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> User:
    """Actualiza nombre y/o email del usuario autenticado (F11.1).

    Reglas:
    - Solo actualiza los campos enviados (model_dump exclude_unset).
    - El email NO se puede cambiar para cuentas con auth_provider != "email"
      (las cuentas Google tienen el email vinculado al proveedor): 403.
    - El email nuevo, si se envia, debe estar libre. Si lo tiene otro
      usuario: 409 con detail "email ya registrado".
    - Si el email enviado es el mismo que ya tiene el usuario, no es
      conflicto (no-op silencioso para ese campo).
    """
    updates = payload.model_dump(exclude_unset=True)

    if "email" in updates and updates["email"] != current_user.email:
        if current_user.auth_provider != "email":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="no puedes cambiar el email de una cuenta vinculada a Google",
            )
        clash = (
            db.query(User)
            .filter(User.email == updates["email"], User.id != current_user.id)
            .first()
        )
        if clash is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="email ya registrado",
            )

    for field, value in updates.items():
        setattr(current_user, field, value)
    db.commit()
    db.refresh(current_user)
    return current_user


@router.put(
    "/me/password",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
def change_my_password(
    payload: PasswordChangeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    """Cambia la contraseña del usuario autenticado (F11.1).

    Reglas:
    - Solo aplicable a cuentas con auth_provider == "email": las cuentas
      Google no tienen contraseña local, asi que devuelve 403.
    - `current_password` debe coincidir con `hashed_password`. Si no:
      401 con detail "contraseña actual incorrecta" (sin filtrar si el
      hash es None u otra causa).
    - `new_password` ya viene validado por Pydantic (min_length=8).
    """
    if current_user.auth_provider != "email" or current_user.hashed_password is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="esta cuenta usa Google para iniciar sesion, no tiene contraseña",
        )
    if not verify_password(payload.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="contraseña actual incorrecta",
        )
    current_user.hashed_password = hash_password(payload.new_password)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/me/settings", response_model=UserSettings)
def read_my_settings(current_user: User = Depends(get_current_user)) -> User:
    """Devuelve la configuracion del detector del usuario actual."""
    return current_user


@router.get("/me/stats", response_model=UserStats)
def read_my_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UserStats:
    """Estadisticas agregadas del usuario: videos, clips y tiempo medio.

    `avg_processing_seconds` se calcula sobre `processed_at - uploaded_at`
    para los videos en estado `done`. Si aun no hay ninguno, devolvemos
    `None` (el frontend lo trata como dato pendiente y oculta el panel
    si todo esta a 0).
    """
    videos_count = (
        db.query(func.count(Video.id))
        .filter(Video.user_id == current_user.id)
        .scalar()
    ) or 0

    clips_count = (
        db.query(func.count(Clip.id))
        .join(Video, Clip.video_id == Video.id)
        .filter(Video.user_id == current_user.id)
        .scalar()
    ) or 0

    # Diferencia de timestamps en SQLite via julianday para evitar el
    # bug de date arithmetic con datos timezone-aware. * 86400 -> segundos.
    diff_seconds = (
        func.julianday(Video.processed_at) - func.julianday(Video.uploaded_at)
    ) * 86400
    avg_seconds = (
        db.query(func.avg(diff_seconds))
        .filter(
            Video.user_id == current_user.id,
            Video.status == VIDEO_STATUS_DONE,
            Video.processed_at.isnot(None),
        )
        .scalar()
    )
    avg_value = float(avg_seconds) if avg_seconds is not None else None

    return UserStats(
        videos_count=int(videos_count),
        clips_count=int(clips_count),
        avg_processing_seconds=avg_value,
    )


@router.put("/me/settings", response_model=UserSettings)
def update_my_settings(
    payload: UserSettingsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> User:
    """Actualiza la configuracion del detector del usuario actual.

    Solo se modifican los campos enviados (semantica PATCH). La validacion
    de rangos la hace Pydantic en el `UserSettingsUpdate`, asi un valor
    fuera de rango produce 422 sin llegar al cuerpo del endpoint.
    """
    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(current_user, field, value)
    db.commit()
    db.refresh(current_user)
    return current_user
