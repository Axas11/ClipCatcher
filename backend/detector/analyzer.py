"""Analizador visual de partidas: detecta ventanas con kills usando una CNN."""

from __future__ import annotations

import json
import logging
from functools import lru_cache
from pathlib import Path
from typing import Any

import cv2
import torch
from PIL import Image
from torchvision import transforms
from torchvision.models import resnet18

logger = logging.getLogger(__name__)

_MODULE_DIR = Path(__file__).resolve().parent
_CONFIG_PATH = _MODULE_DIR / "config.json"
_MODEL_PATH = _MODULE_DIR / "model" / "kill_detector.pt"

# Resolucion de entrada de la CNN entrenada (ResNet18 con head 2 clases).
_INPUT_SIZE = (128, 128)
_TRANSFORM = transforms.Compose([
    transforms.Resize(_INPUT_SIZE),
    transforms.ToTensor(),
])

# Si dos detecciones caen dentro de esta ventana (segundos) se encadenan en
# un solo clip en lugar de cortar dos clips separados.
_CHAIN_WINDOW_S = 6.0

# Recorte relativo del frame donde aparece el killfeed de Valorant
# (esquina superior derecha). Coordenadas en porcentaje del ancho/alto.
_ROI_REL = (0.70, 0.01, 0.995, 0.15)  # x1, y1, x2, y2


def _load_config() -> dict[str, Any]:
    """Lee la configuracion local (margenes y duracion) del JSON del modulo."""
    with _CONFIG_PATH.open("r", encoding="utf-8") as fh:
        return json.load(fh)


@lru_cache(maxsize=1)
def _get_model() -> torch.nn.Module:
    """Carga la ResNet18 con el head binario kill/no-kill (cacheada)."""
    logger.info("cargando modelo de deteccion desde %s", _MODEL_PATH)
    model = resnet18(weights=None)
    model.fc = torch.nn.Linear(model.fc.in_features, 2)
    model.load_state_dict(torch.load(_MODEL_PATH, map_location="cpu"))
    model.eval()
    return model


def _is_kill_frame(roi_bgr: Any) -> bool:
    """True si la CNN clasifica el ROI como `kill` (clase 0)."""
    img_pil = Image.fromarray(cv2.cvtColor(roi_bgr, cv2.COLOR_BGR2RGB))
    tensor = _TRANSFORM(img_pil).unsqueeze(0)
    with torch.no_grad():
        out = _get_model()(tensor)
        cls = int(torch.argmax(out, dim=1).item())
    return cls == 0


def analyze_video(
    video_path: str,
    *,
    chain_window_seconds: float | None = None,
    clip_margin_seconds: float | None = None,
    clip_duration_seconds: float | None = None,
) -> list[tuple[float, float]]:
    """Analiza un video y devuelve ventanas (inicio, fin) en segundos.

    Procesa un frame por segundo, recorta la zona del killfeed y aplica la
    CNN binaria. Detecciones consecutivas dentro de la ventana de
    encadenamiento se fusionan en una sola ventana.

    Los parametros del clipping pueden personalizarse por llamada (F6X,
    configuracion por usuario). Si vienen como ``None``, se usan los
    defaults: ``_CHAIN_WINDOW_S`` para la ventana de encadenamiento, y
    ``margen_clip`` / ``duracion_clip`` de ``config.json`` para el
    margen y la duracion.
    """
    config = _load_config()
    chain_window = chain_window_seconds if chain_window_seconds is not None else _CHAIN_WINDOW_S
    margin = clip_margin_seconds if clip_margin_seconds is not None else float(config.get("margen_clip", 2))
    duration = clip_duration_seconds if clip_duration_seconds is not None else float(config.get("duracion_clip", 6))

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise FileNotFoundError(f"no se pudo abrir el video: {video_path}")

    try:
        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        frame_interval = max(1, int(round(fps)))

        windows: list[tuple[float, float]] = []
        frame_idx = 0
        clip_start: float | None = None
        clip_end: float | None = None

        while True:
            ok, frame = cap.read()
            if not ok:
                break
            if frame_idx % frame_interval == 0:
                h, w = frame.shape[:2]
                rx1, ry1, rx2, ry2 = _ROI_REL
                roi = frame[int(h * ry1) : int(h * ry2), int(w * rx1) : int(w * rx2)]
                if _is_kill_frame(roi):
                    t = frame_idx / fps
                    if clip_start is None:
                        clip_start = max(0.0, t - margin)
                        clip_end = t + duration
                    elif clip_end is not None and t <= clip_end + chain_window:
                        clip_end = t + duration
                    else:
                        windows.append((clip_start, clip_end))
                        clip_start = max(0.0, t - margin)
                        clip_end = t + duration
            frame_idx += 1

        if clip_start is not None and clip_end is not None:
            windows.append((clip_start, clip_end))
    finally:
        cap.release()

    logger.info(
        "analyze_video: %s -> %d ventanas (chain=%.1fs margin=%.1fs duration=%.1fs)",
        video_path, len(windows), chain_window, margin, duration,
    )
    return windows


__all__ = ["analyze_video"]
