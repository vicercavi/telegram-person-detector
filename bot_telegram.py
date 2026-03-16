import cv2
import os
import argparse
import asyncio
import ctypes
from datetime import datetime
from dotenv import load_dotenv
from ultralytics import YOLO
from telegram import Update, Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

load_dotenv()

# --- Argumentos desde terminal ---
parser = argparse.ArgumentParser(description="Detección con YOLO y Telegram Bot")
parser.add_argument("--cam", type=int, default=0, help="ID de la cámara (default: 0)")
parser.add_argument("--save", type=str, default="capturas", help="Directorio donde guardar capturas")
parser.add_argument("--idle", type=int, default=60, help="Segundos de inactividad para considerar que no estas en la PC (default: 60)")
args = parser.parse_args()

CAMERA_ID = args.cam
SAVE_PATH = args.save
IDLE_THRESHOLD = args.idle

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

# --- Deteccion de inactividad del usuario (Windows) ---
def get_idle_seconds():
    """Retorna los segundos desde la ultima interaccion con mouse/teclado."""
    class LASTINPUTINFO(ctypes.Structure):
        _fields_ = [("cbSize", ctypes.c_uint), ("dwTime", ctypes.c_uint)]

    lii = LASTINPUTINFO()
    lii.cbSize = ctypes.sizeof(LASTINPUTINFO)
    ctypes.windll.user32.GetLastInputInfo(ctypes.byref(lii))
    millis = ctypes.windll.kernel32.GetTickCount() - lii.dwTime
    return millis / 1000.0

def user_is_away():
    """True si el usuario lleva mas tiempo inactivo que el umbral configurado."""
    return get_idle_seconds() > IDLE_THRESHOLD

# --- Ruta de guardado organizada por dia/hora ---
def get_save_path():
    """Retorna la ruta de guardado: SAVE_PATH/YYYY-MM-DD/HH/"""
    now = datetime.now()
    path = os.path.join(SAVE_PATH, now.strftime("%Y-%m-%d"), now.strftime("%H"))
    os.makedirs(path, exist_ok=True)
    return path

# --- Enviar imagen por Telegram ---
async def send_photo(photo_path):
    for user_id in USER_IDS:
        try:
            with open(photo_path, "rb") as photo_file:
                await bot.send_photo(chat_id=user_id, photo=photo_file)
            print(f"✅ Imagen enviada a {user_id}")
        except Exception as e:
            print(f"❌ Error enviando a {user_id}: {e}")

# --- Teclados inline ---
def main_menu_keyboard():
    """Menu principal con todas las opciones."""
    if running:
        buttons = [
            [InlineKeyboardButton("📷 Tomar foto", callback_data="foto")],
            [InlineKeyboardButton("🛑 Detener vigilancia", callback_data="stop")],
            [InlineKeyboardButton("ℹ️ Estado", callback_data="estado")],
        ]
    else:
        buttons = [
            [InlineKeyboardButton("▶️ Activar vigilancia", callback_data="start")],
            [InlineKeyboardButton("📷 Tomar foto", callback_data="foto")],
            [InlineKeyboardButton("ℹ️ Estado", callback_data="estado")],
        ]
    return InlineKeyboardMarkup(buttons)

def ask_start_keyboard():
    """Pregunta si desea activar la deteccion."""
    buttons = [
        [InlineKeyboardButton("✅ Si, activar", callback_data="start"),
         InlineKeyboardButton("❌ No", callback_data="menu")],
    ]
    return InlineKeyboardMarkup(buttons)

# --- Comando /start (menu de bienvenida) ---
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome = (
        "🤖 *Camara de Seguridad Inteligente*\n\n"
        "Controla tu sistema de vigilancia desde aqui.\n"
        "Selecciona una opcion:"
    )
    await update.message.reply_text(welcome, parse_mode="Markdown", reply_markup=main_menu_keyboard())

# --- Comando /foto directo ---
async def foto_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _take_and_send_photo(update.effective_user.id, context)
    if not running:
        await context.bot.send_message(
            chat_id=update.effective_user.id,
            text="🔔 La vigilancia automatica esta *desactivada*.\n¿Deseas activar la deteccion de personas?",
            parse_mode="Markdown",
            reply_markup=ask_start_keyboard(),
        )

