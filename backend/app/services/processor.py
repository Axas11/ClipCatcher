"""Servicio de orquestacion del procesamiento de videos."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.clip import Clip
from app.models.user import User
from app.models.video import (
    VIDEO_STATUS_DONE,
    VIDEO_STATUS_FAILED,
    VIDEO_STATUS_PROCESSING,
    Video,
)
from detector.analyzer import analyze_video
from detector.exporter import export_clip

logger = logging.getLogger(__name__)


def process_video(video_id: int, db_factory: Callable[[], Session]) -> None:
    """Procesa un video: detecta highlights, exporta clips y persiste resultados.

    Diseñado para ejecutarse desde ``BackgroundTasks`` de FastAPI. Abre su
    propia sesion DB usando ``db_factory`` (tipicamente ``SessionLocal``) y
    nunca propaga excepciones: si algo falla, marca el video como ``failed``
    y registra el error con stack trace.
    """
    db: Session = db_factory()
    video: Video | None = None
    try:
        video = db.get(Video, video_id)
        if video is None:
            logger.error("process_video: video %d no existe", video_id)
            return

        video.status = VIDEO_STATUS_PROCESSING
        db.commit()

        # Configuracion del detector personalizada por usuario (F6X). Si el
        # User no se encuentra (raro), `analyze_video` cae a sus defaults.
        owner = db.get(User, video.user_id)
        user_settings = (
            {
                "chain_window_seconds": owner.chain_window_seconds,
                "clip_margin_seconds": owner.clip_margin_seconds,
                "clip_duration_seconds": owner.clip_duration_seconds,
            }
            if owner is not None
            else {}
        )
        windows = analyze_video(video.stored_path, **user_settings)
        logger.info(
            "process_video: video %d -> %d ventanas detectadas",
            video_id,
            len(windows),
        )

        settings = get_settings()
        clips_root = (
            Path(settings.storage_path)
            / "clips"
            / str(video.user_id)
            / str(video.id)
        )
        clips_root.mkdir(parents=True, exist_ok=True)

        for idx, (start, end) in enumerate(windows):
            output_path = clips_root / f"clip_{idx:03d}.mp4"
            try:
                export_clip(video.stored_path, start, end, str(output_path))
            except Exception:  # noqa: BLE001
                logger.exception(
                    "process_video: fallo exportando clip %d (%.2f-%.2f) del video %d",
                    idx,
                    start,
                    end,
                    video_id,
                )
                continue
            db.add(Clip(
                video_id=video.id,
                start_time=start,
                end_time=end,
                file_path=str(output_path),
            ))

        video.status = VIDEO_STATUS_DONE
        video.processed_at = datetime.now(timezone.utc)
        db.commit()
        logger.info("process_video: video %d completado", video_id)

    except Exception:  # noqa: BLE001
        logger.exception("process_video: video %d fallo", video_id)
        if video is not None:
            try:
                db.rollback()
                video.status = VIDEO_STATUS_FAILED
                video.processed_at = datetime.now(timezone.utc)
                db.commit()
            except Exception:  # noqa: BLE001
                logger.exception("process_video: no se pudo marcar como failed")
                db.rollback()
    finally:
        db.close()


__all__ = ["process_video"]
