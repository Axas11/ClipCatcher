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

## Modelo de detección visual y reglas de clip

### Pipeline de entrenamiento del modelo
- **Estado MVP:** El clasificador `kill_detector.pt` (ResNet18 con head binario)
  se entrenó **a mano** con un dataset propio de capturas del killfeed de
  Valorant, etiquetadas manualmente en dos carpetas (`kill/` y `no-kill/`).
  El proceso de entrenamiento, las hiperparámetros y la división train/val
  vivieron en un cuaderno/script puntual fuera del repo; en el MVP solo se
  usa el `.pt` resultante.
- **Justificación:** Para el TFG basta con un modelo congelado que demuestre
  el pipeline de inferencia y la cadena end-to-end. Reproducir el entrenamiento
  exigiría compartir el dataset (decenas de miles de imágenes), versionarlo, y
  documentar el setup de GPU — fuera del scope del MVP.
- **Plan futuro:**
  - Automatizar el pipeline en un script reproducible (`scripts/train.py` o
    similar): carga del dataset desde una ruta configurable, división
    train/val (estratificada), training loop con `torch` + `torchvision`,
    early stopping y guardado del mejor checkpoint en
    `backend/detector/model/`.
  - Reportar **precisión y recall** sobre un conjunto de validación
    independiente, además de matriz de confusión y curva PR. Estas métricas
    deben quedar versionadas (p.ej. `model_card.md` junto al `.pt`).
  - Ampliar el dataset con capturas de más partidas, más jugadores y más
    resoluciones; programar **reentrenamiento periódico** cuando el killfeed
    cambie de aspecto (parches del juego, eventos especiales).
  - Considerar exportar a ONNX para inferencia más rápida y portabilidad.

### Chain window configurable por usuario/juego
- **Estado MVP:** El parámetro `chain_window` (6 s) — la distancia máxima
  entre dos detecciones consecutivas para encadenarlas en un mismo clip — está
  hardcodeado como constante (`_CHAIN_WINDOW_S`) en
  `backend/detector/analyzer.py`. `config.json` solo expone `margen_clip` y
  `duracion_clip`.
- **Justificación:** El valor 6 s refleja la dinámica de Valorant (multikills
  típicas en menos de 6 s entre frags). Para el MVP no hay multi-juego ni
  perfiles de usuario, así que un único valor sirve.
- **Plan futuro:**
  - Mover `chain_window` a la configuración persistida (BD o `config.json`),
    con valores **por defecto distintos por juego** (Valorant 6 s, CS2 8 s,
    LoL 15 s, etc.). El detector recibiría el juego como argumento.
  - Permitir que cada usuario sobrescriba el valor en sus preferencias
    (estilo "highlights cortos punzantes" vs "clips narrativos largos").
  - Exponerlo en la UI de subida del frontend como un selector con presets
    por juego + override avanzado.
  - Aplicar el mismo principio a `margen_clip` y `duracion_clip`.

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

## Producto y experiencia de usuario

### Editor de clips estilo TikTok
- **Estado MVP:** No existe. Los clips se exportan tal cual los detecta el
  motor (recorte temporal, manteniendo la composición original 16:9), y se
  reproducen y descargan sin transformación adicional.
- **Justificación:** Un editor con composición vertical (facecam + gameplay
  apilados), subtítulos generados, y elementos visuales superpuestos exige
  un pipeline de edición de vídeo significativamente más complejo (timeline
  por capas, transcodificación, fuentes y assets) y multiplicaría el tiempo
  de implementación. Descartado del MVP en la decisión de scope.
- **Plan futuro:** Pipeline de edición server-side: capa de gameplay (recorte
  vertical 9:16 del centro), capa de facecam (overlay si el usuario sube su
  webcam), subtítulos auto-generados (Whisper, también en trabajo futuro),
  marca de agua opcional. Plantillas predefinidas por tipo de highlight
  (1v1, multikill, clutch). Edición no destructiva sobre el vídeo original.

### Configuración mínima de cuenta con ajuste de sensibilidad (F6X)
- **Estado MVP:** No hay panel de configuración. El umbral de detección y
  los parámetros del clipping (`margen_clip`, `duracion_clip`,
  `chain_window`) son globales y vienen del `config.json` del módulo
  `detector`.
