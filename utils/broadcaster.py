import asyncio
from telegram.constants import ParseMode
from telegram.error import BadRequest, Forbidden
from utils.logger import add_log_line
from core.context_manager import delete_user_data

async def broadcast_message(bot, chat_ids, text, photo_id=None, parse_mode=ParseMode.HTML):
    """
    Envía mensaje a lista de chat_ids. 
    Si falla el formato HTML/Markdown, reintenta en texto plano.
    Maneja bloqueos de usuario limpiando la base de datos.
    """
    fallidos = {}
    sent_count = 0

    for chat_id in chat_ids:
        try:
            # 1. Intentamos enviar con formato (HTML por defecto en este bot)
            if photo_id:
                caption = text.strip() if text and text.strip() else None
                await bot.send_photo(
                    chat_id=int(chat_id),
                    photo=photo_id,
                    caption=caption,
                    parse_mode=parse_mode if caption else None
                )
            elif text:
                await bot.send_message(
                    chat_id=int(chat_id),
                    text=text,
                    parse_mode=parse_mode
                )
            
            sent_count += 1
            await asyncio.sleep(0.05) # Evitar Flood Limits

        except BadRequest as e:
            # 2. Si falla el formato (etiquetas mal cerradas, etc), reintentamos PLANO
            error_str = str(e)
            if "parse entities" in error_str or "can't find end" in error_str:
                try:
                    add_log_line(f"⚠️ Formato fallido para {chat_id}. Reenviando texto plano.")
                    if photo_id:
                        await bot.send_photo(
                            chat_id=int(chat_id),
                            photo=photo_id,
                            caption=text # Sin parse_mode
                        )
                    else:
                        await bot.send_message(
                            chat_id=int(chat_id),
                            text=text # Sin parse_mode
                        )
                    sent_count += 1
                except Exception as e2:
                    fallidos[chat_id] = f"Fallo definitivo: {e2}"
                    add_log_line(f"❌ Error total en {chat_id}: {e2}")
            else:
                # Otro tipo de BadRequest (ej: chat not found)
                fallidos[chat_id] = error_str
                add_log_line(f"❌ Error BadRequest en {chat_id}: {error_str}")

        except Forbidden:
            # 3. El usuario bloqueó al bot
            fallidos[chat_id] = "Bot Bloqueado"
            add_log_line(f"🗑️ Usuario {chat_id} bloqueó el bot. Eliminando datos.")
            delete_user_data(chat_id)

        except Exception as e:
            # 4. Errores generales
            fallidos[chat_id] = str(e)
            add_log_line(f"❌ Excepción en broadcast {chat_id}: {e}")

    return fallidos