import os
from telegram import Update
from telegram.ext import ContextTypes
from core.groq_manager import groq_ai
from utils.logger import get_last_logs # Asumiendo que tienes esto en logger.py

ADMIN_IDS = [int(id.strip()) for id in os.getenv("ADMIN_IDS", "").split(",") if id.strip()]

async def logs_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        return # Ignorar no admins

    # Estadísticas de API
    api_stats = groq_ai.get_stats()
    
    # Últimas líneas del log
    log_lines = get_last_logs(10) # Tu función que lee el archivo .log
    
    msg = f"{api_stats}\n\n📝 *Últimos Logs:*\n```{log_lines}```"
    await update.message.reply_text(msg, parse_mode="Markdown")

async def ms_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /ms ID MENSAJE"""
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        return

    try:
        args = context.args
        if len(args) < 2:
            await update.message.reply_text("Uso: /ms <user_id> <mensaje>")
            return

        target_id = int(args[0])
        message = " ".join(args[1:])
        
        await context.bot.send_message(chat_id=target_id, text=f"🔔 *Mensaje del Admin:*\n\n{message}", parse_mode="Markdown")
        await update.message.reply_text(f"✅ Mensaje enviado a {target_id}")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")