import datetime
import os

LOG_FILE = "bot_activity.log"

def add_log_line(message):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted_msg = f"[{timestamp}] {message}"
    
    print(formatted_msg) # Imprimir en consola
    
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(formatted_msg + "\n")
    except Exception as e:
        print(f"Error escribiendo log: {e}")

def get_last_logs(lines=10):
    if not os.path.exists(LOG_FILE):
        return "Log vacío."
    
    try:
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            all_lines = f.readlines()
            return "".join(all_lines[-lines:])
    except:
        return "Error leyendo logs."