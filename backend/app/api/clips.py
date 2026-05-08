"""Endpoints de acceso a los clips generados (descarga y streaming)."""

from __future__ import annotations

import logging
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.clip import Clip
from app.models.user import User
from app.models.video import Video

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/clips", tags=["clips"])


def _get_owned_clip(clip_id: int, db: Session, current_user: User) -> tuple[Clip, Path]:
    """Recupera un clip propiedad del usuario actual y la ruta de su archivo.

    Devuelve el ``Clip`` y la ``Path`` validada en disco. Lanza 404 si el
    clip no existe o no pertenece al usuario, y 410 si la fila esta en BD
    pero el archivo ya no esta en disco.
    """
    clip = db.get(Clip, clip_id)
    if clip is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="clip no encontrado",
        )
    video = db.get(Video, clip.video_id)
    if video is None or video.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="clip no encontrado",
        )
    path = Path(clip.file_path)
    if not path.is_file():
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="el archivo del clip ya no esta disponible",
        )
    return clip, path


@router.get("/{clip_id}/download")
def download_clip(
    clip_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FileResponse:
    """Devuelve el clip como adjunto MP4 para descarga directa."""
    clip, path = _get_owned_clip(clip_id, db, current_user)
    return FileResponse(
        path,
        media_type="video/mp4",
        filename=f"clip_{clip.id}.mp4",
    )


@router.get("/{clip_id}/stream")
def stream_clip(
    clip_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FileResponse:
    """Sirve el clip inline para incrustarlo en `<video>` HTML5.

    A diferencia de `/download`, no fuerza ``Content-Disposition: attachment``,
    asi el navegador lo reproduce. ``FileResponse`` ya soporta peticiones
    Range nativamente para que el `<video>` pueda hacer seek.
    """
    _clip, path = _get_owned_clip(clip_id, db, current_user)
    return FileResponse(path, media_type="video/mp4")
