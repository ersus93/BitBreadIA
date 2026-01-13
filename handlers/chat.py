import os
import tempfile
from telegram import Update, constants
from telegram.ext import ContextTypes
from core.groq_manager import groq_ai
from core.context_manager import add_message, get_user_context, get_user_model, get_user_agent
from handlers.agents import AGENTS
from core.knowledge_manager import knowledge_base
from utils.logger import add_log_line
from utils.html_utils import smart_split, split_text_safe


DEFAULT_MODEL = os.getenv("MODEL_NAME", "llama3-8b-8192")

async def chat_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type # 'private', 'group' o 'supergroup'
    thread_id = update.effective_message.message_thread_id
    
    user_text = ""
    temp_file_path = None

    # 1. Obtener el contenido (Texto o Audio)
    msg = update.effective_message 
    
    # Si por alguna razón msg es None (ej: actualización de estado), salimos.
    if not msg:
        return

    user_text = ""
    temp_file_path = None

    # --- MODIFICACIÓN 1: Soporte para Caption (Msj Reenviados con foto) ---
    if msg.text:
        user_text = msg.text
    elif msg.caption: 
        user_text = msg.caption
    elif msg.voice or msg.audio:

        # --- Lógica de Audio (Se mantiene igual) ---
        try:
            await context.bot.send_chat_action(chat_id=chat_id, action=constants.ChatAction.RECORD_VOICE, message_thread_id=thread_id)
            # Usamos 'msg'
            voice = msg.voice or msg.audio 
            file_obj = await context.bot.get_file(voice.file_id)
            with tempfile.NamedTemporaryFile(delete=False, suffix=".m4a") as temp_file:
                temp_file_path = temp_file.name
            await file_obj.download_to_drive(temp_file_path)
            transcription = await groq_ai.transcribe_audio(temp_file_path)
            if not transcription:
                return # Si no hay transcripción, no respondemos
            user_text = transcription
            # Usamos 'msg' para responder
            await msg.reply_text(f"🎤 <i>Transcripción:</i> \"{user_text}\"", parse_mode="HTML")
        except Exception as e:
            add_log_line("¡Ups!", level="ERROR", error=e)
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
    
    if msg.reply_to_message:
        # Verificamos si el mensaje al que responden es del bot
        is_reply_to_bot = msg.reply_to_message.from_user.id == bot_user.id

    # Si NO es privado Y NO me mencionan Y NO me están respondiendo... ignoramos.
    if not is_private and not is_mentioned and not is_reply_to_bot:
        return 
    # --------------------------------------------

    # --- LÓGICA DE CONTEXTO DE RESPUESTA (Se mantiene igual) ---
    if msg.reply_to_message:   
        original_msg = msg.reply_to_message 
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
        add_log_line("¡Ups! Falló la lectura del mensaje", level="ERROR", error=e)

    # 3. Guardar mensaje y preparar envío
    add_message(user_id, "user", user_text)
    messages = get_user_context(user_id)
    
    # --- INICIO LÓGICA AGENTES (Corregida: Flujo Único) ---
    current_agent_id = get_user_agent(user_id)
    agent_config = AGENTS.get(current_agent_id, AGENTS["general"])
    target_folder = agent_config.get("folder")
    
    found_context = ""
    messages_to_send = messages.copy() # Preparamos la copia aquí

    # b) Lógica de inyección según agente
    if current_agent_id == "general":
        add_log_line(f"🌍 Modo General activado. Saltando búsqueda local.")
        # No buscamos nada, messages_to_send se queda igual (solo historial)
        
    else:
        # Es un agente especialista
        add_log_line(f"🔍 Agente {current_agent_id} buscando en carpeta: {target_folder}")
        # IMPORTANTE: Asegúrate de que knowledge_base.get_relevant_context soporte 'folder_filter' o revisa knowledge_manager.py
        # Si tu knowledge_manager usa 'filter_category', mantén eso.
        found_context = knowledge_base.get_relevant_context(user_text, filter_category=target_folder)
        
        if found_context:
            system_instruction = (
                f"⚠️ ACTUANDO COMO AGENTE ESPECIALISTA: {agent_config['name']}\n"
                f"Usa EXCLUSIVAMENTE la siguiente información oficial para responder.\n"
                f"Si la respuesta no está en el texto, indícalo claramente.\n\n"
            )
            
            # Inyectamos contexto en el último mensaje
            last_msg = messages_to_send[-1]
            new_content = (
                f"{found_context}\n\n"
                f"{system_instruction}"
                f"👤 Pregunta del usuario: {last_msg['content']}"
            )
            messages_to_send[-1] = {"role": "user", "content": new_content}
            add_log_line(f"📚 Contexto inyectado ({len(found_context)} chars).")

    user_model = get_user_model(user_id, DEFAULT_MODEL)
    
    # Usamos messages_to_send que ya contiene (o no) el contexto del agente
    ai_response = await groq_ai.get_response(messages_to_send, model=user_model)    
   
    # 4. Guardar respuesta
    add_message(user_id, "assistant", ai_response)
    
    try:
        # Usamos el divisor inteligente que respeta HTML
        chunks = smart_split(ai_response, limit=4000)
        
        for chunk in chunks:
            await msg.reply_text(chunk, parse_mode=constants.ParseMode.HTML)

    except Exception as e:
        # Fallback: Si falla el HTML, enviamos texto plano pero DIVIDIDO
        add_log_line(f"⚠️ Error enviando HTML: {e}. Reintentando texto plano.", level="WARNING")
        
        # Dividimos por longitud pura para evitar "Message is too long"
        plain_chunks = split_text_safe(ai_response, limit=4000)
        for p_chunk in plain_chunks:
            await msg.reply_text(p_chunk)