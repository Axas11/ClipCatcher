"""Configuracion del engine y la fabrica de sesiones de SQLAlchemy."""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings

_settings = get_settings()

_connect_args: dict[str, object] = {}
if _settings.database_url.startswith("sqlite"):
    _connect_args["check_same_thread"] = False

engine = create_engine(
    _settings.database_url,
    connect_args=_connect_args,
    future=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


def get_db() -> Generator[Session, None, None]:
    """Dependencia FastAPI que abre y cierra una sesion de base de datos."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