- **Justificación:** Para validar el flujo end-to-end de la entrega no hace
  falta personalización. La sensibilidad por defecto funciona bien en los
  vídeos de prueba.
- **Plan futuro (F6X, programada para el fin de semana antes de la entrega):**
  Página `/account.html` con dos controles mínimos:
  - **Sensibilidad de detección** (slider o tres niveles preset:
    "Conservadora / Equilibrada / Generosa") que ajusta el umbral del
    clasificador binario antes de marcar un frame como kill.
  - **Margen y duración** del clip resultante.
  Persistencia en una nueva tabla `user_settings` ligada al `User`. El
  detector lee la configuración del usuario en lugar de la global cuando
  procesa cada vídeo. Si por tiempo no se llega, queda como primera tarea
  post-entrega.

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

## Edición de vídeo

### Convertidor TikTok configurable
- **Estado MVP (F13.2):** El usuario puede activar un checkbox al subir el
  vídeo para que ClipCatcher genere también la variante vertical 9:16 de
  cada clip detectado, con la facecam superpuesta sobre una máscara
  redondeada y centrada sobre el gameplay reescalado a 1080×1920. La
  conversión se hace en una sola pasada de `ffmpeg` con `filter_complex`,
  delegada en `backend/detector/tiktok_exporter.py`. Todas las coordenadas
  de crop están **hardcoded** para el setup específico de OBS del autor:
  - **Facecam**: 310×170 px en posición `(0, 140)`.
  - **Gameplay**: 640×720 px en posición `(340, 0)`.
  - Escalado de la facecam ×2, posición flotante centrada horizontalmente
    a `y = 250` sobre el canvas vertical.
  En grabaciones con otro layout estas coordenadas producen resultados
  descuadrados.
- **Justificación:** Para un MVP, "funciona para mi setup" es aceptable
  como prueba de concepto del pipeline. Hacerlo configurable requería
  diseño de UI específica (calibración visual o 8 inputs numéricos
  acoplados que se entiendan sin documentación) que se sale del alcance
  de la entrega.
- **Plan futuro:**
  - **Calibración visual por usuario:** subir un fotograma representativo
    de la grabación y dibujar con el ratón los recortes facecam y
    gameplay sobre la imagen. Persistir las 8 coordenadas en una nueva
    tabla `user_tiktok_settings` o como columnas adicionales del User.
  - **Alternativa más simple:** exponer los 8 valores como sliders/inputs
    numéricos en `/account.html` (mismo patrón que F6X con
    `chain_window_seconds` etc.).
  - **Override por vídeo en la subida:** mismo patrón que F10.2 con los
    settings del detector — la calibración persistente vive en el User
    pero se puede sobreescribir por subida si una grabación concreta
    tiene otro layout.
  - **Soporte de máscaras alternativas:** rectangular, oval, sin máscara
    (facecam recortada limpia), o subir una máscara propia en PNG con
    alpha. Asset actualmente fijo en
    `backend/detector/assets/tiktok_mask.png`.
  - **Posición de la facecam configurable:** ahora siempre flotante
    centrada en `y = 250`. Permitir esquinas (top-left, top-right,
    bottom-left, bottom-right) o coordenadas libres.

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
| Análisis visual | CNN ResNet18 (killfeed) | + pipeline reproducible + chain window por juego |
| Análisis audio | — | Whisper + librosa (opt-in) |
| Edición | Recorte temporal directo + variante 9:16 con coords hardcoded (F13.2) | Editor estilo TikTok configurable (calibración visual, máscaras alternativas, subtítulos) |
| Configuración por usuario | Globales en `config.json` | Tabla `user_settings` (sensibilidad, margen, duración) |
| Frontend | HTML/CSS/JS plano | React + Vite (opcional) |
| Negocio | Sin créditos / sin planes | Modelo de suscripción |
| Tests | Verificación manual | `pytest` + integración |

El MVP cumple el flujo demostrable; cada fila de la tabla es un eje
independiente de evolución hacia la arquitectura objetivo.
