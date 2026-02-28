# CREAR NUEVO ARCHIVO: handlers/agents.py

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from core.context_manager import set_user_agent, get_user_agent

# Definición de Agentes
AGENTS = {
    "general": {
        "name": "🌐 IA General",
        "desc": "Conocimiento puro del modelo. Sin acceso a documentos locales.",
        "folder": None 
    },
    "bitbread": {
        "name": "🛠️ Soporte BitBread",
        "desc": "Experto en el sistema, alertas y configuraciones del bot.",
        "folder": "BitBread" # Debe coincidir con el nombre exacto de la carpeta
    },
    "iso17025": {
        "name": "🧪 Experto ISO 17025",
        "desc": "Especialista en normativas ONARC/ONIE y gestión de laboratorios acreditados ISO 17025.",
        "folder": "ISO17025" # Debe coincidir con el nombre exacto de la carpeta
    }
}

async def agents_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra el menú de selección de agentes."""
    user_id = update.effective_user.id
    current_agent = get_user_agent(user_id)
    
    text = (
        "🕵️ <b>Selecciona tu Agente IA</b>\n\n"
        "Elige un experto para mejorar la precisión de las respuestas y ahorrar recursos.\n\n"
    )
    
    keyboard = []
    for agent_id, info in AGENTS.items():
        status = "✅" if agent_id == current_agent else "🔘"
        # Botón con Nombre y Estado
        btn_text = f"{status} {info['name']}"
        keyboard.append([InlineKeyboardButton(btn_text, callback_data=f"set_agent|{agent_id}")])
        
    # Botón de cerrar
    keyboard.append([InlineKeyboardButton("❌ Cerrar menú", callback_data="close_menu")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="HTML")

async def agents_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja los clics en los botones de agentes."""
    query = update.callback_query
    await query.answer()

    data = query.data
    
    if data == "close_menu":
        await query.delete_message()
        return

    if not data.startswith("set_agent|"):
        return

    new_agent_id = data.split("|")[1]
    user_id = query.from_user.id
    
    # Guardar selección
    set_user_agent(user_id, new_agent_id)
    
    # Obtener info para feedback
    agent_info = AGENTS.get(new_agent_id, AGENTS["general"])
    
    # Confirmación visual (editando el mensaje)
    success_text = (
        f"🔄 <b>Agente activado: {agent_info['name']}</b>\n\n"
        f"📝 <i>{agent_info['desc']}</i>\n\n"
        "Ahora puedes preguntar."
    )
    
    await query.edit_message_text(success_text, parse_mode="HTML")