# --- Comando /stop directo ---
async def stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global running
    if running:
        running = False
        await update.message.reply_text(
            "🛑 Vigilancia detenida.",
            reply_markup=main_menu_keyboard(),
        )
    else:
        await update.message.reply_text(
            "⏹️ No estaba activa.",
            reply_markup=main_menu_keyboard(),
        )

# --- Manejador de botones ---
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global running, detection_task
    query = update.callback_query
    await query.answer()

    if query.data == "start":
        if not running:
            running = True
            detection_task = asyncio.create_task(detection_loop())
            await query.edit_message_text(
                "▶️ *Vigilancia activada*\n\nTe avisare cuando detecte a alguien.",
                parse_mode="Markdown",
                reply_markup=main_menu_keyboard(),
            )
        else:
            await query.edit_message_text(
                "⚠️ La vigilancia ya esta activa.",
                reply_markup=main_menu_keyboard(),
            )

    elif query.data == "stop":
        if running:
            running = False
            buttons = [
                [InlineKeyboardButton("▶️ Reactivar", callback_data="start"),
                 InlineKeyboardButton("📷 Tomar foto", callback_data="foto")],
                [InlineKeyboardButton("🏠 Menu", callback_data="menu")],
            ]
            await query.edit_message_text(
                "🛑 *Vigilancia detenida*\n\n¿Que deseas hacer?",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(buttons),
            )
        else:
            await query.edit_message_text(
                "⏹️ No estaba activa.",
                reply_markup=main_menu_keyboard(),
            )

    elif query.data == "foto":
        await query.edit_message_text("📷 Capturando foto...")
        await _take_and_send_photo(query.from_user.id, context)
        if not running:
            await context.bot.send_message(
                chat_id=query.from_user.id,
                text="🔔 La vigilancia automatica esta *desactivada*.\n¿Deseas activar la deteccion de personas?",
                parse_mode="Markdown",
                reply_markup=ask_start_keyboard(),
            )
        else:
            await context.bot.send_message(
                chat_id=query.from_user.id,
                text="📸 Foto enviada. La vigilancia sigue activa.",
                reply_markup=main_menu_keyboard(),
            )

    elif query.data == "estado":
        idle = get_idle_seconds()
        status = "🟢 *Activa*" if running else "🔴 *Inactiva*"
        presence = "🖥️ En la PC" if idle < IDLE_THRESHOLD else f"💤 Ausente ({int(idle)}s sin actividad)"
        text = (
            f"📊 *Estado del sistema*\n\n"
            f"Vigilancia: {status}\n"
            f"Usuario: {presence}\n"
            f"Capturas totales: {frame_count}\n"
            f"Camara: {CAMERA_ID}"
        )
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=main_menu_keyboard())

    elif query.data == "menu":
        await query.edit_message_text(
            "🤖 *Camara de Seguridad Inteligente*\n\nSelecciona una opcion:",
            parse_mode="Markdown",
            reply_markup=main_menu_keyboard(),
        )

# --- Capturar y enviar foto ---
async def _take_and_send_photo(user_id, context):
    cap = cv2.VideoCapture(CAMERA_ID, cv2.CAP_DSHOW)
    if not cap.isOpened():
        await context.bot.send_message(chat_id=user_id, text="❌ No se pudo abrir la cámara.")
        return

    ret, frame = cap.read()
    cap.release()

    if not ret:
        await context.bot.send_message(chat_id=user_id, text="❌ No se pudo capturar la imagen.")
        return

    save_dir = get_save_path()
    timestamp = datetime.now().strftime("%H%M%S")
    img_name = os.path.join(save_dir, f"foto_manual_{timestamp}.jpg")
    cv2.imwrite(img_name, frame)

    with open(img_name, "rb") as photo_file:
        await context.bot.send_photo(chat_id=user_id, photo=photo_file)
    print(f"📷 Foto manual enviada a {user_id}: {img_name}")

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
            save_dir = get_save_path()
            timestamp = datetime.now().strftime("%H%M%S")
            img_name = os.path.join(save_dir, f"persona_{timestamp}_{frame_count}.jpg")
            cv2.imwrite(img_name, frame)
            print(f"📸 Imagen guardada: {img_name}")

            if user_is_away():
                await send_photo(img_name)
            else:
                print(f"🖥️ Usuario activo en la PC — notificacion omitida")

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
    app.add_handler(CommandHandler("foto", foto_command))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("🤖 Bot listo. Envia /start en Telegram para ver el menu.")
    app.run_polling()

if __name__ == "__main__":
    main()
