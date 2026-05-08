# Backend ClipCatcher

API FastAPI del MVP. Persistencia en SQLite, sin Docker.

## Arranque local

```powershell
# 1. Crear y activar el entorno virtual desde la raiz del repo
python -m venv .venv
.venv\Scripts\Activate.ps1

# 2. Instalar dependencias
pip install -r backend/requirements.txt

# 3. Crear el archivo de variables de entorno
Copy-Item backend/.env.example backend/.env
# Editar backend/.env y reemplazar APP_SECRET_KEY y JWT_SECRET_KEY por valores reales.

# 4. Arrancar la API
cd backend
uvicorn app.main:app --reload
```

La API queda en `http://127.0.0.1:8000`. Endpoints utiles:

- `GET /health` → `{"status":"ok"}`
- `GET /docs` → Swagger UI interactivo

Al primer arranque se crean automaticamente:

- `backend/data/clipcatcher.db` (BD SQLite)
- `backend/data/storage/videos/` y `backend/data/storage/clips/`

## Notas

- El archivo `.env` esta gitignorado y nunca debe subirse al repo.
- `torch` y `torchvision` solo son necesarios a partir de la fase F4 (motor de
  deteccion). Para trabajar solo en el backend basta con instalar las cuatro
  primeras secciones de `requirements.txt`.
