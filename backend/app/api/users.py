"""Endpoints de gestion del usuario autenticado."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import UserOut, UserSettings, UserSettingsUpdate

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserOut)
def read_current_user(current_user: User = Depends(get_current_user)) -> User:
    """Devuelve los datos del usuario autenticado a partir del JWT."""
    return current_user


@router.get("/me/settings", response_model=UserSettings)
def read_my_settings(current_user: User = Depends(get_current_user)) -> User:
    """Devuelve la configuracion del detector del usuario actual."""
    return current_user


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
