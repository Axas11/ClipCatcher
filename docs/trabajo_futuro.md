# Trabajo futuro — ClipCatcher

> Componentes y funcionalidades que **no** se han implementado en el MVP entregable
> del TFG (entrega 2026-05-10) y que quedan reservados para una siguiente iteración
> orientada a producción.
>
> El criterio para todos los recortes ha sido el mismo: **priorizar un flujo
> end-to-end demostrable** (login → subir vídeo → procesar con la CNN → listar y
> reproducir clips) frente a la arquitectura completa descrita en la propuesta
> original. La arquitectura "completa" sigue siendo la dirección a la que apunta
> el proyecto.

---

## Infraestructura

### Docker y docker-compose
- **Estado MVP:** No se usa. Todo se ejecuta localmente con `python` y `uvicorn`.
- **Justificación:** Para una demo grabada en una máquina local, Docker añade
  fricción (instalación, healthchecks, puertos) sin aportar valor visible.
- **Plan futuro:** Empaquetar backend y worker en imágenes separadas, orquestar
  con `docker-compose` (servicios: backend, worker, mysql, redis, nginx) y
  preparar despliegue reproducible para cloud.

### Nginx como reverse proxy
- **Estado MVP:** FastAPI sirve el frontend estático directamente con `StaticFiles`.
- **Justificación:** En local no hace falta un proxy delante. Un solo proceso
  basta para la demo.
- **Plan futuro:** Nginx delante (TLS, compresión, cache de estáticos, rate
  limiting) cuando el proyecto se publique en un dominio real.

---

## Persistencia y procesamiento

### MySQL
- **Estado MVP:** Se usa **SQLite** (`backend/data/clipcatcher.db`).
- **Justificación:** SQLite es cero-configuración, no necesita servidor ni
  contraseñas y permite que el evaluador clone, instale dependencias y arranque
  sin más. MySQL exige levantar un servicio aparte y gestionar credenciales.
- **Plan futuro:** Migrar a MySQL al pasar a producción. La capa SQLAlchemy
  hace que el cambio sea casi transparente: bastaría con cambiar `DATABASE_URL`
  y revisar tipos específicos.

### Alembic (migraciones)
- **Estado MVP:** Las tablas se crean al arrancar con
  `Base.metadata.create_all(engine)`.
- **Justificación:** Solo hay un usuario (yo) y la BD se reconstruye en cada
  arranque del entorno de demo. Migraciones añaden complejidad innecesaria.
- **Plan futuro:** Inicializar Alembic, generar la primera migración a partir
  del schema actual y a partir de ahí versionar todos los cambios de modelo.

### Redis + RQ (cola de tareas)
- **Estado MVP:** Se usa `BackgroundTasks` de FastAPI.
- **Justificación:** Para una demo con un único usuario subiendo un vídeo a la
  vez, una cola distribuida sobra. `BackgroundTasks` desacopla la respuesta
  HTTP del procesamiento sin necesidad de infraestructura extra.
- **Plan futuro:** Mover el procesamiento a un worker independiente con
  Redis + RQ (o Celery). Esto permite escalar workers en horizontal, prioridades
  por plan de usuario y reintentos automáticos.

---

## Autenticación

### Google OAuth
- **Estado MVP:** Login y registro con email + contraseña, JWT firmado con
  `python-jose`.
- **Justificación:** Google OAuth requiere crear un proyecto en Google Cloud
  Console, configurar pantalla de consentimiento, gestionar `client_id` /
  `client_secret`, y manejar callbacks. Para una demo defendible, el usuario y
  contraseña con JWT es suficiente y se valida igual de bien.
- **Plan futuro:** Añadir Google OAuth como método adicional (no exclusivo) de
  autenticación, manteniendo email+password como fallback.

---

## Análisis de contenido

### Whisper (audio)
- **Estado MVP:** Solo detección visual con la CNN ResNet18 sobre el killfeed.
- **Justificación:** Whisper descarga modelos de 75 MB - 1.5 GB y aumenta
  notablemente el tiempo de procesamiento por vídeo. Para el TFG, la detección
  visual ya demuestra el flujo completo y es el componente diferenciador.
- **Plan futuro:** Whisper como módulo **opt-in** que el usuario activa por
  vídeo. Combinaría transcripción (búsqueda por palabras clave) con detección
  de picos de energía vía librosa para localizar momentos relevantes.

---

## Negocio y monetización

### Sistema de créditos, planes y suscripciones
- **Estado MVP:** No existe. Un usuario, sin límites, sin pagos.
- **Justificación:** Es trabajo de producto, no de TFG. Un sistema de créditos
  serio implica integración con pasarela de pago, lógica de facturación, y
  gestión de estados de suscripción — todo ello fuera del alcance académico.
- **Plan futuro:** Modelo `Plan`, `Subscription` y `CreditLedger`. Cuotas por
  plan: tamaño máximo de subida (free 2 GB / premium 10 GB), prioridad de cola,
  marca de agua en plan free, acceso a Whisper solo en premium.

---

## Frontend

### React / TypeScript / Tailwind / shadcn
- **Estado MVP:** Frontend en **HTML/CSS/JS plano**, 4 páginas (login,
  dashboard, upload, detalle de vídeo), tema dark + neón. Los archivos React
  generados por la herramienta tipo Lovable/Dyad se han eliminado del repo
  (commits `chore: eliminar scaffolding React/Vite generado` y siguientes).
- **Justificación:** El alcance del TFG no requiere SPA. HTML/CSS/JS directo
  reduce la superficie técnica que defender, encaja con los contenidos del
  ciclo (DAW) y se desarrolla más rápido que un SPA con build pipeline.
- **Plan futuro:** Reescribir el frontend en React + Vite + TypeScript si el
  proyecto evoluciona, reutilizando los endpoints actuales del backend.

---

## Calidad

### Tests automatizados
- **Estado MVP:** Sin cobertura de tests. Verificación manual end-to-end.
- **Justificación:** Tiempo limitado; se prioriza tener el flujo funcionando.
- **Plan futuro:** Tests unitarios con `pytest` para utilidades y servicios,
  tests de integración con `httpx.AsyncClient` para los endpoints, fixture de
  BD SQLite en memoria, y un test de humo del detector con un mp4 corto.

### Logging estructurado y observabilidad
- **Estado MVP:** `logging` estándar de Python a stdout.
- **Plan futuro:** Logs en JSON, correlación por `request_id`, métricas de
  procesamiento (tiempo medio por minuto de vídeo, tasa de fallos del
  detector), y un dashboard básico (Prometheus + Grafana) si se llega a cloud.

---

## Resumen ejecutivo

| Componente | MVP entregable | Producción objetivo |
|---|---|---|
| Orquestación | `python` + `uvicorn` local | Docker Compose |
| Reverse proxy | — (FastAPI sirve estáticos) | Nginx |
| BD | SQLite | MySQL |
| Migraciones | `create_all` al arrancar | Alembic |
| Cola | `BackgroundTasks` | Redis + RQ |
| Auth | Email + password + JWT | + Google OAuth |
| Análisis visual | CNN ResNet18 (killfeed) | Igual |
| Análisis audio | — | Whisper + librosa (opt-in) |
| Frontend | HTML/CSS/JS plano | React + Vite (opcional) |
| Negocio | Sin créditos / sin planes | Modelo de suscripción |
| Tests | Verificación manual | `pytest` + integración |

El MVP cumple el flujo demostrable; cada fila de la tabla es un eje
independiente de evolución hacia la arquitectura objetivo.
