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


@router.get("/{clip_id}/tiktok")
def download_clip_tiktok(
    clip_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FileResponse:
    """Descarga la variante vertical TikTok 9:16 del clip (F13.2).

    Se reusa `_get_owned_clip` para autorizacion (404 unificado si no
    existe o no pertenece al usuario). Si el clip existe pero su
    `tiktok_path` es NULL, devolvemos 404 con un detail especifico
    porque la variante no se genero (el usuario no marco el checkbox).
    Si el path esta en BD pero el archivo ya no esta en disco, 410
    Gone (mismo patron que el download/stream del clip horizontal).
    """
    clip, _horizontal_path = _get_owned_clip(clip_id, db, current_user)
    if not clip.tiktok_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="version TikTok no disponible",
        )
    tiktok_path = Path(clip.tiktok_path)
    if not tiktok_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="el archivo TikTok del clip ya no esta disponible",
        )
    return FileResponse(
        tiktok_path,
        media_type="video/mp4",
        filename=f"clip_{clip.id}_tiktok.mp4",
    )
