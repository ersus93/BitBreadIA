import os
from telegram import Update, constants
from telegram.ext import ContextTypes
from core.groq_manager import groq_ai
from core.context_manager import add_message, get_user_context, get_user_model
from utils.logger import add_log_line

# Importamos para manejar archivos temporales
import tempfile 

DEFAULT_MODEL = os.getenv("MODEL_NAME", "llama3-8b-8192")

async def chat_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    user_text = ""
    temp_file_path = None

    # 1. Verificar qué tipo de mensaje es (Texto o Audio)
    if update.message.text:
        user_text = update.message.text

    elif update.message.voice or update.message.audio:
        # Es un audio: procesar
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=constants.ChatAction.RECORD_VOICE)
        
        try:
            # Obtener el objeto archivo de Telegram
            voice = update.message.voice or update.message.audio
            file_obj = await context.bot.get_file(voice.file_id)
            
            # Crear un archivo temporal para guardarlo
            # Usamos sufijo .m4a o .ogg según lo que mande Telegram, pero .m4a suele funcionar bien con Whisper
            with tempfile.NamedTemporaryFile(delete=False, suffix=".m4a") as temp_file:
                temp_file_path = temp_file.name
            
            # Descargar el audio al disco
            await file_obj.download_to_drive(temp_file_path)
            
            # Transcribir con Groq
            transcription = await groq_ai.transcribe_audio(temp_file_path)
            
            if not transcription:
                await update.message.reply_text("🙉 Escuché algo, pero no pude entenderlo. Intenta de nuevo.")
                return

            # Tratamos la transcripción como si el usuario lo hubiera escrito
            user_text = transcription
            
            # (Opcional) Responder con el texto entendido para confirmar
            await update.message.reply_text(f"🎤 <i>Transcripción:</i> \"{user_text}\"", parse_mode="HTML")

        except Exception as e:
            add_log_line(f"Error procesando audio: {e}")
            await update.message.reply_text("❌ Hubo un error procesando tu audio.")
            return
        finally:
            # LIMPIEZA: Borrar el archivo temporal siempre
            if temp_file_path and os.path.exists(temp_file_path):
                os.remove(temp_file_path)
    
    else:
        # Si no es texto ni audio, ignoramos
        return

    # Si por alguna razón el texto está vacío
    if not user_text.strip():
        return

    # --- A PARTIR DE AQUÍ, ES IGUAL QUE ANTES ---

    # 2. Mostrar estado "escribiendo..." (porque ahora la IA va a pensar)
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=constants.ChatAction.TYPING)

    # 3. Guardar mensaje del usuario (guardamos el texto transcrito)
    add_message(user_id, "user", user_text)

    # 4. Obtener historial
    messages = get_user_context(user_id)

    # 5. Obtener modelo preferido del usuario
    user_model = get_user_model(user_id, DEFAULT_MODEL)

    # 6. Consultar a Groq (Cerebro LLM)
    ai_response = await groq_ai.get_response(messages, model=user_model)

    # 7. Guardar respuesta
    add_message(user_id, "assistant", ai_response)

    # 8. Responder
    try:
        await update.message.reply_text(ai_response, parse_mode=constants.ParseMode.HTML)
    except Exception as e:
        await update.message.reply_text(ai_response)