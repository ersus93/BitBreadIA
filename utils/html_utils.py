import math

def smart_split(text, limit=4000):
    """
    Divide un texto HTML largo en fragmentos seguros para Telegram.
    Maneja el cierre y reapertura de etiquetas <pre><code> para no romper el formato.
    """
    if len(text) <= limit:
        return [text]

    chunks = []
    while text:
        if len(text) <= limit:
            chunks.append(text)
            break

        # 1. Buscamos el mejor punto de corte (último salto de línea antes del límite)
        split_at = text.rfind('\n', 0, limit)
        
        # Si no hay saltos de línea (raro), cortamos en el límite duro
        if split_at == -1:
            split_at = limit

        chunk = text[:split_at]
        next_text = text[split_at:]

        # 2. Verificamos si hemos cortado dentro de un bloque de código
        # Contamos etiquetas de apertura y cierre en este fragmento
        open_pre = chunk.count("<pre>")
        close_pre = chunk.count("</pre>")
        
        open_code = chunk.count("<code>")
        close_code = chunk.count("</code>")

        # 3. Balanceamos el fragmento actual si quedó abierto
        # Nota: Asumimos que si hay <pre> también hay <code>, común en este bot
        tags_to_close = ""
        tags_to_reopen = ""

        if open_code > close_code:
            tags_to_close += "</code>"
            tags_to_reopen = "<code>" + tags_to_reopen
        
        if open_pre > close_pre:
            tags_to_close += "</pre>"
            tags_to_reopen = "<pre>" + tags_to_reopen

        # Cerramos tags en el chunk actual
        chunk += tags_to_close
        
        # Abrimos tags en el siguiente texto (al principio)
        if tags_to_reopen:
            next_text = tags_to_reopen + next_text

        chunks.append(chunk)
        text = next_text
    
    return chunks

def split_text_safe(text, limit=4000):
    """Divisor simple para texto plano (fallback)."""
    return [text[i:i+limit] for i in range(0, len(text), limit)]