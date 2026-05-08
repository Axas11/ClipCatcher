# ClipCatcher

> **TFG · Francisco José Rodríguez Guerra · 2º DAW · 2025-2026**

Plataforma web que detecta automáticamente highlights en partidas de Valorant
y genera clips cortos listos para compartir. El usuario sube una grabación
larga, una CNN entrenada a medida analiza el killfeed frame a frame, y el
backend exporta cada momento detectado como un MP4 reproducible y descargable
desde el navegador.

## Stack del MVP

| Capa | Tecnología |
|---|---|
| Backend | Python 3.13 · [FastAPI](https://fastapi.tiangolo.com/) 0.115 · [SQLAlchemy](https://www.sqlalchemy.org/) 2.0 · [Pydantic](https://docs.pydantic.dev/) 2.9 |
| Base de datos | SQLite (un archivo en `backend/data/clipcatcher.db`) |
| Autenticación | Email + contraseña · JWT (`python-jose` + `passlib`/`bcrypt`) |
| Procesamiento asíncrono | `BackgroundTasks` de FastAPI |
| Detección visual | [PyTorch](https://pytorch.org/) 2.7.1 · `torchvision` 0.22.1 · ResNet18 con head binario kill/no-kill (modelo entrenado a medida) |
| Edición | `ffmpeg` invocado por `subprocess` (H.264 + AAC) |
| Frontend | HTML / CSS / JavaScript ES modules · tema dark + neón cian/morado |
| Servidor | `uvicorn` local · FastAPI sirve también el frontend con `StaticFiles` |

La arquitectura completa del proyecto (Docker, MySQL, Redis + RQ, Nginx, Google
OAuth, Whisper, sistema de planes, editor estilo TikTok, etc.) queda
documentada como evolución posterior en
[`docs/trabajo_futuro.md`](docs/trabajo_futuro.md).

## Estructura del repo

```
ClipCatcher/
├── backend/
│   ├── app/
│   │   ├── api/             # Routers HTTP: auth, users, videos, clips
│   │   ├── core/            # config (Settings), security (JWT/hash), deps
│   │   ├── db/              # engine SQLAlchemy + base + get_db
│   │   ├── models/          # User, Video, Clip
│   │   ├── schemas/         # Pydantic
│   │   ├── services/        # processor (orquesta el detector)
│   │   └── main.py          # punto de entrada FastAPI
│   ├── detector/            # motor de visión por computador
│   │   ├── analyzer.py      # analyze_video(path) -> list[(start, end)]
│   │   ├── exporter.py      # export_clip(path, start, end, output)
│   │   ├── config.json      # margen y duración de los clips
│   │   └── model/
│   │       └── kill_detector.pt   (43 MB, versionado)
│   ├── data/                # SQLite + storage de vídeos y clips (gitignored)
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── index.html           # login y registro
│   ├── dashboard.html       # listado de vídeos del usuario
│   ├── upload.html          # subida con barra de progreso
│   ├── video.html           # detalle + clips reproducibles
│   ├── css/styles.css
│   └── js/{api.js,auth.js}
├── docs/
│   ├── trabajo_futuro.md    # qué quedó fuera del MVP y por qué
│   └── arquitectura.md      # diagrama del flujo end-to-end
└── README.md
```

## Requisitos

- **Python 3.13** (probado en 3.13.13 sobre Windows 11).
- **`ffmpeg`** accesible en el `PATH`. En Windows, instalarlo con
  [Chocolatey](https://community.chocolatey.org/packages/ffmpeg)
  (`choco install ffmpeg`) o [descargarlo](https://www.gyan.dev/ffmpeg/builds/)
  y añadirlo al `PATH` manualmente. Comprobar con `ffmpeg -version`.
- **`git`** para clonar el repo.

## Arranque local paso a paso

```powershell
# 1. Clonar el repo
git clone https://github.com/Axas11/ClipCatcher.git
cd ClipCatcher

# 2. Crear y activar un entorno virtual
python -m venv .venv
.\.venv\Scripts\Activate.ps1   # Windows PowerShell
# source .venv/bin/activate    # Linux / macOS

# 3. Instalar dependencias del backend
pip install -r backend\requirements.txt

# 4. Crear el archivo .env del backend a partir del ejemplo
copy backend\.env.example backend\.env
# Reemplazar APP_SECRET_KEY y JWT_SECRET_KEY por valores reales:
python -c "import secrets; print('APP_SECRET_KEY/JWT_SECRET_KEY ->', secrets.token_urlsafe(48))"

# 5. Arrancar el backend (sirve también el frontend en /)
cd backend
uvicorn app.main:app --reload
```

El backend arranca en `http://127.0.0.1:8000`. Al iniciar, el evento
`lifespan` crea automáticamente:

- `backend/data/clipcatcher.db` con las tablas `users`, `videos` y `clips`.
- `backend/data/storage/videos/` y `backend/data/storage/clips/`.

### Usar la aplicación

1. Abrir [http://127.0.0.1:8000/](http://127.0.0.1:8000/) en el navegador.
2. **Crear cuenta** con email + contraseña (mínimo 8 caracteres).
3. **Subir vídeo** desde el dashboard (formatos `.mp4`, `.mkv`, `.mov`, …).
4. La página de detalle hace polling cada 5 s mostrando `processing → done`.
   El procesamiento de un clip de ~30 s a 720p tarda **~7 s** en CPU.
5. **Reproducir y descargar** los clips generados.

### API

La documentación interactiva (Swagger UI) está en
[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) y permite probar
todos los endpoints sin frontend.

| Método | Ruta | Descripción |
|---|---|---|
| `POST` | `/api/auth/register` | Registra un usuario y devuelve `user` + `token` |
| `POST` | `/api/auth/login` | OAuth2 password flow (form-encoded) → `Token` |
| `GET` | `/api/users/me` | Datos del usuario autenticado |
| `POST` | `/api/videos` | Sube un vídeo (multipart) y encola su procesamiento |
| `GET` | `/api/videos` | Lista los vídeos del usuario |
| `GET` | `/api/videos/{id}` | Detalle del vídeo + clips |
| `GET` | `/api/clips/{id}/download` | Descarga el clip (Content-Disposition: attachment) |
| `GET` | `/api/clips/{id}/stream` | Sirve el clip inline para `<video>` |
| `GET` | `/api/health` | Healthcheck (`{"status":"ok"}`) |

## Troubleshooting

### `pip install` falla con `Could not find a version that satisfies the requirement torch==2.7.1`

Asegúrate de usar Python 3.13. Para versiones anteriores (3.10, 3.11, 3.12)
hay que ajustar los pins de `torch` y `torchvision` en
[`backend/requirements.txt`](backend/requirements.txt).

### `pip install torch` tarda mucho o se queda colgado

`torch` 2.7.1 + `torchvision` 0.22.1 ocupan ~750 MB. La descarga puede
tardar varios minutos en conexiones lentas. Es CPU-only por defecto, lo
cual es suficiente para el MVP (la inferencia de un clip de 30 s tarda
~2.4 s en CPU).

### `ffmpeg: command not found` al exportar clips

`export_clip` usa `subprocess.run(["ffmpeg", ...])` y necesita que `ffmpeg`
esté en el `PATH`. Verificar con `ffmpeg -version`. En Windows, tras
instalar con Chocolatey, abrir una terminal nueva.

### El servidor arranca pero `/api/health` devuelve `Internal Server Error`

Probablemente falta el archivo `backend/.env`. El backend necesita al
menos `APP_SECRET_KEY` y `JWT_SECRET_KEY` definidos. Crear `.env` a
partir de `.env.example` y rellenarlos.

### Subida de un vídeo grande devuelve `413 Payload Too Large`

El límite por defecto es 10 GiB (`MAX_UPLOAD_BYTES=10737418240`).
Editar `backend/.env` para subirlo si fuese necesario y reiniciar uvicorn
(la configuración se cachea con `lru_cache`).

### El detector procesa en CPU y es lento

El stack está pinneado a las builds CPU de PyTorch (`torch==2.7.1` y
`torchvision==0.22.1` con sufijo `+cpu`). Para usar GPU, instalar
manualmente las builds CUDA de la
[matriz oficial de PyTorch](https://pytorch.org/get-started/locally/) y
reinstalar `torchvision` compatible. La aceleración GPU queda fuera del
MVP.

## Licencia

Este repositorio se entrega como TFG de Francisco José Rodríguez Guerra
para el ciclo Desarrollo de Aplicaciones Web (DAW) en el curso 2025-2026.
El uso académico, evaluador y de aprendizaje está permitido. Cualquier
otro uso requiere consentimiento del autor.
