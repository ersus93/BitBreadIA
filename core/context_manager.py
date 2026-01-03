import json
import os

# Ruta donde se guardará el historial
DATA_DIR = "data"
CONTEXT_FILE = os.path.join(DATA_DIR, "user_context.json")
SETTINGS_FILE = os.path.join(DATA_DIR, "user_settings.json")

# Aseguramos que la carpeta data exista
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)


def _load_json(filepath):
    """Carga un archivo JSON genérico."""
    if not os.path.exists(filepath):
        return {}
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}

def _save_json(filepath, data):
    """Guarda datos en un archivo JSON."""
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error guardando {filepath}: {e}")

        
def _load_data():
    """Carga el archivo JSON de historial."""
    if not os.path.exists(CONTEXT_FILE):
        return {}
    try:
        with open(CONTEXT_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}

def _save_data(data):
    """Guarda los cambios en el archivo JSON."""
    try:
        with open(CONTEXT_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error guardando contexto: {e}")

def add_message(user_id, role, content):
    """Agrega un mensaje al historial del usuario."""
    data = _load_data()
    str_id = str(user_id)
    
    if str_id not in data:
        data[str_id] = []
    
    # Agregamos el nuevo mensaje
    data[str_id].append({"role": role, "content": content})
    
    # Límite de memoria (opcional: guarda solo los últimos 20 mensajes para no saturar)
    if len(data[str_id]) > 20:
        data[str_id] = data[str_id][-20:]
        
    _save_data(data)

def get_user_context(user_id):
    """Obtiene la lista de mensajes para enviar a la API."""
    data = _load_data()
    return data.get(str(user_id), [])

def clear_context(user_id):
    """Borra el historial de un usuario (/newchat)."""
    data = _load_data()
    str_id = str(user_id)
    
    if str_id in data:
        del data[str_id]
        _save_data(data)

def set_user_model(user_id, model_id):
    """Guarda el modelo preferido del usuario."""
    data = _load_json(SETTINGS_FILE)
    str_id = str(user_id)
    
    if str_id not in data:
        data[str_id] = {}
    
    data[str_id]["model"] = model_id
    _save_json(SETTINGS_FILE, data)

def get_user_model(user_id, default_model):
    """Obtiene el modelo del usuario o el default si no ha elegido."""
    data = _load_json(SETTINGS_FILE)
    str_id = str(user_id)
    return data.get(str_id, {}).get("model", default_model)

def get_all_user_ids():
    """Retorna una lista con los IDs de todos los usuarios que han hablado con el bot."""
    # Combinamos usuarios del contexto y de settings para tener la lista más completa
    context_data = _load_data()
    settings_data = _load_json(SETTINGS_FILE)
    
    all_ids = set(context_data.keys()) | set(settings_data.keys())
    return list(all_ids)

def delete_user_data(user_id):
    """Elimina datos de un usuario si bloquea el bot (Limpieza de DB)."""
    str_id = str(user_id)
    
    # Borrar de contexto
    c_data = _load_data()
    if str_id in c_data:
        del c_data[str_id]
        _save_data(c_data)
        
    # Borrar de settings
    s_data = _load_json(SETTINGS_FILE)
    if str_id in s_data:
        del s_data[str_id]
        _save_json(SETTINGS_FILE, s_data)