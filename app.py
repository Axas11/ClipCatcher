import tkinter as tk
from tkinter import messagebox, scrolledtext
import os
import threading
import subprocess
import sys

INPUT_DIR = "videos"
CLIPS_DIR = "clips"

def procesar_videos(log_area):
    videos = [
        f for f in os.listdir(INPUT_DIR)
        if f.lower().endswith((".mp4", ".avi", ".mov", ".mkv"))
    ]

    if not videos:
        messagebox.showinfo("Info", "No hay videos por procesar en la carpeta 'videos'.")
        return

    for video in videos:
        video_path = os.path.join(INPUT_DIR, video)
        log_area.insert(tk.END, f"🎬 Procesando: {video}\n")
        log_area.see(tk.END)

        # Aquí llamamos al procesamiento
        from video_analizador import analizar_video_temporal
        analizar_video_temporal(video_path)

        log_area.insert(tk.END, f"✅ Procesado: {video}\n")
        log_area.see(tk.END)

    messagebox.showinfo("Listo", "Todos los videos fueron procesados.")

def procesar_thread(log_area):
    threading.Thread(target=procesar_videos, args=(log_area,), daemon=True).start()

def abrir_clips():
    path = os.path.abspath(CLIPS_DIR)
    if sys.platform == "win32":
        os.startfile(path)
    elif sys.platform == "darwin":
        subprocess.Popen(["open", path])
    else:
        subprocess.Popen(["xdg-open", path])

def main():
    if not os.path.exists(INPUT_DIR):
        os.makedirs(INPUT_DIR)
    if not os.path.exists(CLIPS_DIR):
        os.makedirs(CLIPS_DIR)

    root = tk.Tk()
    root.title("Clip Extractor IA")
    root.geometry("500x400")

    tk.Label(root, text="Clip Extractor IA", font=("Arial", 16)).pack(pady=10)

    btn_procesar = tk.Button(root, text="Procesar videos", command=lambda: procesar_thread(log_area))
    btn_procesar.pack(pady=5)

    btn_abrir = tk.Button(root, text="Abrir carpeta de clips", command=abrir_clips)
    btn_abrir.pack(pady=5)

    log_area = scrolledtext.ScrolledText(root, width=60, height=15)
    log_area.pack(pady=10)

    tk.Label(root, text="Coloca los videos en la carpeta 'videos' antes de procesar.").pack(pady=5)

    root.mainloop()

if __name__ == "__main__":
    main()
