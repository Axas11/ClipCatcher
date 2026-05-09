"""Modelo SQLAlchemy del usuario de ClipCatcher."""

from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class User(Base):
    """Cuenta de un usuario que sube videos para procesar."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # Configuracion del detector por usuario (F6X). Se inicializan a los
    # mismos valores que `backend/detector/config.json` para que un usuario
    # recien registrado tenga el mismo comportamiento que el MVP.
    chain_window_seconds: Mapped[float] = mapped_column(Float, nullable=False, default=6.0)
    clip_margin_seconds: Mapped[float] = mapped_column(Float, nullable=False, default=2.0)
    clip_duration_seconds: Mapped[float] = mapped_column(Float, nullable=False, default=6.0)

    videos: Mapped[list["Video"]] = relationship(  # type: ignore[name-defined]
        back_populates="owner",
        cascade="all, delete-orphan",
    )
