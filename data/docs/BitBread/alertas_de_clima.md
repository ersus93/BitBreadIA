# 📚 DOCUMENTACIÓN DEL MÓDULO DE ALERTAS DE CLIMA - BitBread Alert Bot

## 📋 VISIÓN GENERAL

El **Módulo de Alertas de Clima** es un sistema integral que proporciona:
- ✅ Reportes meteorológicos detallados en tiempo real
- ✅ Suscripciones automáticas con alertas personalizadas
- ✅ Integración con IA para consejos inteligentes
- ✅ Sistema anti-spam avanzado
- ✅ Alertas globales de desastres naturales
- ✅ Soporte multi-idioma

## 🏗️ ARQUITECTURA DEL SISTEMA

### **1. `weather.py` - Controlador Principal**
**Ubicación:** `handlers/weather.py`
**Propósito:** Maneja todos los comandos y flujos de conversación relacionados con clima.

#### **Funciones Clave:**

| Función | Propósito | Estado de Conversación |
|---------|-----------|-----------------------|
| `weather_command()` | Menú principal de clima (comando `/w`) | - |
| `weather_subscribe_command()` | Inicia suscripción | `LOCATION_INPUT` |
| `location_handler()` | Procesa ubicación GPS/texto | `LOCATION_INPUT` |
| `weather_time_callback()` | Selecciona hora de alerta | ConversationHandler.END |
| `weather_settings_command()` | Configura alertas | - |
| `weather_toggle_callback()` | Activa/desactiva tipo de alerta | - |
| `responder_clima_actual()` | Genera reporte completo + IA | - |

#### **Estados de Conversación:**
```python
LOCATION_INPUT = range(1)  # Esperando ubicación del usuario
```

### **2. `weather_api.py` - Cliente API con Caché**
**Ubicación:** `utils/weather_api.py`
**Propósito:** Maneja todas las llamadas a OpenWeather API con sistema de caché inteligente.

#### **Clases Principales:**

| Clase | Descripción |
|-------|-------------|
| `WeatherAPICache` | Caché con TTL de 15 minutos y límite de 100 entradas |
| `WeatherAPI` | Cliente robusto con reintentos automáticos (3 intentos) |

#### **Endpoints Soportados:**
```python
- current_weather  # Clima actual
- forecast         # Pronóstico 5 días
- uvi              # Índice UV
- air_pollution    # Calidad del aire
- reverse_geocode  # Geocodificación inversa
```

### **3. `weather_manager.py` - Gestor de Suscripciones**
**Ubicación:** `utils/weather_manager.py`
**Propósito:** Administra suscripciones, historial y sistema anti-spam.

#### **Características Avanzadas:**

| Característica | Descripción |
|----------------|-------------|
| **ID Único de Evento** | Genera hash SHA256 para evitar duplicados |
| **Cooldown Inteligente** | Control por tipo de alerta (ej: 6h para lluvia) |
| **Etapas de Alerta** | Soporta `early` e `imminent` para mismo evento |
| **Retención de 7 días** | Historial automáticamente limpiado |

#### **Estructura de Datos:**
```json
{
  "local": {},      # Alertas por usuario
  "global": {},     # Eventos globales
  "events": {}      # Índice de eventos únicos
}
```

### **4. `weather_loop_v2.py` - Bucle de Fondo**
**Ubicación:** `core/weather_loop_v2.py`
**Propósito:** Ejecuta verificaciones periódicas y envía alertas automáticas.

#### **Tipos de Alerta:**

| Tipo | Condición | Cooldown |
|------|-----------|----------|
| **Rain** | Código 300-599 (lluvia/llovizna) | 6 horas |
| **Storm** | Código 200-299 (tormenta) | 6 horas |
| **UV High** | Índice UV ≥ 6 | 6 horas |
| **Daily Summary** | Hora configurada por usuario | 20 horas |

#### **Flujo del Bucle:**
```
1. Cargar todas las suscripciones activas
2. Por cada usuario:
   a. Obtener datos de API (con caché)
   b. Verificar condiciones de emergencia
   c. Verificar hora para resumen diario
   d. Enviar alertas si corresponden
3. Esperar 5 minutos
```

## 🚀 FLUJOS DE USUARIO

### **1. Consulta Manual de Clima**
```
Usuario: /w Madrid
       ↓
Geocodificar "Madrid"
       ↓
Obtener datos: actual + pronóstico + UV + AQI
       ↓
Generar reporte con IA
       ↓
Responder al usuario
```

