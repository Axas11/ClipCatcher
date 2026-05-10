# Trabajo futuro — ClipCatcher

Este documento recoge el camino de evolución del MVP entregable hacia un
producto más completo. Lo que está implementado a día de la entrega
(detección visual con CNN, login email+password y OAuth Google,
configuración por vídeo, conversor TikTok básico, recuperación de
contraseña por email) **no aparece aquí**: solo lo que aún falta y por
qué encajaría con la arquitectura actual.

---

## Persistencia y migraciones

El MVP usa SQLite con `Base.metadata.create_all()` al arrancar, sin
versionado de schema. Funciona para un único usuario evaluando en
local, pero en cuanto haya datos reales de varios usuarios la falta
de migraciones se vuelve un problema en cada cambio de modelo.

El siguiente paso lógico es migrar a PostgreSQL e introducir Alembic.
La capa SQLAlchemy hace que el cambio de motor sea casi transparente
(cambiar `DATABASE_URL` y revisar tipos específicos como
`DateTime(timezone=True)`, que en SQLite hoy se devuelve como naive
y obliga a un `replace(tzinfo=timezone.utc)` defensivo en
`reset_password`). Postgres elimina ese parche y aporta concurrencia
real, índices más ricos y herramientas de backup serias.

---

## Procesamiento distribuido

Hoy el procesamiento de un vídeo (analyze + export + opcional
conversión TikTok) corre en `BackgroundTasks` de FastAPI, dentro del
mismo proceso del servidor web. Eso bloquea CPU del servidor mientras
la inferencia ocurre, y limita la concurrencia a lo que aguante un
solo proceso uvicorn.

El paso natural es mover el procesamiento a un worker independiente
con Redis + RQ (o Celery), idealmente sobre máquinas con GPU. Esto
permite escalar workers en horizontal, dar prioridad de cola a los
planes premium, y reintentar automáticamente cuando un job falla por
un fallo transitorio (ffmpeg que crashea, OOM, etc.). El servidor web
queda libre para responder requests, y el procesamiento de un vídeo
de 30 minutos no afecta a la latencia de un `GET /api/videos`.

---

## Detección visual

### Multijuego

El clasificador `kill_detector.pt` está entrenado solo con killfeed
de Valorant. El pipeline es genérico (recorte de ROI →
preprocesado → CNN binaria), así que la extensión a otros juegos
pasa por entrenar redes nuevas sobre cada killfeed.

Los candidatos obvios son CS2 (killfeed similar al de Valorant pero
con tipografía y posición distinta), League of Legends (eventos de
muerte con texto en banner inferior, no en killfeed clásico) y Apex
Legends (kills se ven en el centro de la pantalla durante los
finishers, requiere un ROI distinto). Cada juego necesita su propio
dataset etiquetado y, una vez entrenado, vivir como un `.pt`
independiente cargado según un parámetro `game` que el usuario
seleccione al subir el vídeo.

### Eventos más allá de la kill suelta

El detector actual marca frames con kill y agrupa los cercanos en
clips. Funciona bien para multikills consecutivas, pero no
distingue entre tipos de momento. Sería interesante reconocer
patrones de mayor nivel: un **ace** (5 kills en una sola ronda), un
**clutch** (1 superviviente vs varios enemigos cerrando la ronda),
**multikills clasificadas** (double / triple / quad / ace), y
finales de ronda con resultado.

Algunos se pueden derivar del propio detector existente contando
kills por ventana temporal, otros requieren una segunda señal:
indicadores de HUD del estado de la ronda, conteo de jugadores
vivos, scoreboard. Cada nuevo tipo de evento sería un clasificador
adicional o una regla de negocio sobre las detecciones primarias.

### Pipeline de entrenamiento reproducible

El modelo actual se entrenó manualmente con un dataset etiquetado
en dos carpetas y un cuaderno fuera del repo. Antes de añadir más
juegos conviene formalizar el flujo: un `scripts/train.py` con
carga del dataset desde una ruta configurable, división train/val
estratificada, training loop con `torch` y `torchvision`, early
stopping y guardado del mejor checkpoint. Reportar precisión y
recall sobre validación independiente, y guardar las métricas en un
`model_card.md` junto al `.pt` para tener trazabilidad de qué
modelo se desplegó.

### Whisper para análisis de audio

La detección actual es exclusivamente visual. Whisper permitiría
añadir una capa de audio: transcripción del jugador para localizar
momentos por palabra clave ("ace", "que peli", "lo tengo"), y
detección de picos de energía con librosa para encontrar reacciones
emocionales que la CNN no ve.

Whisper descarga modelos de 75 MB a 1.5 GB y aumenta tiempo de
procesamiento, así que tendría sentido como módulo opt-in que el
usuario activa por vídeo, idealmente solo para planes premium.

---

## Convertidor TikTok configurable

El conversor 9:16 que existe hoy en `backend/detector/tiktok_exporter.py`
funciona pero con coordenadas de crop hardcoded para el setup de OBS
del autor: facecam 310×170 en (0, 140) y gameplay 640×720 en (340, 0).
En grabaciones con otro layout sale descuadrado.

La forma más amable de hacerlo configurable es una calibración
visual: el usuario sube un fotograma representativo de su grabación
y dibuja con el ratón los recortes facecam y gameplay sobre la
imagen. Las 8 coordenadas resultantes se persisten en
`user_tiktok_settings` (o como columnas del User) y se aplican a
cada conversión futura. Como atajo previo, se podrían exponer los 8
valores como sliders en `/account.html`, igual que ya están las
opciones del detector.

