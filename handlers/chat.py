import os
import tempfile
from telegram import Update, constants
from telegram.ext import ContextTypes
from core.groq_manager import groq_ai
from core.context_manager import add_message, get_user_context, get_user_model
from core.knowledge_manager import knowledge_base
from utils.logger import add_log_line

DEFAULT_MODEL = os.getenv("MODEL_NAME", "llama3-8b-8192")

async def chat_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type # 'private', 'group' o 'supergroup'
    thread_id = update.effective_message.message_thread_id
    
    user_text = ""
    temp_file_path = None

    # 1. Obtener el contenido (Texto o Audio)
    if update.message.text:
        user_text = update.message.text
    elif update.message.voice or update.message.audio:
        # --- Lógica de Audio (Se mantiene igual) ---
        try:
            await context.bot.send_chat_action(chat_id=chat_id, action=constants.ChatAction.RECORD_VOICE, message_thread_id=thread_id)
            voice = update.message.voice or update.message.audio
            file_obj = await context.bot.get_file(voice.file_id)
            with tempfile.NamedTemporaryFile(delete=False, suffix=".m4a") as temp_file:
                temp_file_path = temp_file.name
            await file_obj.download_to_drive(temp_file_path)
            transcription = await groq_ai.transcribe_audio(temp_file_path)
            if not transcription:
                return # Si no hay transcripción, no respondemos
            user_text = transcription
            await update.message.reply_text(f"🎤 <i>Transcripción:</i> \"{user_text}\"", parse_mode="HTML")
        except Exception as e:
            add_log_line(f"Error audio: {e}")
            return
        finally:
            if temp_file_path and os.path.exists(temp_file_path):
                os.remove(temp_file_path)
    
    if not user_text.strip():
        return

    # --- NUEVA LÓGICA DE FILTRADO PARA GRUPOS ---
    bot_user = await context.bot.get_me()
    bot_username = f"@{bot_user.username}"
    
    # Determinamos si debemos responder
    is_private = chat_type == constants.ChatType.PRIVATE
    is_mentioned = bot_username in user_text
    is_reply_to_bot = False
    
    if update.message.reply_to_message:
        # Verificamos si el mensaje al que responden es del bot
        is_reply_to_bot = update.message.reply_to_message.from_user.id == bot_user.id

    # Si NO es privado Y NO me mencionan Y NO me están respondiendo... ignoramos.
    if not is_private and not is_mentioned and not is_reply_to_bot:
        return 
    # --------------------------------------------

    # --- LÓGICA DE CONTEXTO DE RESPUESTA (Se mantiene igual) ---
    if update.message.reply_to_message:
        original_msg = update.message.reply_to_message
        original_text = original_msg.text or original_msg.caption or "[Archivo]"
        original_author = original_msg.from_user.first_name if original_msg.from_user else "Usuario"
        
        # Limpiamos la mención del texto para que no ensucie el prompt de la IA
        clean_text = user_text.replace(bot_username, "").strip()
        
        user_text = (
            f"📄 [Contexto: Respondiendo a {original_author}: \"{original_text}\"]\n"
            f"💬 [Pregunta]: {clean_text}"
        )

    # 2. Mostrar "Escribiendo..."
    try:
        await context.bot.send_chat_action(chat_id=chat_id, action=constants.ChatAction.TYPING, message_thread_id=thread_id)
    except Exception as e:
        add_log_line(f"Error chat_action: {e}")

    # 3. Guardar mensaje y obtener respuesta de Groq
    add_message(user_id, "user", user_text)
    messages = get_user_context(user_id)
    user_model = get_user_model(user_id, DEFAULT_MODEL)
    ai_response = await groq_ai.get_response(messages, model=user_model)

    # --- LÓGICA DE CONTEXTO LOCAL DATA ---
    # 1. Buscamos información en los archivos .md
    found_context = knowledge_base.get_relevant_context(user_text)
    
    # 2. Obtenemos el historial normal del chat
    messages = get_user_context(user_id)
    
    # 3. Si encontramos info en los docs, la inyectamos en el ÚLTIMO mensaje para la IA
    # (Esto no se guarda en la DB del usuario para no ensuciar el historial, solo se envía a Groq)
    messages_to_send = messages.copy() # Hacemos una copia para no alterar el original
    
    if found_context:
        # Modificamos el último mensaje de la copia para incluir la info encontrada
        last_msg = messages_to_send[-1]
        new_content = (
            f"{found_context}\n\n"
            f"Instrucción: Usa la información de arriba para responder la siguiente pregunta del usuario. "
            f"Si la información no es suficiente, responde con tu conocimiento general.\n\n"
            f"Pregunta del usuario: {last_msg['content']}"
        )
        messages_to_send[-1] = {"role": "user", "content": new_content}
        
        add_log_line(f"📚 Contexto inyectado para usuario {user_id}")

    user_model = get_user_model(user_id, DEFAULT_MODEL)
    
    # OJO: Aquí cambiamos 'messages' por 'messages_to_send'
    ai_response = await groq_ai.get_response(messages_to_send, model=user_model)    
   
    # 4. Guardar respuesta y enviar
    add_message(user_id, "assistant", ai_response)
    try:
        await update.message.reply_text(ai_response, parse_mode=constants.ParseMode.HTML)
    except Exception:
        await update.message.reply_text(ai_response)