"""Endpoints de gestion de videos: subida, listado y detalle."""

from __future__ import annotations

import logging
import uuid
from pathlib import Path

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    HTTPException,
    Response,
    UploadFile,
    status,
)
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.deps import get_current_user
from app.db.session import SessionLocal, get_db
from app.models.user import User
from app.models.video import (
    VIDEO_STATUS_PROCESSING,
    VIDEO_STATUS_UPLOADED,
    Video,
)
from app.schemas.video import VideoDetail, VideoOut
from app.services.processor import process_video

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/videos", tags=["videos"])

_CHUNK_SIZE = 1024 * 1024  # 1 MiB por lectura


@router.post(
    "",
    response_model=VideoOut,
    status_code=status.HTTP_201_CREATED,
)
def upload_video(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Video:
    """Sube un video del usuario, lo persiste a disco y encola su procesamiento.

    Valida que el archivo tenga nombre y extension, lo guarda en
    ``STORAGE_PATH/videos/{user_id}/{uuid}.{ext}`` controlando el tamano
    contra ``MAX_UPLOAD_BYTES`` mientras escribe (sin cargar todo en memoria),
    crea la fila ``Video`` y delega el analisis a un ``BackgroundTask``.
    """
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="el archivo no tiene nombre",
        )
    suffix = Path(file.filename).suffix.lower()
    if not suffix:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="el archivo debe tener extension (.mp4, .mkv, ...)",
        )

    settings = get_settings()
    user_dir = Path(settings.storage_path) / "videos" / str(current_user.id)
    user_dir.mkdir(parents=True, exist_ok=True)
    stored_path = user_dir / f"{uuid.uuid4().hex}{suffix}"

    total = 0
    try:
        with stored_path.open("wb") as out:
            while chunk := file.file.read(_CHUNK_SIZE):
                total += len(chunk)
                if total > settings.max_upload_bytes:
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=(
                            "el archivo supera el maximo permitido "
                            f"({settings.max_upload_bytes} bytes)"
                        ),
                    )
                out.write(chunk)
    except HTTPException:
        if stored_path.exists():
            stored_path.unlink()
        raise
    except Exception:  # noqa: BLE001
        logger.exception("upload_video: fallo escribiendo %s", stored_path)
        if stored_path.exists():
            stored_path.unlink()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="no se pudo guardar el archivo",
        )

    video = Video(
        user_id=current_user.id,
        original_filename=file.filename,
        stored_path=str(stored_path),
        status=VIDEO_STATUS_UPLOADED,
    )
    db.add(video)
    db.commit()
    db.refresh(video)

    background_tasks.add_task(process_video, video.id, SessionLocal)
    video.status = VIDEO_STATUS_PROCESSING
    db.commit()
    db.refresh(video)

    logger.info(
        "upload_video: usuario=%d video_id=%d filename=%r bytes=%d",
        current_user.id,
        video.id,
        file.filename,
        total,
    )
    return video


@router.get("", response_model=list[VideoOut])
def list_videos(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Video]:
    """Lista los videos del usuario actual ordenados por subida descendente."""
    return (
        db.query(Video)
        .filter(Video.user_id == current_user.id)
        .order_by(Video.uploaded_at.desc())
        .all()
    )


def _get_owned_video(video_id: int, db: Session, current_user: User) -> Video:
    """Recupera un video propiedad del usuario actual o lanza 404 unificado.

    Mismo `detail` para "no existe" y "no es del usuario" para evitar
    information disclosure por analisis diferencial de respuestas.
    """
    video = db.get(Video, video_id)
    if video is None or video.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="video no encontrado",
        )
    return video


@router.get("/{video_id}", response_model=VideoDetail)
def get_video(
    video_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Video:
    """Devuelve un video con sus clips. 404 si no existe o no es del usuario."""
    return _get_owned_video(video_id, db, current_user)


@router.delete(
    "/{video_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,  # 204 no admite body; evita JSONResponse default.
)
def delete_video(
    video_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    """Borra un video del usuario, sus clips y los archivos en disco.

    Orden:
    1. Comprobar propiedad (404 unificado si no es del usuario o no existe).
    2. Para cada clip: borrar el archivo en disco si existe (FileNotFound
       no aborta la operacion: queremos limpiar todo lo limpiable).
    3. Borrar el archivo del video original en disco.
    4. Commit del DELETE en BD: el cascade de la relacion `Video.clips`
       (`cascade="all, delete-orphan"`) elimina los rows de `clips`. La
       FK con `ondelete="CASCADE"` lo respaldaria a nivel BD pero el
       ORM ya lo gestiona.

    Devuelve 204 No Content. Si algo falla limpiando ficheros se loggea
    como warning pero no se devuelve error 5xx: la BD ya quedo consistente.
    """
    video = _get_owned_video(video_id, db, current_user)

    clip_paths = [Path(c.file_path) for c in video.clips]
    video_path = Path(video.stored_path)

    db.delete(video)
    db.commit()

    for path in clip_paths:
        try:
            path.unlink(missing_ok=True)
        except OSError as exc:
            logger.warning(
                "delete_video: no se pudo borrar clip %s: %s", path, exc
            )

    try:
        video_path.unlink(missing_ok=True)
    except OSError as exc:
        logger.warning(
            "delete_video: no se pudo borrar fichero del video %s: %s",
            video_path,
            exc,
        )

    logger.info(
        "delete_video: usuario=%d video_id=%d clips_borrados=%d",
        current_user.id,
        video_id,
        len(clip_paths),
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
