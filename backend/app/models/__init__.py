"""Re-exporta los modelos para registrarlos en `Base.metadata`."""

from app.models.clip import Clip
from app.models.user import User
from app.models.video import Video

__all__ = ["Clip", "User", "Video"]
