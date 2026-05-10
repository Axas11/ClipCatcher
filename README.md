# ClipCatcher

> **TFG · Francisco José Rodríguez Guerra · 2º DAW · 2025-2026**

ClipCatcher detecta automáticamente highlights en partidas de Valorant
usando una CNN entrenada a medida sobre el killfeed. El usuario sube
una grabación, el detector visual marca los frames con kill, los
agrupa en ventanas multikill, y exporta cada highlight como un MP4
horizontal listo para descargar. Opcionalmente puede generar también
una variante vertical 9:16 para TikTok / Reels / Shorts.

## Features

- **Detección visual** con ResNet-18 entrenada sobre un dataset propio
  del killfeed de Valorant. Sin OCR genérico.
- **Encadenamiento de kills**: detecciones consecutivas dentro de una
  ventana configurable se agrupan en un mismo clip multikill en lugar
  de fragmentarse en varios.
- **Configuración por vídeo**: ventana de encadenamiento, margen y
  duración del clip se pueden ajustar individualmente desde la
  pantalla de subida sin modificar la configuración por defecto del
  usuario.
- **Conversor a vertical 9:16** opcional, con la facecam superpuesta
  sobre una máscara redondeada y el gameplay reescalado al canvas
  vertical. Las coordenadas de crop son fijas para el setup de OBS
  del autor — ver [Limitaciones](#limitaciones-del-mvp).
- **Auth dual**: email + contraseña con bcrypt + JWT, o Google OAuth
  vía `authlib`. La integración con Google es opcional: si las
  credenciales no están en `.env`, el botón se oculta y el endpoint
  responde 503.
- **Recuperación de contraseña por email** con token UUID single-use
  TTL 1h vía Gmail SMTP. Solo aplica a cuentas email+password
  (las cuentas Google las gestiona Google). Si el SMTP no está
  configurado, el endpoint sigue devolviendo 200 (anti-enumeration)
  pero registra el link en logs en lugar de enviarlo.
- **Frontend HTML/CSS/JS sin frameworks**: 7 páginas (landing
  comercial, login/registro, dashboard, upload, detalle de vídeo,
  cuenta, reset-password) con tema dark + neón cian/morado, tipografía
  Inter + Geist Sans, e iconos Lucide vía CDN.
- **Backend FastAPI + SQLAlchemy + SQLite** con procesamiento
  asíncrono via `BackgroundTasks`. ~21 endpoints bajo `/api/*` más el
  catch-all 404 que devuelve JSON para `/api/...` y la página HTML
  personalizada para el resto.

## Stack

| Capa | Tecnología |
|---|---|
| Backend | Python 3.13 · FastAPI 0.115 · SQLAlchemy 2.0 · Pydantic 2.9 |
| Base de datos | SQLite (`backend/data/clipcatcher.db`) |
| Autenticación | bcrypt + JWT (`python-jose`) o Google OAuth (`authlib`) |
| Email | `smtplib` con SSL (Gmail SMTP en la configuración por defecto) |
| Procesamiento | `BackgroundTasks` de FastAPI |
| Detección visual | PyTorch 2.7.1 + torchvision 0.22.1 (CPU) · ResNet-18 con head binario kill / no-kill |
| Edición de clips | `ffmpeg` invocado por `subprocess` (H.264 + AAC) |
| Conversor 9:16 | `ffmpeg` filter_complex en una pasada (crop + scale + alphamerge + overlay) |
| Frontend | HTML5 / CSS vanilla / JavaScript ES modules |
| Servidor | `uvicorn` local (FastAPI sirve también el frontend con `StaticFiles`) |

## Estructura del repo

```
ClipCatcher/
├── backend/
│   ├── app/
│   │   ├── api/                   # auth, oauth, users, videos, clips, stats
│   │   ├── core/                  # config, security (JWT/hash), deps
│   │   ├── db/                    # engine + Base + get_db
│   │   ├── models/                # User, Video, Clip, PasswordResetToken
│   │   ├── schemas/               # Pydantic
│   │   ├── services/
│   │   │   ├── processor.py       # orquesta analyze + export + tiktok
│   │   │   └── email_service.py   # SMTP best-effort
│   │   └── main.py
│   ├── detector/
│   │   ├── analyzer.py            # analyze_video(path) -> list[(start, end)]
│   │   ├── exporter.py            # export_clip(path, start, end, output)
│   │   ├── tiktok_exporter.py     # convert_to_tiktok(input, output) — 9:16
│   │   ├── config.json            # margen y duración por defecto
│   │   ├── assets/
│   │   │   └── tiktok_mask.png    # máscara redondeada de la facecam
│   │   └── model/
│   │       └── kill_detector.pt   (43 MB, versionado)
│   ├── data/                      # SQLite + storage de vídeos y clips (gitignored)
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── index.html                 # landing comercial + login/registro
│   ├── dashboard.html             # listado de vídeos del usuario
│   ├── upload.html                # subida con drop zone y configuración avanzada
│   ├── video.html                 # detalle + clips reproducibles
│   ├── account.html               # perfil + cambio de contraseña
│   ├── reset-password.html        # establecer nueva contraseña tras email
│   ├── 404.html
│   ├── css/styles.css
│   └── js/{api,auth,toast,modal,slider,animations}.js
├── docs/
│   ├── arquitectura.md            # vista general del flujo end-to-end
│   └── trabajo_futuro.md          # qué falta y por qué
└── README.md
```

## Requisitos

- **Python 3.13** (probado en 3.13.13 sobre Windows 11).
- **`ffmpeg`** en el `PATH`. En Windows: `choco install ffmpeg` o
  [descarga oficial](https://www.gyan.dev/ffmpeg/builds/) y añadir
  manualmente. Verificar con `ffmpeg -version`.
- **`git`**.

## Setup local

```powershell
# 1. Clonar
git clone https://github.com/Axas11/ClipCatcher.git
cd ClipCatcher

# 2. Entorno virtual
python -m venv .venv
.\.venv\Scripts\Activate.ps1      # Windows PowerShell
# source .venv/bin/activate       # Linux / macOS

# 3. Dependencias
pip install -r backend\requirements.txt

# 4. Crear .env a partir del ejemplo
copy backend\.env.example backend\.env

# 5. Generar secrets y rellenar APP_SECRET_KEY y JWT_SECRET_KEY
python -c "import secrets; print(secrets.token_urlsafe(48))"

# 6. Arrancar
cd backend
uvicorn app.main:app
```

El backend escucha en `http://127.0.0.1:8001` (o el puerto que pongas
con `--port`). Al iniciar, el evento `lifespan` crea
automáticamente:

- `backend/data/clipcatcher.db` con las tablas `users`, `videos`,
  `clips` y `password_reset_tokens`.
- `backend/data/storage/videos/` y `backend/data/storage/clips/`.

### Variables de entorno

`.env` lleva las siguientes claves. **Solo `APP_SECRET_KEY` y
`JWT_SECRET_KEY` son obligatorias para arrancar; el resto son
opcionales y degradan la funcionalidad correspondiente si faltan.**

| Variable | Obligatoria | Descripción |
|---|---|---|
| `APP_SECRET_KEY` | sí | Firma de cookies de sesión (la usa OAuth para el state CSRF). Generar con `secrets.token_urlsafe(48)`. |
| `JWT_SECRET_KEY` | sí | Firma de los JWT de autenticación. Mismo método. |
| `DATABASE_URL` | no | Default `sqlite:///./data/clipcatcher.db`. |
| `MAX_UPLOAD_BYTES` | no | Default 10 GiB. |
| `FRONTEND_URL` | no | Base URL para los links que se mandan por email. Default `http://127.0.0.1:8001`. |
| `GOOGLE_CLIENT_ID` | no | OAuth Client ID de Google Cloud. Si está vacío, el botón "Continuar con Google" se oculta. |
| `GOOGLE_CLIENT_SECRET` | no | Idem. Necesario solo si `GOOGLE_CLIENT_ID` está. |
| `GOOGLE_REDIRECT_URI` | no | Default `http://127.0.0.1:8001/api/auth/google/callback`. Tiene que coincidir con el que has autorizado en la consola de Google. |
| `SMTP_HOST` | no | Default `smtp.gmail.com`. |
| `SMTP_PORT` | no | Default `465` (SSL). |
| `SMTP_USER` | no | Email remitente. Si está vacío, los emails de reset no se envían y el endpoint solo loggea el link. |
| `SMTP_PASSWORD` | no | App Password de Gmail (no la contraseña de la cuenta). [Cómo generarla](https://myaccount.google.com/apppasswords). |

`backend/.env` está en `.gitignore` y nunca debe commitearse.
`backend/.env.example` es el template inicial y sí está versionado.

## Usar la aplicación

1. Abrir `http://127.0.0.1:8001/`.
2. Crear cuenta con email + contraseña (mínimo 8 caracteres) o, si
   has configurado las credenciales de Google, "Continuar con Google".
3. **Subir un vídeo** desde el dashboard. El bloque "Configuración
   avanzada (opcional)" permite ajustar la sensibilidad del detector
   solo para esta subida y activar la generación de la variante
   vertical TikTok.
4. La página de detalle hace polling cada 5 s y pasa de `processing`
   a `done` cuando termina. Para `clip_18458.mp4` (29 s, 720p) el
   procesamiento tarda ~7 s en CPU; con la variante TikTok activada,
   ~9 s adicionales por clip.
5. **Reproducir y descargar** los clips. Si activaste TikTok, cada
   clip muestra dos botones: "Descargar (16:9)" y "Descargar TikTok
   (9:16)".

### Recuperación de contraseña

En la pantalla de login, "¿Olvidaste tu contraseña?" abre un modal
para introducir el email. Si la cuenta existe y es email+password, se
envía un link de reset con TTL 1h al inbox del usuario. El endpoint
devuelve 200 sin importar si el email existe (anti-enumeration);
los emails de cuentas Google y los inexistentes se ignoran
silenciosamente.

### API

Documentación interactiva (Swagger) en `http://127.0.0.1:8001/docs`.
Endpoints principales:

| Método | Ruta | Auth | Descripción |
|---|---|---|---|
| `POST` | `/api/auth/register` | — | Crea cuenta email+password y devuelve JWT |
| `POST` | `/api/auth/login` | — | OAuth2 password flow (form-encoded) |
| `POST` | `/api/auth/forgot-password` | — | Solicita email de reset (200 siempre) |
| `POST` | `/api/auth/reset-password` | — | Consume token y actualiza contraseña |
| `GET` | `/api/auth/google/login` | — | Inicia flujo OAuth Google (redirect) |
| `GET` | `/api/auth/google/callback` | — | Callback OAuth → JWT propio |
| `GET` | `/api/auth/google/available` | — | Indica si Google OAuth está configurado |
| `GET` | `/api/users/me` | JWT | Datos del usuario actual |
| `PATCH` | `/api/users/me` | JWT | Actualiza nombre y/o email |
| `PUT` | `/api/users/me/password` | JWT | Cambia contraseña (solo email+password) |
| `GET` / `PUT` | `/api/users/me/settings` | JWT | Lee / actualiza defaults del detector |
| `GET` | `/api/users/me/stats` | JWT | Agregados del usuario |
| `GET` | `/api/users/me/activity` | JWT | Timeline de eventos recientes |
| `POST` | `/api/videos` | JWT | Sube vídeo (multipart) y encola procesamiento |
| `GET` | `/api/videos` | JWT | Lista vídeos del usuario |
| `GET` | `/api/videos/{id}` | JWT | Detalle + clips |
| `DELETE` | `/api/videos/{id}` | JWT | Borra vídeo y todos sus clips (BD + disco) |
| `GET` | `/api/clips/{id}/download` | JWT | Descarga clip horizontal 16:9 |
| `GET` | `/api/clips/{id}/stream` | JWT | Sirve clip inline para `<video>` (con Range) |
| `GET` | `/api/clips/{id}/tiktok` | JWT | Descarga variante 9:16 si fue generada (404 si no) |
| `GET` | `/api/stats/global` | — | Agregados anónimos para la landing pública |
| `GET` | `/api/health` | — | Healthcheck |

## Limitaciones del MVP

- **Conversor TikTok hardcoded.** Las coordenadas de crop (facecam
  310×170 en (0, 140), gameplay 640×720 en (340, 0)) están fijas
  para el setup de OBS del autor. En grabaciones con otra
  disposición, la facecam o el gameplay quedarán descuadrados. La
  configurabilidad por usuario está en
  [`docs/trabajo_futuro.md`](docs/trabajo_futuro.md).
- **SQLite como base de datos.** Funciona para un único usuario en
  local pero no para concurrencia real ni para producción. Postgres
  + Alembic está en el roadmap.
- **`BackgroundTasks` como cola.** Bloquea CPU del proceso
  principal mientras inferencia + ffmpeg corren. Para múltiples
  usuarios concurrentes hace falta Redis + RQ con workers
  separados.
- **Sin análisis de audio.** La detección es exclusivamente visual.
  Whisper para transcripción y librosa para picos de energía están
  contemplados como módulos opt-in pero no implementados.
- **Sin rate limiting.** Endpoints sensibles (`/auth/login`,
  `/auth/forgot-password`, `/videos` POST) no tienen límites por
  IP ni por usuario. Para abrir la app a usuarios reales hace falta
  añadirlo (ej. con `slowapi`).

## Troubleshooting

### `pip install` falla con `Could not find a version that satisfies torch==2.7.1`

Asegúrate de usar Python 3.13. Para 3.10–3.12 hay que ajustar los
pins de `torch` y `torchvision` en
[`backend/requirements.txt`](backend/requirements.txt).

### `pip install torch` tarda muchísimo

`torch` 2.7.1 + `torchvision` 0.22.1 ocupan ~750 MB. La descarga
puede tardar varios minutos en conexiones lentas. La build es
CPU-only por defecto, suficiente para inferencia (~2.4 s por clip
de 30 s).

### `ffmpeg: command not found` al exportar clips

`export_clip` y `convert_to_tiktok` usan `subprocess.run(["ffmpeg",
...])` y necesitan que `ffmpeg` esté en el `PATH`. En Windows tras
instalar con Chocolatey hay que abrir una terminal nueva.

### El email de reset no llega

Tres causas posibles. (1) `SMTP_USER` / `SMTP_PASSWORD` están
vacíos en `.env`: el endpoint loggea el link a stdout y vuelves a
mirar la consola del backend. (2) El `SMTP_PASSWORD` no es una App
Password sino la contraseña de la cuenta de Google: Gmail rechaza
el login con error claro en logs. (3) Va a Spam: pasa la primera
vez con cualquier dominio sin reputación, marca como No-Spam y los
siguientes llegan a la bandeja principal.

### Subida grande devuelve `413 Payload Too Large`

Default 10 GiB (`MAX_UPLOAD_BYTES=10737418240`). Si necesitas más,
edita `backend/.env` y reinicia uvicorn (la configuración se cachea
con `lru_cache`).

### El detector procesa lento

Pinneado a builds CPU de PyTorch (`torch==2.7.1+cpu`,
`torchvision==0.22.1+cpu`). Para usar GPU instala las builds CUDA
desde la [matriz oficial de PyTorch](https://pytorch.org/get-started/locally/)
y reinstala `torchvision` compatible. La aceleración GPU queda
fuera del MVP.

## Licencia

Este repositorio se entrega como TFG de Francisco José Rodríguez
Guerra para el ciclo Desarrollo de Aplicaciones Web (DAW) en el
curso 2025-2026. El uso académico, evaluador y de aprendizaje está
permitido. Cualquier otro uso requiere consentimiento del autor.
