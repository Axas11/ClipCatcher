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
from detector.tiktok_exporter import convert_to_tiktok

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

        # Configuracion del detector con prioridad explicita (F10.2):
        # 1) override por video (Video.X_override) si lo paso el cliente
        #    en el upload.
        # 2) settings del User propietario (F6X) si existe.
        # 3) defaults del propio analyze_video (constante + config.json).
        # `None` se traduce a "no se aplica este nivel" -> el siguiente
        # toma el relevo.
        owner = db.get(User, video.user_id)

        def _pick(field: str) -> float | None:
            override = getattr(video, f"{field}_override", None)
            if override is not None:
                return override
            if owner is not None:
                return getattr(owner, field, None)
            return None

        detector_settings = {
            "chain_window_seconds": _pick("chain_window_seconds"),
            "clip_margin_seconds": _pick("clip_margin_seconds"),
            "clip_duration_seconds": _pick("clip_duration_seconds"),
        }
        logger.info(
            "process_video: video %d settings -> %s (override? %s)",
            video_id,
            detector_settings,
            {
                "chain": video.chain_window_seconds_override is not None,
                "margin": video.clip_margin_seconds_override is not None,
                "duration": video.clip_duration_seconds_override is not None,
            },
        )
        windows = analyze_video(video.stored_path, **detector_settings)
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

            # F13.2: variante vertical 9:16 TikTok si el usuario lo
            # marco al subir. Si la conversion falla NO abortamos el
            # procesamiento — el clip horizontal ya esta exportado y
            # debe llegar al usuario aunque la variante secundaria
            # falle por algun motivo (formato raro, mascara faltante,
            # ffmpeg lento, etc.).
            tiktok_path: str | None = None
            if video.convert_to_tiktok:
                tiktok_output = clips_root / f"clip_{idx:03d}_tiktok.mp4"
                try:
                    convert_to_tiktok(str(output_path), str(tiktok_output))
                    tiktok_path = str(tiktok_output)
                except Exception:  # noqa: BLE001
                    logger.warning(
                        "process_video: fallo conversion TikTok del clip %d "
                        "(%.2f-%.2f) del video %d (clip horizontal OK)",
                        idx, start, end, video_id,
                        exc_info=True,
                    )

            db.add(Clip(
                video_id=video.id,
                start_time=start,
                end_time=end,
                file_path=str(output_path),
                tiktok_path=tiktok_path,
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