### **2. Suscripción Automática**
```
Usuario: /weather_subscribe
       ↓
Solicitar ubicación (GPS o texto)
       ↓
Procesar ubicación + obtener zona horaria
       ↓
Mostrar clima actual confirmación
       ↓
Solicitar hora preferida (06:00, 07:00, etc.)
       ↓
Guardar suscripción en JSON
```

### **3. Alertas Automáticas**
```
Bucle cada 5 minutos:
   Para cada usuario suscrito:
      - Verificar lluvia/tormenta en próximas 4 horas
      - Verificar UV alto actual
      - Si es hora configurada: enviar resumen diario
      - Registrar envío para cooldown
```

## 🔧 CONFIGURACIÓN DE ALERTAS

### **Tipos Configurables:**
```python
alert_types = {
    "rain": True,              # Lluvia
    "storm": True,             # Tormenta
    "snow": True,              # Nieve/escarcha
    "uv_high": True,           # UV alto (≥6)
    "fog": True,               # Niebla
    "temp_high": True,         # Calor intenso
    "temp_low": True,          # Frío intenso
    "global_disasters": True,  # Desastres naturales globales
    "daily_summary": True      # Resumen diario
}
```

### **Horarios Disponibles:**
- **Mañana**: 06:00, 07:00, 08:00, 09:00, 10:00
- **Mediodía**: 12:00
- **Tarde**: 14:00, 18:00
- **Noche**: 20:00, 21:00, 22:00

## 🧠 INTEGRACIÓN CON IA

### **Consejos Inteligentes:**
El sistema utiliza `get_groq_weather_advice()` para:
- Recomendaciones de vestimenta basadas en temperatura
- Alertas de protección UV
- Consejos para lluvia/tormenta
- Sugerencias para actividades diarias

### **Parámetros de Análisis:**
```python
{
    "min_temp": float,        # Temperatura mínima del día
    "max_temp": float,        # Temperatura máxima del día
    "weather_ids": list[int], # IDs de condiciones climáticas
    "uv_max": float,          # Índice UV máximo
    "is_rainy": bool          # ¿Es día lluvioso?
}
```

## 🛡️ SISTEMA ANTI-SPAM

### **Mecanismos Implementados:**

| Mecanismo | Descripción |
|-----------|-------------|
| **ID Hash Único** | `SHA256(user_id + tipo + hora + coordenadas)` |
| **Cooldown por Tipo** | Tiempos específicos por tipo de alerta |
| **Etapas Separadas** | `early` vs `imminent` para mismo evento |
| **Límite Temporal** | No enviar eventos similares en <2h |
| **Retención Limitada** | Historial automáticamente purgado (7 días) |

### **Generación de ID de Evento:**
```python
def generate_event_id(user_id, alert_type, event_time, weather_id, lat, lon):
    # Redondea a hora más cercana
    # Incluye coordenadas (redondeadas a 2 decimales ≈1km)
    # Genera hash SHA256 corto (16 chars)
```

## 🌍 ALERTAS GLOBALES DE DESASTRES

### **Integración con `global_disasters_loop`:**
```python
# En weather_manager.py
"global_disasters": True  # Activar/desactivar en config

# En weather_loop_v2.py
if alert_types.get('global_disasters', True):
    # Incluir eventos globales en resumen
```

### **Buffer de Eventos Globales:**
```python
GLOBAL_EVENTS_BUFFER_PATH  # Almacena últimos 48h de eventos
```

## 📊 FORMATOS DE MENSAJE

### **Reporte Completo:**
```
🌤️ Clima en Madrid, ES
—————————————————
• Cielo despejado
• 🌡 Temperatura: 22.5°C
• 🤔 Sensación: 23.1°C
• 📈 Máx: 25.0°C | 📉 Mín: 18.0°C
• 💧 Humedad: 65%
• 💨 Viento: 3.5 m/s
• ☀️ UV: 4.2 (Moderado)
• 🌫️ Calidad aire: Bueno (AQI: 2)
• 🕐 Hora local: 14:30
• 🌅 Amanecer: 06:45
• 🌇 Atardecer: 21:15

📅 Próximas horas:
  15:00: 23°C ☀️ Cielo despejado
  18:00: 21°C 🌤️ Nubes dispersas
  21:00: 19°C 🌙 Cielo despejado

💡 Consejos de 🤖 @BitBreadIAbot:
—————————————————
👕 Ropa: Camiseta o camisa ligera.
🧴 Sol: Índice UV moderado, protección recomendada.
```

