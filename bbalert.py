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
from handlers.admin import logs_command, ms_handler
from utils.logger import add_log_line
from handlers.models import models_command, models_callback
from handlers.agents import agents_command, agents_callback

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

    # --- REGISTRO DE HANDLERS (ORDEN CORREGIDO) ---
    
    # 1. Comandos Generales
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("newchat", newchat))
    app.add_handler(CommandHandler("models", models_command))
    app.add_handler(CommandHandler("agent", agents_command))
    
    # 2. Handlers de Conversación (ADMIN) - PRIORIDAD ALTA
    # IMPORTANTE: Esto debe ir ANTES de cualquier CallbackQueryHandler global
    app.add_handler(ms_handler) 

    # 3. Handler de Botones (Menú de Modelos)
    # IMPORTANTE: Añadimos 'pattern' para que SOLO reaccione a botones de modelos
    # y deje pasar los botones del comando /ms u otros futuros.
    app.add_handler(CallbackQueryHandler(models_callback, pattern="^set_model\|"))
    app.add_handler(CallbackQueryHandler(agents_callback, pattern="^set_agent\||^close_menu"))
    
    # 4. Otros comandos admin
    app.add_handler(CommandHandler("logs", logs_command))

    # 5. Handler de chat general (Este debe ir al FINAL)
    chat_filter = (filters.TEXT | filters.VOICE | filters.AUDIO) & (~filters.COMMAND)
    app.add_handler(MessageHandler(chat_filter, chat_handler))

    # --- Registrar el manejador de errores ---
    app.add_error_handler(error_handler)

    print("✅ Bot iniciado correctamente.")
    
    app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)

if __name__ == '__main__':
    main()