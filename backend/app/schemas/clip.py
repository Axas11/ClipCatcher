"""Schemas Pydantic relacionados con clips generados."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ClipOut(BaseModel):
    """Representacion publica de un clip extraido de un video."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    video_id: int
    start_time: float
    end_time: float
    created_at: datetime
