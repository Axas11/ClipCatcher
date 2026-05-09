"""Schemas Pydantic relacionados con estadisticas globales (F12.1)."""

from pydantic import BaseModel


class GlobalStats(BaseModel):
    """Agregados anonimos del sistema completo.

    Sin user_id, sin emails, solo conteos y tiempo medio. Pensado
    para mostrar en la landing publica.
    """

    videos_count: int
    clips_count: int
    avg_processing_seconds: float | None = None
