"""Modelo SQLAlchemy del video subido por un usuario."""

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.clip import Clip
    from app.models.user import User


# Estados validos del campo `status`. Se mantiene como string para SQLite
# y para no acoplar la API a un Enum de Python.
VIDEO_STATUS_UPLOADED = "uploaded"
VIDEO_STATUS_PROCESSING = "processing"
VIDEO_STATUS_DONE = "done"
VIDEO_STATUS_FAILED = "failed"


class Video(Base):
    """Video original subido por el usuario y su estado de procesamiento."""

    __tablename__ = "videos"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_path: Mapped[str] = mapped_column(String(500), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=VIDEO_STATUS_UPLOADED,
    )
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    processed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Overrides por video de los settings del detector (F10.2). Si vienen
    # como NULL, el processor cae a los defaults del User propietario y
    # despues a los del detector. Los rangos validos los aplica Pydantic
    # en el endpoint de subida; aqui solo persistimos el valor.
    chain_window_seconds_override: Mapped[float | None] = mapped_column(
        Float, nullable=True
    )
    clip_margin_seconds_override: Mapped[float | None] = mapped_column(
        Float, nullable=True
    )
    clip_duration_seconds_override: Mapped[float | None] = mapped_column(
        Float, nullable=True
    )

    # Flag para que el processor genere ademas la variante vertical
    # 9:16 estilo TikTok de cada clip (F13.2). Default False para que
    # el comportamiento del MVP no cambie cuando el usuario no marca
    # el checkbox.
    convert_to_tiktok: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )

    owner: Mapped["User"] = relationship(back_populates="videos")
    clips: Mapped[list["Clip"]] = relationship(
        back_populates="video",
        cascade="all, delete-orphan",
        order_by="Clip.start_time",
    )
