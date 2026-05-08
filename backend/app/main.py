"""Punto de entrada del backend FastAPI de ClipCatcher."""

import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.db.base import Base
from app.db.session import engine
from app import models  # noqa: F401  (registra los modelos en Base.metadata)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("clipcatcher.backend")


def _ensure_runtime_dirs(storage_path: str) -> None:
    """Crea las carpetas necesarias para datos y almacenamiento de videos."""
    storage = Path(storage_path)
    videos = storage / "videos"
    clips = storage / "clips"
    for path in (storage, videos, clips, Path("data")):
        path.mkdir(parents=True, exist_ok=True)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Inicializa BD y carpetas al arrancar la aplicacion."""
    settings = get_settings()
    _ensure_runtime_dirs(settings.storage_path)
    Base.metadata.create_all(bind=engine)
    logger.info("backend listo: BD inicializada en %s", settings.database_url)
    yield


app = FastAPI(title="ClipCatcher API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    """Healthcheck simple para comprobar que la API responde."""
    return {"status": "ok"}
