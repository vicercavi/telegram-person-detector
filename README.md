# Bot de Deteccion de Personas con YOLOv8 y Telegram

Bot que utiliza la camara de tu equipo para detectar personas en tiempo real mediante el modelo YOLOv8. Cuando detecta una persona, captura una imagen y la envia automaticamente a traves de Telegram.

## Descripcion

Este proyecto combina vision por computadora con un bot de Telegram para crear un sistema de vigilancia ligero:

1. **Captura de video** en tiempo real desde una camara (webcam, camara USB, etc.)
2. **Deteccion de personas** usando el modelo YOLOv8 nano (`yolov8n.pt`) con un umbral de confianza del 80%
3. **Notificacion instantanea** via Telegram: envia la foto capturada al usuario configurado
4. **Control remoto** del sistema desde el chat de Telegram con comandos `/start` y `/stop`

## Estructura del Proyecto

```
deteccion/
├── bot_telegram.py                # Script principal del bot
├── dependencias_yolo_deteccion.py # Script para instalar dependencias
├── yolov8n.pt                     # Modelo YOLOv8 nano pre-entrenado
├── capturas/                      # Carpeta donde se guardan las imagenes capturadas
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
conda create -n deteccion python==3.10
conda activate deteccion
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

### Comandos de Telegram

Una vez que aparezca el mensaje `Bot escuchando comandos /start y /stop...`, abre el chat con tu bot en Telegram y usa:

| Comando  | Accion |
|----------|--------|
| `/start` | Inicia la deteccion y el envio de fotos |
| `/stop`  | Detiene la deteccion |

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
4. Si detecta una persona (confianza >= 80%), guarda la imagen como `persona_detectada_N.jpg`
5. Envia la imagen al usuario via Telegram
6. Continua hasta recibir `/stop` o cerrar el programa

## Solucion de Problemas

- **"No se pudo abrir la camara"**: Verifica que la camara esta conectada y el ID es correcto. Prueba con `--cam 1` si `--cam 0` no funciona.
- **El bot no responde en Telegram**: Asegura que el token es correcto y que iniciaste una conversacion con el bot primero.
- **Deteccion lenta**: El modelo `yolov8n.pt` es el mas ligero. Si tienes GPU NVIDIA, instala CUDA para acelerar la inferencia.
