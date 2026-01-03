import os
import httpx
import itertools
import json
import re
import random
from dotenv import load_dotenv
from utils.logger import add_log_line

load_dotenv()

class GroqManager:
    def __init__(self):
        keys_str = os.getenv("GROQ_API_KEYS", "")
        self.api_keys = [k.strip() for k in keys_str.split(",") if k.strip()]
        
        if not self.api_keys:
            single_key = os.getenv("GROQ_API_KEY")
            if single_key:
                self.api_keys = [single_key]
            else:
                self.api_keys = []
                print("⚠️ ADVERTENCIA: No se encontraron API KEYS en .env")
            
        if self.api_keys:
            random.shuffle(self.api_keys)

        self.key_cycle = itertools.cycle(self.api_keys)
        # Inicializar current_key de forma segura
        self.current_key = next(self.key_cycle) if self.api_keys else None
        
        self.requests_since_rotation = 0 
        self.ROTATION_LIMIT = 100
        
        self.model = os.getenv("MODEL_NAME", "llama-3.3-70b-versatile")
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"
        
        self.usage_stats = {k: 0 for k in self.api_keys}
        self.total_requests = 0
        self._load_stats()

    def _get_headers(self):
        return {
            "Authorization": f"Bearer {self.current_key}",
            "Content-Type": "application/json"
        }

    def rotate_key(self):
        if not self.api_keys: return
        old_key = self.current_key
        self.current_key = next(self.key_cycle)
        self.requests_since_rotation = 0
        
        add_log_line(f"🔄 Rotando API Key: ...{old_key[-4:]} -> ...{self.current_key[-4:]}")

    def _check_preventive_rotation(self):
        self.requests_since_rotation += 1
        if self.requests_since_rotation >= self.ROTATION_LIMIT:
            add_log_line(f"⚖️ Límite de {self.ROTATION_LIMIT} pedidos alcanzado. Rotación preventiva.")
            self.rotate_key()

    async def get_response(self, messages, model=None, temperature=0.3):
        """
        Ahora acepta un parámetro 'model'. Si es None, usa self.model (el del .env).
        """
        if not self.api_keys:
            return "❌ Error de configuración: No hay API Keys disponibles."

        # Determinar qué modelo usar
        target_model = model if model else self.model

        attempts = 0
        max_retries = len(self.api_keys)

        system_prompt = {
            "role": "system", 
            "content": (
                "Eres BitBread IA. Tu misión es actuar como un asistente híbrido: "
                "1. Si se te proporciona 'INFORMACIÓN OFICIAL' o contexto técnico, actúa como un experto estricto en ese dominio (BitBread/HACCP) y basa tu respuesta en esos datos. "
                "2. Si NO se proporciona contexto o la pregunta es general (saludos, cultura, código general), actúa como una IA útil, amable y experta en tecnología. "
                "Siempre responde usando formato HTML para Telegram (<b>negrita</b>, <i>cursiva</i>, listas)."
            )
        }

        messages_to_send = [system_prompt] + messages

        payload = {
            "model": target_model, # Usamos el modelo seleccionado
            "messages": messages_to_send,
            "temperature": temperature
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            while attempts < max_retries:
                try:
                    response = await client.post(
                        self.api_url, 
                        headers=self._get_headers(), 
                        json=payload
                    )

                    if response.status_code == 200:
                        data = response.json()
                        content = data['choices'][0]['message']['content']                 
                        content = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', content)                        
                        content = re.sub(r'(?m)^\* ', '• ', content)
                        
                        self.usage_stats[self.current_key] += 1
                        self.total_requests += 1
                        self._save_stats() # Guardar stats actualizado
                        self._check_preventive_rotation()
                        return content
                    
                    elif response.status_code in [429, 500, 503]:
                        add_log_line(f"⚠️ Error {response.status_code}. Rotando key...")
                        self.rotate_key()
                        attempts += 1
                    
                    else:
                        error_msg = f"Error API Groq {response.status_code}: {response.text}"
                        add_log_line(error_msg)
                        return f"⚠️ Error de API: {response.status_code}"

                except Exception as e:
                    add_log_line(f"❌ Excepción en GroqManager: {e}")
                    self.rotate_key()
                    attempts += 1

        return "🚫 El sistema está saturado. Intenta en un minuto."
    
    async def transcribe_audio(self, file_path):
        """
        Transcribe un archivo de audio usando Whisper en Groq.
        """
        if not self.api_keys:
            return "❌ Error: No hay API Keys."

        # URL Específica para transcribir (diferente a la de chat)
        transcription_url = "https://api.groq.com/openai/v1/audio/transcriptions"
        
        # Usamos Whisper Large V3 (el mejor para español/multilenguaje)
        model_id = "whisper-large-v3"

        attempts = 0
        max_retries = len(self.api_keys)

        async with httpx.AsyncClient(timeout=60.0) as client:
            while attempts < max_retries:
                try:
                    # Abrimos el archivo en modo binario
                    with open(file_path, "rb") as f:
                        files = {"file": (os.path.basename(file_path), f, "audio/m4a")}
                        data = {"model": model_id, "temperature": 0.0}
                        
                        # NOTA: No usamos self._get_headers() aquí porque 
                        # httpx debe gestionar el Content-Type para archivos multipart.
                        headers = {"Authorization": f"Bearer {self.current_key}"}

                        response = await client.post(
                            transcription_url, 
                            headers=headers, 
                            files=files, 
                            data=data
                        )

                    if response.status_code == 200:
                        self.usage_stats[self.current_key] += 1
                        self._save_stats()
                        self._check_preventive_rotation()
                        return response.json().get("text", "")
                    
                    elif response.status_code in [429, 500, 503]:
                        add_log_line(f"⚠️ Error {response.status_code} en Transcripción. Rotando key...")
                        self.rotate_key()
                        attempts += 1
                    else:
                        add_log_line(f"❌ Error API Audio {response.status_code}: {response.text}")
                        return None

                except Exception as e:
                    add_log_line(f"❌ Excepción en Transcripción: {e}")
                    self.rotate_key()
                    attempts += 1

        return None

    def get_stats(self):
        """Devuelve las estadísticas formateadas en HTML."""
        # Usamos self.total_requests y self.model que SÍ existen
        stats_txt = f"📊 <b>Uso de APIs Groq</b>\n"
        stats_txt += f"Total Requests: {self.total_requests}\n"
        stats_txt += f"Modelo: {self.model}\n\n"
        
        # Usamos self.usage_stats que SÍ existe
        for key, count in self.usage_stats.items():
            # Ocultamos la key por seguridad
            short_key = f"...{key[-4:]}" if len(key) > 4 else key
            stats_txt += f"🔑 {short_key}: {count} reqs\n"
            
        return stats_txt
    
    def _load_stats(self):
        """Carga las estadísticas desde el archivo JSON si existe."""
        stats_file = "data/api_stats.json"
        if not os.path.exists(stats_file):
            return

        try:
            with open(stats_file, 'r', encoding='utf-8') as f:
                saved_data = json.load(f)
                
            # Recuperar total global
            self.total_requests = saved_data.get("total_requests", 0)
            
            # Recuperar uso por key (solo si la key sigue existiendo en .env)
            saved_usage = saved_data.get("usage_stats", {})
            for key, count in saved_usage.items():
                if key in self.usage_stats:
                    self.usage_stats[key] = count
                    
            add_log_line("📈 Estadísticas cargadas correctamente.")
        except Exception as e:
            add_log_line(f"⚠️ Error cargando estadísticas: {e}")

    def _save_stats(self):
        """Guarda las estadísticas actuales en JSON."""
        stats_file = "data/api_stats.json"
        data = {
            "total_requests": self.total_requests,
            "usage_stats": self.usage_stats
        }
        try:
            # Asegurar que la carpeta data existe
            os.makedirs("data", exist_ok=True)
            with open(stats_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error guardando stats: {e}")


groq_ai = GroqManager()