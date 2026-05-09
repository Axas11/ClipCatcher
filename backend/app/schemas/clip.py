"""Schemas Pydantic relacionados con clips generados."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator


class ClipOut(BaseModel):
    """Representacion publica de un clip extraido de un video."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    video_id: int
    start_time: float
    end_time: float
    created_at: datetime
    # F13.2: indica si existe variante vertical 9:16 descargable via
    # /api/clips/{id}/tiktok. Solo presencia (truthy/null), NUNCA la
    # ruta real en disco — el field_validator la enmascara.
    tiktok_path: str | None = None

    @field_validator("tiktok_path", mode="before")
    @classmethod
    def _mask_path(cls, v):
        # Convierte la ruta interna a un sentinel "available" si existe;
        # asi `if (clip.tiktok_path)` sigue funcionando en el frontend
        # sin que se filtre el path en disco.
        return "available" if v else None