Además, vale la pena soportar máscaras alternativas (rectangular,
oval, sin máscara, o PNG custom subido por el usuario) y permitir
posicionar la facecam en esquinas (top-left, top-right, etc.) en
lugar del centrado fijo actual.

---

## Editor visual post-detección

El conversor TikTok actual hace una composición fija: recorta
gameplay, recorta facecam, las apila vertical y exporta. No hay
edición real.

Un editor visual permitiría al usuario ajustar cada clip antes de
descargarlo: marcar punto de entrada y salida con precisión de
frame, añadir subtítulos generados (encajaría con Whisper), aplicar
plantillas predefinidas según el tipo de highlight (1v1, multikill,
clutch), y añadir overlays opcionales (marca de agua, texto fijo,
contador de kills). La edición debería ser **no destructiva** sobre
el clip original — guardar la timeline en BD y renderizar bajo
demanda — para que el usuario pueda iterar.

---

## App móvil / PWA con notificaciones push

El procesamiento es asíncrono: el usuario sube y queda esperando.
Hoy la página `video.html` hace polling cada 5 s al backend para ver
si terminó. Funciona en escritorio donde la pestaña está abierta,
pero en móvil la pestaña se duerme.

Convertir el frontend en una PWA con service worker y notificaciones
push permitiría notificar "tu vídeo está listo" sin que el usuario
tenga que mantener la app en primer plano. Encaja bien con el flujo
de "subo, cierro, vuelvo cuando me avisen". El backend ya tiene la
señal (status pasa a `done`); solo faltaría persistir el endpoint
push de cada cliente y disparar la notificación tras la transición.

---

## Modelo de negocio

El MVP no tiene plan de pago, ni cuotas, ni límites por usuario.
Para un producto real eso es insostenible: el coste por minuto
procesado es real (CPU/GPU, almacenamiento, ancho de banda).

El esquema natural sería freemium con tres ejes: tamaño máximo de
subida (free 2 GB / premium 10 GB), número de vídeos por mes,
acceso a features avanzadas (Whisper, conversor TikTok configurable,
editor). En el plan free se añadiría una marca de agua discreta en
el clip exportado, y los jobs de free entrarían a la cola con
prioridad menor que los premium. Modelos `Plan`, `Subscription` y
`CreditLedger`, integración con una pasarela de pago (Stripe es la
opción menos dolorosa), y webhooks para sincronizar estados.

---

## Operación

### Rate limiting

Los endpoints sensibles (`/api/auth/login`, `/api/auth/forgot-password`,
`/api/auth/reset-password`, `/api/videos` POST) no tienen rate
limiting. Eso significa que un atacante puede hacer fuerza bruta
sobre passwords, enumerar emails registrados saturando el SMTP de
Gmail, o agotar disco subiendo vídeos en bucle.

`slowapi` (FastAPI + limiter) es el camino más directo: límites
por IP en login (5/min), por email en forgot-password (1/min para
no dejar el SMTP de Gmail al borde de bloqueo), y por usuario en
upload (3/hora en plan free). Postgres + Redis dan storage propio
para los contadores; en SQLite se puede usar memoria con la
aceptación de que reiniciar el servidor resetea las cuotas.

### Email templates HTML

El email de reset de contraseña actual es texto plano. Funciona
pero parece de los 90: cualquier usuario espera diseño,
branding y link como botón. Pasar a HTML+text fallback con un
template engine ligero (Jinja2 ya viene con FastAPI en realidad
indirecto, o `email.message.EmailMessage` con `add_alternative`
para multipart) y un par de plantillas (`reset_password.html`,
quizás también un `welcome.html` post-registro y un
`processing_done.html` cuando se generen los clips si se va por la
ruta de notificaciones).

### Tests automatizados

El MVP se ha verificado con smoke scripts puntuales que se borran
tras pasar (creados en backend/_*_smoke.py durante cada fase).
Antes de abrir la app a usuarios reales hace falta cobertura
permanente: `pytest` para utilidades y servicios, integración con
`httpx.AsyncClient` para los endpoints, fixture de SQLite en
memoria para no depender del estado del disco, y un test de humo
del detector con un mp4 corto que valide que el `.pt` carga y
predice. La meta no es 100% de cobertura sino los caminos críticos
(auth, upload, procesamiento, descarga, password reset) blindados.

---

## Resumen

| Eje | MVP actual | Siguiente paso |
|---|---|---|
| Persistencia | SQLite + `create_all` al arrancar | PostgreSQL + Alembic |
| Cola de procesamiento | `BackgroundTasks` en proceso | Redis + RQ con workers GPU |
| Detección visual | CNN binaria killfeed Valorant | Multijuego + eventos compuestos (ace, clutch, multikills) |
| Análisis de audio | — | Whisper opt-in con librosa para picos |
| Edición de vídeo | Recorte temporal + 9:16 con coords fijas | Editor visual + calibración por usuario + plantillas |
| Cliente | Web responsive | PWA con notificaciones push |
| Auth | Email+password, JWT, OAuth Google, password reset | + rate limiting en endpoints sensibles |
| Comunicación con el usuario | Email texto plano | Templates HTML con branding |
| Negocio | Sin cuotas | Freemium con créditos y planes |
| Calidad | Smokes manuales por fase | `pytest` + integración + CI |

Cada fila es un eje independiente y se pueden abordar en cualquier
orden. Los más urgentes para abrir la app a usuarios reales son
rate limiting, tests automatizados y migración a Postgres; el resto
son evolución de producto a medio plazo.
