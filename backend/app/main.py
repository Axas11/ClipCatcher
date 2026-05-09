"""Punto de entrada del backend FastAPI de ClipCatcher."""

import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.sessions import SessionMiddleware

from app.api import auth as auth_router
from app.api import clips as clips_router
from app.api import oauth as oauth_router
from app.api import stats as stats_router
from app.api import users as users_router
from app.api import videos as videos_router
from app.core.config import get_settings
from app.db.base import Base
from app.db.session import engine
from app import models  # noqa: F401  (registra los modelos en Base.metadata)

_FRONTEND_DIR = Path(__file__).resolve().parents[2] / "frontend"

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

# SessionMiddleware lo necesita authlib para guardar el state CSRF y el
# nonce del id_token entre /api/auth/google/login y /callback. La cookie
# es HttpOnly y firmada con `app_secret_key`. SameSite=lax permite que
# Google redirija de vuelta con la cookie presente.
app.add_middleware(
    SessionMiddleware,
    secret_key=get_settings().app_secret_key,
    same_site="lax",
    https_only=False,  # localhost. En produccion poner True con HTTPS.
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth_router.router, prefix="/api")
app.include_router(oauth_router.router, prefix="/api")
app.include_router(users_router.router, prefix="/api")
app.include_router(videos_router.router, prefix="/api")
app.include_router(clips_router.router, prefix="/api")
app.include_router(stats_router.router, prefix="/api")


@app.get("/health")
@app.get("/api/health")
def health() -> dict[str, str]:
    """Healthcheck simple para comprobar que la API responde."""
    return {"status": "ok"}


# Handler 404 (F12.4b): si una ruta /api/* devuelve 404 mantenemos el
# JSON estandar; si una ruta de frontend (HTML/CSS/JS, no /api) devuelve
# 404, servimos la pagina 404.html con el branding completo.
_NOT_FOUND_PAGE = _FRONTEND_DIR / "404.html"


@app.exception_handler(StarletteHTTPException)
async def custom_404_handler(request: Request, exc: StarletteHTTPException):
    if exc.status_code == 404 and not request.url.path.startswith("/api/"):
        if _NOT_FOUND_PAGE.is_file():
            return FileResponse(_NOT_FOUND_PAGE, status_code=404)
    # Fallback: respuesta JSON estandar (igual que la default de FastAPI).
    return JSONResponse(
        {"detail": exc.detail},
        status_code=exc.status_code,
        headers=getattr(exc, "headers", None),
    )


# Catch-all en /api/* (F12.4b). Se registra DESPUES de todos los
# routers concretos y del @app.get("/api/health") para que solo capture
# rutas que ningun handler previo ha aceptado. Si lo dejaramos antes
# robaria a las rutas concretas. Devuelve 404 JSON estandar; sin esto,
# StaticFiles(html=True) interceptaria la 404 y serviria 404.html como
# respuesta a /api/noexiste, rompiendo clientes API.
@app.api_route(
    "/api/{full_path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"],
    include_in_schema=False,
)
async def api_catch_all_404(full_path: str):
    raise HTTPException(status_code=404, detail="Not Found")


# Frontend estatico montado en `/`. Debe ir DESPUES de los routers e
# `@app.get` para que las rutas /api/* y /health tengan prioridad sobre
# el catch-all del mount. `html=True` hace que `GET /` sirva index.html.
app.mount("/", StaticFiles(directory=_FRONTEND_DIR, html=True), name="frontend")