### **Alerta de Emergencia:**
```
🌧️ Alerta de Lluvia en Madrid
—————————————————
Se espera: Lluvia moderada
🕐 Hora aprox: 16:00
☔ ¡No olvides el paraguas!

[Publicidad aleatoria]
```

## 🔄 INTEGRACIÓN CON SISTEMA PRINCIPAL

### **En `bbalert.py`:**
```python
# Iniciar bucle de clima
asyncio.create_task(weather_alerts_loop(app.bot))

# Registrar handlers
app.add_handler(weather_conversation_handler)  # DEBE IR PRIMERO
app.add_handler(CommandHandler("w", weather_command))
app.add_handlers(weather_callback_handlers)    # Al final
```

### **Dependencias:**
```python
from core.weather_loop_v2 import weather_alerts_loop
from handlers.weather import (
    weather_command, 
    weather_conversation_handler,
    weather_callback_handlers
)
```

## 🐛 SOLUCIÓN DE PROBLEMAS COMUNES

### **Problema: "Message is not modified"**
**Causa:** Intentar editar mensaje con mismo contenido
**Solución:** En `weather_settings_command()`:
```python
except BadRequest as e:
    if "Message is not modified" in str(e):
        if update.callback_query:
            await update.callback_query.answer("✅ Cambio aplicado")
```

### **Problema: Ubicación no encontrada**
**Causa:** Fallo en geocodificación
**Solución:** Usar reverse geocoding como respaldo:
```python
if not city_name or city_name == "Ubicación":
    result = reverse_geocode(lat, lon)
    if result:
        city_name, country = result
```

### **Problema: Alertas duplicadas**
**Causa:** Cooldown insuficiente
**Solución:** Verificar con `should_send_alert()`:
```python
if should_send_alert(user_id, 'rain', cooldown_hours=6):
    # Enviar alerta
    update_last_alert_time(user_id, 'rain')
```

## 📈 MÉTRICAS Y LOGGING

### **Logs Clave:**
```python
add_log_line("🌦️ Iniciando Sistema de Clima...")
add_log_line(f"✅ Usuario {user_id} suscrito: {city}")
add_log_line(f"⚠️ Error API clima para {user_id}: {e}")
add_log_line(f"📝 Alerta registrada: {alert_type} para user {user_id}")
```

### **Archivos de Datos:**
```
data/
├── weather_subs.json          # Suscripciones de usuarios
├── weather_alerts_history.json # Historial de alertas
└── global_events_buffer.json  # Buffer de eventos globales
```

## 🔮 MEJORAS FUTURAS

### **Prioridad Alta:**
1. **Alertas por Radio:** Añadir radio de impacto (ej: 50km alrededor)
2. **Múltiples Ubicaciones:** Permitir suscripción a varias ciudades
3. **Preferencias de Viaje:** Alertas para rutas específicas

### **Prioridad Media:**
1. **Gráficos:** Integrar gráficos de temperatura/lluvia
2. **Comparativas:** Comparar con días anteriores
3. **Webhook:** Notificaciones push para emergencias

### **Prioridad Baja:**
1. **Crowdsourcing:** Reportes de usuarios
2. **Predicción IA:** Modelo propio de predicción
3. **Integración Calendario:** Alertas basadas en eventos

---

## 📖 RESUMEN PARA CHATBOT

**Preguntas comunes que puede responder:**
- "¿Cómo me suscribo a alertas de clima?"
- "¿Qué tipos de alertas puedo recibir?"
- "¿Cómo cambiar la hora de mis alertas diarias?"
- "¿Por qué no recibí mi alerta de lluvia?"
- "¿Cómo consultar el clima de otra ciudad?"

**Comandos clave a recordar:**
- `/w` o `/weather` - Menú principal de clima
- `/weather_subscribe` - Suscribirse a alertas
- `/weather_settings` - Configurar alertas
- `/w Madrid` - Consultar clima de Madrid

**Características destacadas:**
- ✅ Consejos de IA personalizados
- ✅ Alertas de desastres globales
- ✅ Sistema anti-spam robusto
- ✅ Soporte multi-idioma
- ✅ Caché inteligente para API

Esta documentación proporciona una visión completa del módulo de clima para que el chatbot pueda responder preguntas técnicas, de uso y de solución de problemas relacionadas con las alertas meteorológicas del bot BitBread.