import os
import subprocess

def guardar_clip(video_path, inicio, output_path_sin_extension, duracion):
    os.makedirs(os.path.dirname(output_path_sin_extension), exist_ok=True)
    output_path = f"{output_path_sin_extension}.mp4"
    print(f"💾 Guardando clip en: {output_path}")

    if duracion <= 0:
        print(f"⚠️ Duración inválida: {duracion}s — no se guardará el clip.")
        return

    try:
        cmd = [
            "ffmpeg",
            "-y",
            "-ss", str(inicio),
            "-i", video_path,
            "-t", str(duracion),
            "-c:v", "libx264",
            "-preset", "fast",
            "-c:a", "aac",
            "-strict", "experimental",  # asegúrate que AAC esté habilitado
            output_path
        ]
        subprocess.run(cmd, check=True)
        print("✅ Clip guardado correctamente con audio.")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error al guardar clip: {e}")
