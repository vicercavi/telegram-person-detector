# Convierte tu PC en una Camara de Seguridad Inteligente

Transforma cualquier computadora con webcam en un sistema de vigilancia inteligente que monitorea lo que ocurre cuando no estas. Usa inteligencia artificial (YOLOv8) para detectar personas en tiempo real y te avisa al instante por Telegram con una foto de lo que detecto.

Ideal para vigilar tu hogar, oficina, habitacion o cualquier espacio mientras estas fuera.

## Descripcion

Este proyecto combina vision por computadora con un bot de Telegram para crear un sistema de seguridad casero sin necesidad de comprar camaras especializadas — solo necesitas tu PC y una webcam:

1. **Tu PC se convierte en camara de seguridad** — usa tu webcam, camara USB o cualquier camara conectada
2. **Deteccion inteligente de personas** — usa el modelo YOLOv8 nano para identificar personas con 80% de confianza, ignorando mascotas, sombras u objetos
3. **Alertas instantaneas en tu celular** — recibe una foto en Telegram en el momento exacto en que alguien aparece
4. **Control remoto desde cualquier lugar** — activa o desactiva la vigilancia desde tu celular con `/start` y `/stop`
5. **Modo inteligente** — detecta si estas usando la PC (mouse/teclado) y solo envia notificaciones cuando no estas presente
6. **Registro fotografico organizado** — las capturas se guardan automaticamente en subcarpetas por dia y hora (`capturas/2026-03-16/14/`)

## Estructura del Proyecto

```
deteccion/
├── bot_telegram.py                # Script principal del bot
├── dependencias_yolo_deteccion.py # Script para instalar dependencias
├── yolov8n.pt                     # Modelo YOLOv8 nano pre-entrenado
├── .env                           # Tus credenciales (no se sube al repo)
├── .env.example                   # Plantilla de configuracion
├── capturas/                      # Capturas organizadas por dia/hora
│   └── 2026-03-16/
│       ├── 09/                    # Capturas de las 9:00 - 9:59
│       ├── 14/                    # Capturas de las 14:00 - 14:59
│       └── ...
├── LEER.txt                       # Instrucciones originales
└── README.md                      # Este archivo
```

## Requisitos Previos

- **Python 3.10** (recomendado via Anaconda/Miniconda)
- Una **camara** conectada al equipo
- Un **bot de Telegram** creado con [@BotFather](https://t.me/BotFather)
- Tu **ID de usuario** de Telegram (puedes obtenerlo con [@userinfobot](https://t.me/userinfobot))

## Instalacion

### 1. Crear entorno virtual con Anaconda

```bash
conda create -n deteccion_personas python==3.10
conda activate deteccion_personas
```

### 2. Instalar dependencias

Ejecuta el script de instalacion dentro del entorno activado:

```bash
python dependencias_yolo_deteccion.py
```

Esto instalara:
- `ultralytics` — YOLOv8 para deteccion de objetos
- `opencv-python` — Captura y procesamiento de video
- `python-telegram-bot==20.7` — API del bot de Telegram
- `python-dotenv` — Carga de variables de entorno desde archivo `.env`

### 3. Configurar el bot

Copia el archivo de ejemplo y edita con tus credenciales:

```bash
cp .env.example .env
```

Edita `.env` con tus datos:

```env
TELEGRAM_BOT_TOKEN=tu_token_aqui
TELEGRAM_USER_IDS=123456789
```

> **Nota de seguridad:** El archivo `.env` esta en `.gitignore` y nunca se sube al repositorio. No compartas tu token publicamente.

## Uso

### Iniciar el bot

```bash
conda activate deteccion
python bot_telegram.py --cam 0 --save capturas
```

**Argumentos:**

| Argumento | Descripcion | Default |
|-----------|-------------|---------|
| `--cam`   | ID de la camara (0 = webcam principal) | `0` |
| `--save`  | Directorio donde guardar las capturas | `capturas` |
| `--idle`  | Segundos sin actividad para considerar que no estas en la PC | `60` |

### Comandos de Telegram

Una vez que aparezca el mensaje `Bot escuchando comandos /start, /stop y /foto...`, abre el chat con tu bot en Telegram y usa:

| Comando  | Accion |
|----------|--------|
| `/start` | Inicia la deteccion y el envio de fotos |
| `/stop`  | Detiene la deteccion |
| `/foto`  | Captura y envia una foto al instante (sin necesidad de que `/start` este activo) |

### Ejemplo completo

```bash
# Activar entorno
conda activate deteccion

# Usar camara 0 y guardar capturas en escritorio
python bot_telegram.py --cam 0 --save C:\Users\tu_usuario\Desktop\capturas_personas
```

## Como Funciona

1. El bot se conecta a Telegram y espera comandos
2. Al recibir `/start`, abre la camara indicada
3. Lee frames continuamente y los analiza con YOLOv8
4. Si detecta una persona (confianza >= 80%), guarda la imagen en `capturas/YYYY-MM-DD/HH/`
5. Verifica si el usuario esta activo en la PC (mouse/teclado)
   - **Si estas ausente** (sin actividad por mas de `--idle` segundos): envia la foto por Telegram
   - **Si estas presente**: guarda la foto pero NO envia notificacion
6. Continua hasta recibir `/stop` o cerrar el programa

## Solucion de Problemas

- **"No se pudo abrir la camara"**: Verifica que la camara esta conectada y el ID es correcto. Prueba con `--cam 1` si `--cam 0` no funciona.
- **El bot no responde en Telegram**: Asegura que el token es correcto y que iniciaste una conversacion con el bot primero.
- **Deteccion lenta**: El modelo `yolov8n.pt` es el mas ligero. Si tienes GPU NVIDIA, instala CUDA para acelerar la inferencia.
