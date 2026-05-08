import os
from video_analizador import analizar_video_temporal

INPUT_DIR = "videos"

def procesar_video(video_path):
    print(f"🎬 Procesando: {video_path}")
    analizar_video_temporal(video_path)
    print("✅ Procesado correctamente.\n")

def main():
    if not os.path.exists(INPUT_DIR):
        os.makedirs(INPUT_DIR)
        print(f"✅ Carpeta creada: {INPUT_DIR}")
        print("🔹 Coloca tus videos en esta carpeta y vuelve a ejecutar el programa.")
        return

    videos = [
        f for f in os.listdir(INPUT_DIR)
        if f.lower().endswith((".mp4", ".avi", ".mov", ".mkv"))
    ]

    if not videos:
        print("⚠️ No hay videos por procesar en la carpeta 'videos/'.")
        return

    for video in videos:
        video_path = os.path.join(INPUT_DIR, video)
        procesar_video(video_path)

if __name__ == "__main__":
    main()
