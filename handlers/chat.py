import os
import tempfile
from telegram import Update, constants
from telegram.ext import ContextTypes
from core.groq_manager import groq_ai
from core.context_manager import add_message, get_user_context, get_user_model
from utils.logger import add_log_line

DEFAULT_MODEL = os.getenv("MODEL_NAME", "llama3-8b-8192")

async def chat_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    
    # ID del hilo (Topic) para evitar errores
    thread_id = update.effective_message.message_thread_id
    
    user_text = ""
    temp_file_path = None

    # 1. Obtener el contenido del mensaje del usuario (Texto o Audio)
    if update.message.text:
        user_text = update.message.text

    elif update.message.voice or update.message.audio:
        # Procesamiento de Audio
        try:
            await context.bot.send_chat_action(
                chat_id=chat_id, 
                action=constants.ChatAction.RECORD_VOICE,
                message_thread_id=thread_id
            )
        except Exception as e:
            add_log_line(f"Error chat_action (voz): {e}")
        
        try:
            voice = update.message.voice or update.message.audio
            file_obj = await context.bot.get_file(voice.file_id)
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=".m4a") as temp_file:
                temp_file_path = temp_file.name
            
            await file_obj.download_to_drive(temp_file_path)
            
            # Transcribir
            transcription = await groq_ai.transcribe_audio(temp_file_path)
            
            if not transcription:
                await update.message.reply_text("🙉 No pude entender el audio.")
                return

            user_text = transcription
            # Confirmamos transcripción
            await update.message.reply_text(f"🎤 <i>Transcripción:</i> \"{user_text}\"", parse_mode="HTML")

        except Exception as e:
            add_log_line(f"Error audio: {e}")
            await update.message.reply_text("❌ Error procesando audio.")
            return
        finally:
            if temp_file_path and os.path.exists(temp_file_path):
                os.remove(temp_file_path)
    
    else:
        # Si no es texto ni audio, ignoramos
        return

    if not user_text.strip():
        return

    # --- NUEVA LÓGICA: DETECTAR CONTEXTO DE RESPUESTA (REPLY) ---
    # Verificamos si este mensaje es una respuesta a otro mensaje
    if update.message.reply_to_message:
        original_msg = update.message.reply_to_message
        
        # Intentamos obtener texto o caption (si es foto/video)
        original_text = original_msg.text or original_msg.caption or "[Archivo sin texto]"
        original_author = original_msg.from_user.first_name if original_msg.from_user else "Usuario"
        
        # Reescribimos lo que se enviará a la IA para incluir el contexto
        # La IA verá: El mensaje original + Tu pregunta
        user_text = (
            f"📄 [Contexto: Estoy respondiendo a un mensaje de {original_author} que dice:]\n"
            f"\"{original_text}\"\n\n"
            f"💬 [Mi respuesta/pregunta es:]\n"
            f"{user_text}"
        )
    # ------------------------------------------------------------

    # 2. Mostrar "Escribiendo..."
    try:
        await context.bot.send_chat_action(
            chat_id=chat_id, 
            action=constants.ChatAction.TYPING,
            message_thread_id=thread_id
        )
    except Exception as e:
        add_log_line(f"Error chat_action (typing): {e}")

    # 3. Guardar mensaje (ahora incluye el contexto si fue reply)
    add_message(user_id, "user", user_text)

    # 4. Obtener historial y modelo
    messages = get_user_context(user_id)
    user_model = get_user_model(user_id, DEFAULT_MODEL)

    # 5. Consultar a Groq
    ai_response = await groq_ai.get_response(messages, model=user_model)

    # 6. Guardar respuesta y Responder
    add_message(user_id, "assistant", ai_response)

    try:
        await update.message.reply_text(ai_response, parse_mode=constants.ParseMode.HTML)
    except Exception:
        await update.message.reply_text(ai_response)