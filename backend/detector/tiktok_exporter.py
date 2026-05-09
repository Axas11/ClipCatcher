"""Convertidor de clips horizontales (16:9) a formato vertical TikTok (9:16).

IMPORTANTE - Coordenadas hardcoded:
Las coordenadas de crop estan actualmente fijadas para grabaciones con
una configuracion especifica de OBS:
- Facecam en esquina superior izquierda (310x170 px en posicion 0,140).
- Gameplay principal en zona derecha (640x720 px en posicion 340,0).
La adaptacion de estas coordenadas a otras configuraciones queda como
trabajo futuro (ver docs/trabajo_futuro.md seccion "Convertidor TikTok").
"""

from __future__ import annotations

import logging
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)

# Resolucion final TikTok / Reels / Shorts.
FINAL_WIDTH = 1080
FINAL_HEIGHT = 1920

# Coordenadas hardcoded de la camara facecam en el video origen.
CAMERA_X = 0
CAMERA_Y = 140
CAMERA_W = 310
CAMERA_H = 170

# Escalado de la camara en el output vertical.
CAMERA_SCALE = 2.0
SCALED_CAMERA_W = int(CAMERA_W * CAMERA_SCALE)
SCALED_CAMERA_H = int(CAMERA_H * CAMERA_SCALE)

# Posicion de la camara flotante en el output (centrada horizontal).
CAMERA_OVERLAY_X = (FINAL_WIDTH - SCALED_CAMERA_W) // 2
CAMERA_OVERLAY_Y = 250

# Coordenadas del gameplay.
GAMEPLAY_X = 340
GAMEPLAY_Y = 0
GAMEPLAY_W = 640
GAMEPLAY_H = 720

# Path al asset de mascara (forma redondeada de la facecam).
MASK_PATH = Path(__file__).parent / "assets" / "tiktok_mask.png"


def convert_to_tiktok(input_path: str, output_path: str) -> None:
    """Convierte un clip horizontal en formato vertical TikTok 9:16.

    Args:
        input_path: ruta al MP4 horizontal de entrada.
        output_path: ruta donde escribir el MP4 vertical resultante.

    Raises:
        FileNotFoundError: si la mascara o el input no existen.
        subprocess.CalledProcessError: si ffmpeg falla.
    """
    if not MASK_PATH.exists():
        raise FileNotFoundError(
            f"Mascara TikTok no encontrada en {MASK_PATH}. "
            "Asegurate de tenerla en backend/detector/assets/."
        )

    # Duracion del input para sincronizar el "loop 1" de la mascara
    # (la imagen se repite tantos segundos como dure el video).
    duracion_cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        input_path,
    ]
    duracion = subprocess.check_output(duracion_cmd).decode().strip()

    # Pipeline ffmpeg en una sola pasada:
    # 1) Crop del gameplay y escalado a 1080x1920.
    # 2) Crop de la facecam y escalado a 2x.
    # 3) Aplicar mascara alpha sobre la facecam.
    # 4) Overlay de la facecam sobre el gameplay vertical.
    filter_complex = (
        f"[0:v]crop={GAMEPLAY_W}:{GAMEPLAY_H}:{GAMEPLAY_X}:{GAMEPLAY_Y},"
        f"scale={FINAL_WIDTH}:{FINAL_HEIGHT},setsar=1[game];"
        f"[0:v]crop={CAMERA_W}:{CAMERA_H}:{CAMERA_X}:{CAMERA_Y},"
        f"scale={SCALED_CAMERA_W}:{SCALED_CAMERA_H},setsar=1[camraw];"
        f"[1:v]format=rgba,scale={SCALED_CAMERA_W}:{SCALED_CAMERA_H}[mask];"
        f"[camraw][mask]alphamerge[cam];"
        f"[game][cam]overlay={CAMERA_OVERLAY_X}:{CAMERA_OVERLAY_Y}:format=auto[v]"
    )

    cmd = [
        "ffmpeg", "-y",  # sobreescribir si existe
        "-i", input_path,
        "-loop", "1", "-t", duracion, "-i", str(MASK_PATH),
        "-filter_complex", filter_complex,
        "-map", "[v]",
        "-map", "0:a?",  # audio opcional (no toda la grabacion lo tiene)
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "18",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        output_path,
    ]

    logger.info("convert_to_tiktok: %s -> %s (dur=%ss)", input_path, output_path, duracion)
    subprocess.run(cmd, check=True, capture_output=True)
    logger.info("convert_to_tiktok: completado %s", output_path)


__all__ = ["convert_to_tiktok"]
