import cv2
import os
import argparse
import asyncio
from dotenv import load_dotenv
from ultralytics import YOLO
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, ContextTypes

load_dotenv()

# --- Argumentos desde terminal ---
parser = argparse.ArgumentParser(description="Detección con YOLO y Telegram Bot")
parser.add_argument("--cam", type=int, default=0, help="ID de la cámara (default: 0)")
parser.add_argument("--save", type=str, default="capturas", help="Directorio donde guardar capturas")
args = parser.parse_args()

CAMERA_ID = args.cam
SAVE_PATH = args.save
os.makedirs(SAVE_PATH, exist_ok=True)

# --- Configuración del bot ---
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
USER_IDS = [int(uid) for uid in os.getenv("TELEGRAM_USER_IDS", "").split(",") if uid.strip()]

if not TOKEN:
    raise ValueError("Falta la variable de entorno TELEGRAM_BOT_TOKEN. Revisa tu archivo .env")
if not USER_IDS:
    raise ValueError("Falta la variable de entorno TELEGRAM_USER_IDS. Revisa tu archivo .env")
# Obtener el path actual del script
current_dir = os.path.dirname(os.path.abspath(__file__))

# Ruta relativa al modelo
model_path = os.path.join(current_dir, "yolov8n.pt")

# Cargar el modelo
model = YOLO(model_path)

bot = Bot(token=TOKEN)

# Variables de control
running = False
detection_task = None
frame_count = 0

# --- Enviar imagen por Telegram ---
async def send_photo(photo_path):
    for user_id in USER_IDS:
        try:
            with open(photo_path, "rb") as photo_file:
                await bot.send_photo(chat_id=user_id, photo=photo_file)
            print(f"✅ Imagen enviada a {user_id}")
        except Exception as e:
            print(f"❌ Error enviando a {user_id}: {e}")

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global running, detection_task
    if not running:
        running = True
        await update.message.reply_text("▶️ Detección iniciada.")
        detection_task = asyncio.create_task(detection_loop())
    else:
        await update.message.reply_text("⚠️ Ya está en ejecución.")

# --- Comando /stop ---
async def stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global running
    if running:
        running = False
        await update.message.reply_text("🛑 Detección detenida.")
    else:
        await update.message.reply_text("⏹️ No estaba ejecutándose.")

async def detection_loop():
    global running, frame_count

    print(f"🎥 Iniciando cámara {CAMERA_ID}...")
    cap = cv2.VideoCapture(CAMERA_ID, cv2.CAP_DSHOW)

    if not cap.isOpened():
        print(f"❌ No se pudo abrir la cámara {CAMERA_ID}")
        return

    while running and cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            print("⚠️ No se pudo leer el frame.")
            break

        results = model(frame, conf=0.8)
        detected = any(
            result.names[int(box.cls[0])] == "person"
            for result in results
            for box in result.boxes
        )

        if detected:
            img_name = os.path.join(SAVE_PATH, f"persona_detectada_{frame_count}.jpg")
            cv2.imwrite(img_name, frame)
            print(f"📸 Imagen guardada: {img_name}")
            await send_photo(img_name)

        frame_count += 1
        await asyncio.sleep(0.1)

    print("🧹 Liberando recursos...")
    cap.release()
    cv2.destroyAllWindows()

# --- Main sin async ---
def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("stop", stop_command))

    print("🤖 Bot escuchando comandos /start y /stop...")
    app.run_polling()

if __name__ == "__main__":
    main()
