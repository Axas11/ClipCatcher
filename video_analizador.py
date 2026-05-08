import cv2
import torch
import json
import os
import sys
from PIL import Image
from torchvision import transforms
from torchvision.models import resnet18
from utils import guardar_clip

# Detectar si estamos en un ejecutable PyInstaller o en desarrollo
if getattr(sys, 'frozen', False):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Cargar configuración
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")
with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    config = json.load(f)

margen = config.get("margen_clip", 2)
duracion = config.get("duracion_clip", 6)
ventana_encadenado = 6

# Modelo y transformaciones
transform = transforms.Compose([
    transforms.Resize((128, 128)),
    transforms.ToTensor()
])

MODEL_PATH = os.path.join(BASE_DIR, "model", "kill_detector.pt")
model = resnet18(weights=None)
model.fc = torch.nn.Linear(model.fc.in_features, 2)
model.load_state_dict(torch.load(MODEL_PATH, map_location="cpu"))
model.eval()

def predecir_img(cv_img):
    img_pil = Image.fromarray(cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB))
    tensor = transform(img_pil).unsqueeze(0)
    with torch.no_grad():
        salida = model(tensor)
        clase = torch.argmax(salida, dim=1).item()
    return clase == 0  # 0 es KILL

def analizar_video_temporal(ruta_video):
    cap = cv2.VideoCapture(ruta_video)
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_actual = 0
    frame_interval = int(fps)
    inicio_clip = None
    fin_clip = None

    nombre_base = os.path.splitext(os.path.basename(ruta_video))[0]
    carpeta_clips = os.path.join("clips", nombre_base)
    os.makedirs(carpeta_clips, exist_ok=True)

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        if frame_actual % frame_interval == 0:
            h, w = frame.shape[:2]
            x1, y1 = int(w * 0.70), int(h * 0.01)
            x2, y2 = int(w * 0.995), int(h * 0.15)
            roi = frame[y1:y2, x1:x2]

            if predecir_img(roi):
                tiempo = frame_actual / fps
                if inicio_clip is None:
                    inicio_clip = max(0, tiempo - margen)
                    fin_clip = tiempo + duracion
                elif tiempo <= fin_clip + ventana_encadenado:
                    fin_clip = tiempo + duracion
                else:
                    output_name = f"clip_{int(inicio_clip)}"
                    output_path = os.path.join(carpeta_clips, output_name)
                    guardar_clip(ruta_video, inicio_clip, output_path, fin_clip - inicio_clip)
                    inicio_clip = max(0, tiempo - margen)
                    fin_clip = tiempo + duracion

        frame_actual += 1

    if inicio_clip is not None:
        output_name = f"clip_{int(inicio_clip)}"
        output_path = os.path.join(carpeta_clips, output_name)
        guardar_clip(ruta_video, inicio_clip, output_path, fin_clip - inicio_clip)

    cap.release()
