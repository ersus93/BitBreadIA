from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from core.context_manager import set_user_model, get_user_model
import os

# Modelo por defecto del sistema (backup)
DEFAULT_MODEL = os.getenv("MODEL_NAME", "llama3-8b-8192")

# Definición de modelos disponibles (ID API : Nombre amigable)
AVAILABLE_MODELS = {
    "llama3-70b-8192": "🧠 Llama 3 70B (Inteligente/Code/Math)",
    "llama-3.1-8b-instant": "⚡ Llama 3.1 8B (Rápido/Chat)",
    "gemma2-9b-it": "🤖 Gemma 2 9B (Google/Creativo)",
    "openai/gpt-oss-120b": "🦾 GPT-OSS 120B (OpenAI/Inteligente)"
}

async def models_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Envía el menú de selección de modelos."""
    user_id = update.effective_user.id
    current_model = get_user_model(user_id, DEFAULT_MODEL)

    keyboard = []
    for model_id, model_name in AVAILABLE_MODELS.items():
        # Añadir un check ✅ al modelo actual
        display_text = model_name
        if model_id == current_model:
            display_text = f"✅ {model_name}"
        
        # El callback_data envía "set_model|ID_DEL_MODELO"
        keyboard.append([InlineKeyboardButton(display_text, callback_data=f"set_model|{model_id}")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    
    msg_text = (
        "<b>🛠️ Configuración de BitBread IA</b>\n\n"
        "Selecciona el modelo que deseas usar. Tu preferencia se guardará automáticamente.\n\n"
        "🔸 <b>Llama 70B:</b> El más inteligente y el que se usa por defecto. Útil para código, matemáticas y lógica compleja.\n"
        "🔸 <b>Llama 3.1 8B:</b> El más rápido. Ideal para charlas casuales.\n"
        "🔸 <b>Gemma 2:</b> Modelo de Google. Bueno para escritura creativa.\n"
        "🔸 <b>GPT-OSS 120B:</b> Modelo de OpenAI. Ideal para tareas complejas.\n"

    )

    await update.message.reply_text(msg_text, reply_markup=reply_markup, parse_mode="HTML")

async def models_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja el clic en los botones del menú."""
    query = update.callback_query
    await query.answer() # Avisar a Telegram que recibimos el clic

    data = query.data
    if not data.startswith("set_model|"):
        return

    # Extraer el ID del modelo seleccionado
    selected_model = data.split("|")[1]
    user_id = query.from_user.id

    # Guardar en JSON
    set_user_model(user_id, selected_model)

    # Actualizar el mensaje para mostrar el nuevo ✅
    # Reconstruimos el teclado
    keyboard = []
    for model_id, model_name in AVAILABLE_MODELS.items():
        display_text = model_name
        if model_id == selected_model:
            display_text = f"✅ {model_name}"
        keyboard.append([InlineKeyboardButton(display_text, callback_data=f"set_model|{model_id}")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_reply_markup(reply_markup=reply_markup)
    await query.edit_message_text(
        text=f"✅ <b>Modelo actualizado a:</b>\n{AVAILABLE_MODELS.get(selected_model, selected_model)}\n\n¡Ya puedes continuar hablando!",
        reply_markup=reply_markup,
        parse_mode="HTML"
    )