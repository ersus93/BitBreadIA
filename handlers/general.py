from telegram import Update
from telegram.ext import ContextTypes
from core.context_manager import clear_context

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.first_name
    await update.message.reply_text(
        f"¡Hola {user}! 🤖\n\n"
        "Soy BitBread IA. Puedes hablar conmigo de lo que quieras.\n"
        "💾 Recuerdo nuestras últimas conversaciones.\n"
        "🔄 Usa /newchat si quieres que olvide lo anterior y empecemos de cero."
    )

async def newchat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    clear_context(user_id)
    await update.message.reply_text("🗑️ He borrado nuestra memoria. ¡Empecemos de nuevo! ¿En qué te ayudo?")