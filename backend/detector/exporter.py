"""Exportador de clips: corta un fragmento de un video usando ffmpeg."""

from __future__ import annotations

import logging
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)


def export_clip(
    video_path: str,
    start: float,
    end: float,
    output_path: str,
) -> None:
    """Exporta el fragmento [start, end] de ``video_path`` a ``output_path``.

    ``output_path`` debe incluir la extension (idealmente .mp4); la carpeta
    contenedora se crea si no existe. Lanza ``ValueError`` si la duracion
    resultante no es positiva, o ``subprocess.CalledProcessError`` si ffmpeg
    falla.
    """
    duration = end - start
    if duration <= 0:
        raise ValueError(
            f"duracion no positiva: start={start}, end={end} -> {duration}s"
        )

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        "ffmpeg",
        "-y",
        "-ss", str(start),
        "-i", video_path,
        "-t", str(duration),
        "-c:v", "libx264",
        "-preset", "fast",
        "-c:a", "aac",
        "-strict", "experimental",
        str(out),
    ]
    logger.info(
        "export_clip: %s [%.2f, %.2f] -> %s",
        video_path,
        start,
        end,
        out,
    )
    subprocess.run(cmd, check=True, capture_output=True)


__all__ = ["export_clip"]
