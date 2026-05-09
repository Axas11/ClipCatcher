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
    # NULLABLE desde F8: los usuarios que se registran via Google OAuth
    # no tienen contrasena local. La logica de login email+password debe
    # rechazar cualquier intento contra una cuenta sin hashed_password.
    hashed_password: Mapped[str | None] = mapped_column(String(255), nullable=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # Identidad multi-proveedor (F8). `auth_provider` indica como se creo la
    # cuenta: "email" (registro local con password) o "google" (OAuth).
    # `google_id` es el subject (`sub`) estable que devuelve Google y nos
    # permite identificar al usuario aunque cambie de email.
    auth_provider: Mapped[str] = mapped_column(String(20), nullable=False, default="email")
    google_id: Mapped[str | None] = mapped_column(
        String(255), nullable=True, unique=True, index=True
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
