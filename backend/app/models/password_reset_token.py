"""Tokens de reset de contraseña (F14).

Cada fila representa un enlace de "olvide mi contraseña" emitido a un
usuario. Single-use: al consumirlo se marca `used_at` para que un
segundo intento con el mismo token sea rechazado. TTL 1h vía
`expires_at` (timezone-aware UTC).
"""

from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    # UUID hex de 32 chars como PK (no autoincrement). Lo genera el
    # endpoint /forgot-password con uuid.uuid4().hex.
    token: Mapped[str] = mapped_column(String(32), primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
