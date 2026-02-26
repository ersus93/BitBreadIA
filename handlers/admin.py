import os
import html
from telegram import Update, constants, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from core.groq_manager import groq_ai
from core.config import ADMIN_CHAT_IDS, BOT_VERSION
from core.context_manager import get_all_user_ids
from utils.logger import get_last_logs
from utils.broadcaster import broadcast_message

ADMIN_IDS = [int(id.strip()) for id in os.getenv("ADMIN_IDS", "").split(",") if id.strip()]


# Estados de la conversación
AWAITING_CONTENT = 1
AWAITING_CONFIRMATION = 2
AWAITING_ADDITIONAL_TEXT = 3
AWAITING_ADDITIONAL_PHOTO = 4


async def logs_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Verificar si es admin
    if update.effective_user.id not in ADMIN_CHAT_IDS:
        return

    try:
        # 1. Llamamos a la función CORRECTA que ya existe.
        stats_text = groq_ai.get_stats()

        # 2. Obtenemos logs
        raw_logs = get_last_logs(15)
        
        # 3. Escapamos los logs para evitar errores de parseo HTML
        escaped_logs = html.escape(raw_logs)

        # 4. Unimos todo
        final_message = (
            f"🤖 <b>BitBread IA:</b><i> v{BOT_VERSION}</i>\n\n"
            f"{stats_text}\n"
            f"📝 <b>Últimos Logs:</b>\n"
            f"<pre>{escaped_logs}</pre>"
        )

        await update.message.reply_text(final_message, parse_mode=constants.ParseMode.HTML)

    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")


# --- NUEVO SISTEMA /ms INTERACTIVO ---

async def ms_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Inicia el asistente de mensaje masivo."""
    user_id = update.effective_user.id
    
    if user_id not in ADMIN_CHAT_IDS:
        await update.message.reply_text("🚫 No autorizado.")
        return ConversationHandler.END

    # Limpiar datos previos
    context.user_data.pop('ms_text', None)
    context.user_data.pop('ms_photo_id', None)

    await update.message.reply_text(
        "✍️ <b>Difusión Masiva</b>\n\n"
        "Envía ahora el contenido del mensaje (Texto o Foto).\n"
        "Escribe /cancelar para salir.",
        parse_mode="HTML"
    )
    return AWAITING_CONTENT

async def handle_initial_content(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    message = update.message
    
    if message.text:
        context.user_data['ms_text'] = message.text
        keyboard = [
            [InlineKeyboardButton("🖼️ Añadir Imagen", callback_data="ms_add_photo")],
            [InlineKeyboardButton("🚀 Enviar Solo Texto", callback_data="ms_send_final")],
            [InlineKeyboardButton("❌ Cancelar", callback_data="ms_cancel")]
        ]
        await message.reply_text(
            "✅ Texto recibido. ¿Quieres añadir una imagen o enviar ya?",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    elif message.photo:
        context.user_data['ms_photo_id'] = message.photo[-1].file_id
        if message.caption:
            context.user_data['ms_text'] = message.caption

        keyboard = [
            [InlineKeyboardButton("✍️ Añadir/Editar Texto", callback_data="ms_add_text")],
            [InlineKeyboardButton("🚀 Enviar Solo Imagen", callback_data="ms_send_final")],
            [InlineKeyboardButton("❌ Cancelar", callback_data="ms_cancel")]
        ]
        await message.reply_text(
            "✅ Imagen recibida. ¿Quieres editar el texto o enviar?",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        await message.reply_text("⚠️ Envía solo texto o imagen.")
        return AWAITING_CONTENT

    return AWAITING_CONFIRMATION

async def handle_confirmation_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    choice = query.data

    if choice == "ms_add_text":
        await query.edit_message_text("✍️ Envía el texto que acompañará a la imagen:")
        return AWAITING_ADDITIONAL_TEXT
    
    elif choice == "ms_add_photo":
        await query.edit_message_text("🖼️ Envía la imagen para adjuntar al texto:")
        return AWAITING_ADDITIONAL_PHOTO
    
    elif choice == "ms_send_final":
        return await execute_broadcast(query, context)
    
    elif choice == "ms_cancel":
        await query.edit_message_text("🚫 Operación cancelada.")
        context.user_data.clear()
        return ConversationHandler.END

async def receive_additional_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['ms_text'] = update.message.text
    keyboard = [[InlineKeyboardButton("🚀 Enviar Ahora", callback_data="ms_send_final")]]
    await update.message.reply_text("✅ Texto actualizado. Listo para enviar.", reply_markup=InlineKeyboardMarkup(keyboard))
    return AWAITING_CONFIRMATION

async def receive_additional_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['ms_photo_id'] = update.message.photo[-1].file_id
    keyboard = [[InlineKeyboardButton("🚀 Enviar Ahora", callback_data="ms_send_final")]]
    await update.message.reply_text("✅ Imagen añadida. Lista para enviar.", reply_markup=InlineKeyboardMarkup(keyboard))
    return AWAITING_CONFIRMATION

async def execute_broadcast(query, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Ejecuta el envío usando la librería broadcaster."""
    await query.edit_message_text("⏳ <b>Iniciando difusión...</b>", parse_mode="HTML")

    text_to_send = context.user_data.get('ms_text', "")
    photo_id = context.user_data.get('ms_photo_id')
    
    # Obtenemos usuarios de nuestro context_manager
    target_ids = get_all_user_ids()
    
    if not target_ids:
        await query.message.reply_text("❌ No hay usuarios en la base de datos.")
        return ConversationHandler.END

    # --- USO DE LA LIBRERÍA ---
    fallidos = await broadcast_message(
        bot=context.bot,
        chat_ids=target_ids,
        text=text_to_send,
        photo_id=photo_id,
        parse_mode=constants.ParseMode.HTML
    )
    # --------------------------

    total_enviados = len(target_ids) - len(fallidos)
    
    reporte = f"✅ <b>Difusión Completada</b>\n\n🎯 Total: {len(target_ids)}\n✅ Enviados: {total_enviados}\n❌ Fallidos: {len(fallidos)}"
    
    if fallidos:
        reporte += "\n\n<b>Detalle de errores:</b>\n"
        for uid, err in list(fallidos.items())[:10]: # Mostrar max 10 errores
            reporte += f"• ID {uid}: {err}\n"

    await query.message.reply_text(reporte, parse_mode="HTML")
    context.user_data.clear()
    return ConversationHandler.END

async def cancel_ms(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("🚫 Cancelado.")
    context.user_data.clear()
    return ConversationHandler.END

# Objeto ConversationHandler para exportar a bbalert.py
ms_handler = ConversationHandler(
    entry_points=[CommandHandler("ms", ms_start)],
    states={
        AWAITING_CONTENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_initial_content), MessageHandler(filters.PHOTO, handle_initial_content)],
        AWAITING_CONFIRMATION: [CallbackQueryHandler(handle_confirmation_choice)],
        AWAITING_ADDITIONAL_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_additional_text)],
        AWAITING_ADDITIONAL_PHOTO: [MessageHandler(filters.PHOTO, receive_additional_photo)],
    },
    fallbacks=[CommandHandler("cancelar", cancel_ms)],
)