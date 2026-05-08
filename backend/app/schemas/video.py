"""Schemas Pydantic relacionados con videos subidos."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.clip import ClipOut


class VideoOut(BaseModel):
    """Representacion publica resumida de un video."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    original_filename: str
    status: str
    uploaded_at: datetime
    processed_at: datetime | None = None


class VideoDetail(VideoOut):
    """Detalle completo de un video con sus clips asociados."""

    clips: list[ClipOut] = []
