import math

def smart_split(text, limit=4000):
    """
    Divide texto HTML en fragmentos seguros para Telegram.
    Balancea etiquetas: <pre>, <code>, <b>, <i>, <u>, <s>.
    """
    if len(text) <= limit:
        return [text]

    chunks = []
    # Lista de etiquetas que debemos vigilar si quedan abiertas
    tags_to_track = ["pre", "code", "b", "i", "u", "s"]

    while text:
        if len(text) <= limit:
            chunks.append(text)
            break

        # 1. Buscar punto de corte
        split_at = text.rfind('\n', 0, limit)
        if split_at == -1:
            split_at = text.rfind(' ', 0, limit) # Intentar en un espacio si no hay saltos
        if split_at == -1:
            split_at = limit # Corte duro si no hay opción

        chunk = text[:split_at]
        next_text = text[split_at:]

        # 2. Balancear etiquetas
        tags_to_close = ""
        tags_to_reopen = ""

        # Revisamos cada tipo de etiqueta
        for tag in tags_to_track:
            # Contamos aperturas y cierres simples
            # Nota: Esto asume HTML bien formado por la IA.
            # No arregla etiquetas cruzadas (<b><i>...</b></i>), eso debe venir bien de la IA.
            start_tag = f"<{tag}>"
            end_tag = f"</{tag}>"
            
            count_open = chunk.count(start_tag)
            count_close = chunk.count(end_tag)

            if count_open > count_close:
                tags_to_close += end_tag
                tags_to_reopen = start_tag + tags_to_reopen
        
        # Cerramos en el chunk actual
        chunk += tags_to_close
        
        # Abrimos en el siguiente texto
        if tags_to_reopen:
            next_text = tags_to_reopen + next_text

        chunks.append(chunk)
        text = next_text
    
    return chunks

def split_text_safe(text, limit=4000):
    """Divisor simple para texto plano (fallback)."""
    return [text[i:i+limit] for i in range(0, len(text), limit)]