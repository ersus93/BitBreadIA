import os
from dotenv import load_dotenv

# Cargar el archivo .env
load_dotenv()
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# --- CONFIGURACIÓN DE TELEGRAM ---
TOKEN_TELEGRAM = os.getenv("TELEGRAM_TOKEN")
# Convertimos la cadena de IDs "123,456" en una lista de enteros [123, 456]
ADMIN_CHAT_IDS = [
    int(id.strip()) 
    for id in os.getenv("ADMIN_IDS", "").split(",") 
    if id.strip()
]

# --- CONFIGURACIÓN DE GROQ ---
# Lista de API Keys para la rotación
GROQ_API_KEYS = [
    key.strip() 
    for key in os.getenv("GROQ_API_KEYS", "").split(",") 
    if key.strip()
]

MODEL_NAME = os.getenv("MODEL_NAME", "llama3-8b-8192")

# --- PARÁMETROS DEL BOT ---
# Límite de mensajes que el bot recordará por usuario (contexto)
MAX_HISTORY = int(os.getenv("MAX_HISTORY", 2))

# --- RUTAS DE ARCHIVOS ---
# Carpeta para base de datos JSON y Logs
DATA_DIR = "data"
LOG_FILE = "bot_activity.log"
CONTEXT_FILE = os.path.join(DATA_DIR, "user_context.json")
DOCS_DIR = os.path.join(DATA_DIR, "docs")

if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

if not os.path.exists(DOCS_DIR):
    os.makedirs(DOCS_DIR)

try:
    with open(os.path.join(BASE_DIR, "version.txt"), "r") as f:
        BOT_VERSION = f.read().strip()
except Exception as e:
    print(f"⚠️ No se pudo leer version.txt: {e}")
    BOT_VERSION = "0.0.00"