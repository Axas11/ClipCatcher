"""Endpoint publico de estadisticas globales agregadas (F12.1).

Devuelve sumas y media de todo el sistema sin filtrar por usuario.
NO incluye nada que identifique a un usuario concreto: solo conteos
y tiempo medio. Pensado para alimentar el banner "Stats" de la
landing comercial.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.clip import Clip
from app.models.video import VIDEO_STATUS_DONE, Video
from app.schemas.stats import GlobalStats

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("/global", response_model=GlobalStats)
def read_global_stats(db: Session = Depends(get_db)) -> GlobalStats:
    """Agregados anonimos del sistema completo.

    Sin auth: la landing los muestra a usuarios deslogueados. Solo
    expone conteos y tiempo medio, ningun dato individual.

    Si la base esta vacia, los conteos van a 0 y la media a None.
    El frontend interpreta None como "todavia no hay datos" y muestra
    un placeholder (ver landing F12.1).
    """
    videos_count = db.query(func.count(Video.id)).scalar() or 0
    clips_count = db.query(func.count(Clip.id)).scalar() or 0

    diff_seconds = (
        func.julianday(Video.processed_at) - func.julianday(Video.uploaded_at)
    ) * 86400
    avg_seconds = (
        db.query(func.avg(diff_seconds))
        .filter(
            Video.status == VIDEO_STATUS_DONE,
            Video.processed_at.isnot(None),
        )
        .scalar()
    )

    return GlobalStats(
        videos_count=int(videos_count),
        clips_count=int(clips_count),
        avg_processing_seconds=(float(avg_seconds) if avg_seconds is not None else None),
    )
