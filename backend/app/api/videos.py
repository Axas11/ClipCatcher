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
from app.schemas.video import VideoOut
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
