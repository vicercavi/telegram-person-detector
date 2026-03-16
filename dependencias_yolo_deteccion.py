import subprocess
import sys
import os


requirements = [
    "ultralytics",         # Para YOLOv8
    "opencv-python",       # Para capturar video
    "python-telegram-bot==20.7",  # Para el bot de Telegram (versión 20.7 recomendada)
    "python-dotenv",       # Para cargar variables de entorno desde .env
]

# Ejecutar pip install para cada paquete
for package in requirements:
    print(f"⬇️ Instalando: {package}...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

print("\n🎉 Todas las dependencias fueron instaladas correctamente.")
