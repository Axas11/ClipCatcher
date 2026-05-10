"""Re-exporta los modelos para registrarlos en `Base.metadata`."""

from app.models.clip import Clip
from app.models.password_reset_token import PasswordResetToken
from app.models.user import User
from app.models.video import Video

__all__ = ["Clip", "PasswordResetToken", "User", "Video"]
