import os
import html
from telegram import Update, constants
from telegram.ext import ContextTypes
from core.groq_manager import groq_ai
from core.config import BOT_VERSION, ADMIN_CHAT_IDS
from utils.logger import get_last_logs # Asumiendo que tienes esto en logger.py

ADMIN_IDS = [int(id.strip()) for id in os.getenv("ADMIN_IDS", "").split(",") if id.strip()]

async def logs_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Verificar si es admin
    if update.effective_user.id not in ADMIN_CHAT_IDS:
        return

    try:
        # 1. Llamamos a la función CORRECTA que ya existe
        stats_text = groq_ai.get_stats()

        # 2. Obtenemos logs
        raw_logs = get_last_logs(15)
        
        # 3. Escapamos los logs para evitar errores de parseo HTML
        escaped_logs = html.escape(raw_logs)

        # 4. Unimos todo
        final_message = (
            f"{stats_text}\n"
            f"📝 <b>Últimos Logs:</b>\n"
            f"<pre>{escaped_logs}</pre>"
        )

        await update.message.reply_text(final_message, parse_mode=constants.ParseMode.HTML)

    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")


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