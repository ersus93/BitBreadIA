# bbalert.py
import logging
import os
import traceback
import html
import json
from dotenv import load_dotenv
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# Importar handlers
from handlers.general import start, newchat
from handlers.chat import chat_handler
from handlers.admin import logs_command, ms_command
from utils.logger import add_log_line
from handlers.models import models_command, models_callback

# Cargar entorno
load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")

# Configuración básica de logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)

# --- NUEVO: Manejador de Errores ---
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Registra errores causados por Updates."""
    add_log_line(f"⚠️ Excepción capturada: {context.error}")
    
    # Imprimir el traceback en consola para depuración
    tb_list = traceback.format_exception(None, context.error, context.error.__traceback__)
    tb_string = "".join(tb_list)
    print(tb_string)

def main():
    if not TOKEN:
        print("❌ Error: No se encontró el TELEGRAM_TOKEN en .env")
        return

    add_log_line("🤖 Iniciando Bot de Chat Groq (Multi-API) con Soporte de Audio...")

    # Construir aplicación
    app = ApplicationBuilder().token(TOKEN).build()

    # --- REGISTRO DE HANDLERS ---
    
    # Comandos Generales
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("newchat", newchat))
    app.add_handler(CommandHandler("models", models_command))
    
    # Handler de Botones (Callbacks del menú)
    app.add_handler(CallbackQueryHandler(models_callback))
    
    # Comandos Admin
    app.add_handler(CommandHandler("logs", logs_command))
    app.add_handler(CommandHandler("ms", ms_command))
    
    # Handler de Chat (Texto, Voz y Audio)
    # Tu filtro actual ya es correcto:
    chat_filter = (filters.TEXT | filters.VOICE | filters.AUDIO) & (~filters.COMMAND)
    app.add_handler(MessageHandler(chat_filter, chat_handler))

    # --- NUEVO: Registrar el manejador de errores ---
    app.add_error_handler(error_handler)

    print("✅ Bot iniciado correctamente.")
    
    # Ejecutar polling permitiendo reconexiones automáticas
    app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)

if __name__ == '__main__':
    main()