# 📚 DOCUMENTACIÓN DEL MÓDULO BTC ALERTS - BitBread Bot

## 📋 VISIÓN GENERAL

El **Módulo BTC Alerts** es un sistema profesional de análisis técnico y monitoreo en tiempo real de Bitcoin que ofrece:
- ✅ Análisis multi-temporalidad (1h, 2h, 4h, 8h, 12h, 1d, 1w)
- ✅ Integración dual: Binance API + TradingView
- ✅ Sistema de alertas automáticas por cruce de niveles Fibonacci
- ✅ Análisis técnico avanzado con más de 15 indicadores
- ✅ Suscripciones personalizadas por timeframe
- ✅ Mensajes enriquecidos con recomendaciones profesionales

## 🏗️ ARQUITECTURA DEL SISTEMA

### **1. `btc_advanced_analysis.py` - Motor de Análisis**
**Ubicación:** `core/btc_advanced_analysis.py`
**Propósito:** Realiza análisis técnico profesional con indicadores avanzados.

#### **Indicadores Calculados:**

| Indicador | Parámetros | Propósito |
|-----------|------------|-----------|
| **EMA** | 9, 20, 50, 200 | Tendencia a corto, medio y largo plazo |
| **RSI** | 14 periodos | Momentum y sobrecompra/sobreventa |
| **Stochastic** | K=14, D=3, smooth=3 | Ciclos de mercado |
| **CCI** | 20 periodos | Identificación de tendencias |
| **Awesome Oscillator** | - | Momentum alcista/bajista |
| **ADX** | 14 periodos | Fuerza de tendencia |
| **MACD** | 12, 26, 9 | Convergencia/divergencia |
| **ATR** | 14 periodos | Volatilidad |
| **Ichimoku Kijun-sen** | 26 periodos | Soporte/resistencia dinámica |

#### **Puntuación de Momentum:**
```
Sistema de scoring (0-10+ puntos):
• Tendencia (EMAs): +1 por cada EMA superada
• RSI: +1 si >50, +2 si <30 (sobreventa)
• Stochastic: +1 si <20 (sobrevendido)
• MACD: +1 si histograma positivo
• ADX: +2 si >25 con tendencia clara

Señales resultantes:
≥6 puntos: "COMPRA FUERTE" 🚀
2-5 puntos: "COMPRA" 📈
-1 a 1: "NEUTRAL" ⚖️
-5 a -2: "VENTA" 📉
≤-6: "VENTA FUERTE" 🐻
```

### **2. `btc_handlers.py` - Controlador de Comandos**
**Ubicación:** `handlers/btc_handlers.py`
**Propósito:** Maneja interacciones de usuario a través de Telegram.

#### **Comandos Principales:**

| Comando | Función | Parámetros |
|---------|---------|------------|
| `/btcalerts` | Menú principal de BTC | `[TV] [1h|2h|4h|8h|12h|1d|1w]` |
| `toggle_btc_alerts` | Activa/desactiva suscripción | timeframe específico |
| `btc_switch_view` | Cambia entre Binance/TradingView | fuente + temporalidad |

#### **Vistas Disponibles:**

| Vista | Fuente de Datos | Características |
|-------|----------------|-----------------|
| **Binance (Local)** | API Binance + análisis propio | Análisis avanzado, confluencias, Ichimoku |
| **TradingView** | TradingView TA API | Recomendaciones oficiales, pivotes estándar |

### **3. `btc_loop.py` - Bucle de Monitoreo**
**Ubicación:** `core/btc_loop.py`
**Propósito:** Monitorea BTC en tiempo real y envía alertas automáticas.

#### **Lógica de Niveles Fibonacci:**

```
Niveles calculados (basados en 100 velas anteriores):
• R3: Pivot + (Rango × 1.272) → Extensión máxima
• R2: Pivot + (Rango × 0.618) → Fibonacci 61.8%
• R1: Pivot + (Rango × 0.382) → Fibonacci 38.2%
• P: (High + Low + Close) / 3 → Pivot central
• S1: Pivot - (Rango × 0.382)
• S2: Pivot - (Rango × 0.618)
• S3: Pivot - (Rango × 1.272)

Golden Pocket (FIB_618): Low + (Rango × 0.618)
Kijun-sen: (High26 + Low26) / 2 (Ichimoku)
```

#### **Tipos de Alertas:**

| Nivel | Condición | Significado |
|-------|-----------|-------------|
| **R3** | Price > R3 | Extensión máxima, posible agotamiento |
| **R2** | Price > R2 | Momentum fuerte, objetivo R3 |
| **R1** | Price > R1 | Zona de fortaleza alcista |
| **FIB_618_UP** | Price > Golden Pocket | Recuperación crítica, reversión |
| **P_UP** | Price > Pivot | Sesgo positivo intradía |
| **P_DOWN** | Price < Pivot | Sesgo negativo intradía |
| **FIB_618_DOWN** | Price < Golden Pocket | Pérdida soporte institucional |
| **S1** | Price < S1 | Primer soporte perdido |
| **S2** | Price < S2 | S2 perdido, debilidad estructural |
| **S3** | Price < S3 | Extensión bajista, pánico |

### **4. `btc_manager.py` - Gestor de Suscripciones**
**Ubicación:** `utils/btc_manager.py`
**Propósito:** Administra suscripciones y estado del sistema.

#### **Estructura de Datos:**

```json
{
  "user_id": {
    "subscriptions": ["4h", "1d", "1w"]
  }
}

{
  "4h": {
    "last_candle_time": 1736020800000,
    "levels": { ... },
    "alerted_levels": ["P_UP", "R1"]
  },
  "1d": { ... }
}
```

#### **Funciones Clave:**
- `toggle_btc_subscription()`: Activa/desactiva timeframe
- `get_btc_subscribers()`: Obtiene usuarios por timeframe
- `load_btc_state()`: Carga estado multi-temporal
- `save_btc_state()`: Guarda estado con estructura jerárquica

### **5. `tv_helper.py` - Integración TradingView**
**Ubicación:** `utils/tv_helper.py`
**Propósito:** Obtiene datos e indicadores de TradingView.

#### **Datos Obtenidos:**

| Categoría | Datos | Uso |
|-----------|-------|-----|
| **Precios** | current_price, close | Precio actual |
| **Pivotes** | R1-R3, P, S1-S3 | Niveles estándar |
| **Indicadores** | RSI, MACD, SMA50, SMA200 | Análisis técnico |
| **Volumen** | Volume, ATR | Volatilidad y actividad |
| **Recomendación** | RECOMMENDATION, BUY/SELL counts | Señal oficial |

## 🔄 FLUJOS DE TRABAJO

### **1. Consulta Manual del Usuario**
```
Usuario: /btcalerts 4h
       ↓
Determinar fuente (Binance/TV)
       ↓
Obtener velas (1000 periodos)
       ↓
Calcular indicadores avanzados
       ↓
Determinar niveles Fibonacci
       ↓
Analizar momentum y tendencia
       ↓
Generar mensaje con:
  - Señal principal
  - Score compra/venta
  - Niveles clave
  - Recomendaciones
       ↓
Mostrar teclado interactivo
```

### **2. Suscripción a Alertas**
```
Usuario: Clica botón "🔔 4h"
       ↓
Toggle en btc_manager
       ↓
Actualizar teclado (🔔→🔕)
       ↓
Confirmar con notificación flotante
       ↓
Usuario recibe:
  - Alertas de cruce de niveles
  - Actualizaciones de vela
  - Cambios de momentum
```

### **3. Monitoreo Automático (Loop)**
```
Cada 60 segundos:
  Para cada timeframe (1h, 2h, 4h, 8h, 12h, 1d, 1w):
    1. Obtener velas Binance
    2. Verificar si es vela nueva
    3. Si es nueva:
        - Recalcular niveles
        - Determinar posición inicial
        - Enviar resumen de sesión
    4. Monitorear cruces:
        - Comparar precio con niveles
        - Si cruza umbral (0.1%):
          • Generar alerta enriquecida
          • Enviar a suscriptores
          • Marcar como alertado
    5. Guardar estado
```

## 🎯 SISTEMA DE ALERTAS

### **Estructura de Mensajes de Alerta:**

```
🚀 *Ruptura R3 (4H)*
—————————————————
📊 El precio entra en zona de extensión máxima.

*Contexto Técnico:*
📈 Momentum: COMPRA FUERTE
⚖️ Score: 8 Compra | 2 Venta
• Clave: Tendencia Alcista (Sobre todas las EMAs)

*Detalles del Cruce:*
🧗 Nivel: R3 ($68,500)
💰 Precio: $68,750
🎯 Objetivo: $71,925

⚡ *Recomendación:*
_Zona de toma de ganancias. Precaución extrema._

⏳ Marco Temporal: 4H

[Publicidad aleatoria]
```

### **Lógica de Pre-alertas en Nueva Vela:**
Cuando se detecta una vela nueva, el sistema analiza la posición inicial y pre-configura alertas:

```python
# Si precio inicia sobre R3
pre_filled_alerts = ['P_UP', 'R1', 'R2', 'R3']
status_msg = "Extrema euforia. BTC inicia sesión sobre R3."
status_icon = "🚀"

# Si precio inicia bajo S3
pre_filled_alerts = ['P_DOWN', 'S1', 'S2', 'S3']
status_msg = "Pánico extremo. BTC bajo S3."
status_icon = "🕳️"
```

## 🔧 CONFIGURACIÓN Y PERSONALIZACIÓN

### **Timelines Soportados:**

| Timeframe | Duración Vela | Lookback Análisis | Uso Recomendado |
|-----------|---------------|-------------------|-----------------|
| **1h** | 1 hora | 100 velas (4 días) | Trading intradía |
| **4h** | 4 horas | 100 velas (17 días) | Swing trading |
| **1d** | 1 día | 100 velas (3 meses) | Inversión media |
| **1w** | 1 semana | 100 velas (2 años) | Inversión largo plazo |

### **Umbrales Configurables:**

| Parámetro | Valor | Descripción |
|-----------|-------|-------------|
| `threshold` | 0.001 (0.1%) | Margen para considerar cruce |
| `lookback_window` | 100 velas | Período para cálculo Fibonacci |
| `k_look` | 26 velas | Período para Ichimoku Kijun-sen |
| `cooldown_alert` | Sin repetición | No re-alerta mismo nivel |

## 📊 INTEGRACIÓN CON APIS EXTERNAS

### **Binance API:**

```python
Endpoints usados:
• https://api.binance.com/api/v3/klines
• Parámetros: symbol=BTCUSDT, interval=[1h-1w], limit=1000

Datos obtenidos:
[
  open_time, open, high, low, close, volume,
  close_time, quote_volume, trades,
  taker_buy_base, taker_buy_quote, ignore
]
```

### **TradingView TA API:**

```python
Configuración:
• Exchange: BINANCE
• Screener: CRYPTO
• Interval: mapeado automático
• Símbolo: BTCUSDT

Indicadores obtenidos:
• Pivot.M.Classic.[R1-R3, S1-S3, Middle]
• RSI, MACD, SMA50, SMA200, ATR
• Volume, recomendación, scores
```

## 🛡️ MANEJO DE ERRORES Y ROBUSTEZ

### **Sistemas de Fallback:**

```python
# En btc_loop.py - Múltiples endpoints
endpoints = [
    "https://api.binance.us/api/v3/klines",
    "https://api.binance.com/api/v3/klines",
    "https://api1.binance.com/api/v3/klines"
]

# En btc_advanced_analysis.py - Valores por defecto
if ema is not None:
    df[f'EMA_{length}'] = ema
else:
    df[f'EMA_{length}'] = df['close']  # Fallback seguro
```

### **Validación de Datos:**

```python
# Verificar datos suficientes
if df is None or len(df) < 200:
    return None  # No analizar si hay pocos datos

# Limpieza de NaN
df.fillna(0, inplace=True)

# Conversión segura de tipos
try:
    price = float(df.iloc[-1]['close'])
except:
    price = 0
```

## 🚀 OPTIMIZACIONES DE RENDIMIENTO

### **Caching Inteligente:**
- Velas se obtienen una vez por timeframe por ciclo
- Análisis técnico se realiza una vez por vela nueva
- Estado se guarda solo cuando hay cambios

### **Procesamiento Asíncrono:**
```python
# En btc_loop.py
await asyncio.sleep(60)  # Espera principal
await asyncio.sleep(0.5)  # Entre timeframes

# Envío paralelo de mensajes
await _enviar_msg_func(msg, subs, ...)
```

## 🔮 CARACTERÍSTICAS FUTURAS

### **Prioridad Alta:**
1. **Backtesting:** Pruebas históricas de estrategias
2. **Alertas Personalizadas:** Niveles personalizados por usuario
3. **Múltiples Pares:** Extender a ETH, SOL, etc.

### **Prioridad Media:**
1. **Gráficos Inline:** Mini-gráficos en Telegram
2. **Notificaciones Push:** Para alertas críticas
3. **Webhook Externo:** Integración con otros sistemas

### **Prioridad Baja:**
1. **Trading Automático:** Ejecución de órdenes
2. **Análisis Sentimiento:** Integración con noticias
3. **Machine Learning:** Predicción con modelos propios

## 📖 RESUMEN PARA CHATBOT

### **Preguntas Comunes que Puede Responder:**
- "¿Cómo me suscribo a alertas de BTC?"
- "¿Qué significa la señal 'COMPRA FUERTE'?"
- "¿Cómo cambio entre vista Binance y TradingView?"
- "¿Por qué no recibí mi alerta de cruce?"
- "¿Qué timeframe es mejor para trading?"

### **Comandos Clave a Recordar:**
- `/btcalerts` - Menú principal de BTC
- `/btcalerts 4h TV` - Ver análisis 4h en TradingView
- `🔔 4h` - Botón para suscribirse a alertas 4h
- `📊 Ver Análisis PRO` - Ver análisis técnico completo

### **Conceptos Técnicos Importantes:**
- **Pivot Central:** Punto de equilibrio del mercado
- **Golden Pocket (61.8%):** Nivel crítico de Fibonacci
- **Kijun-sen:** Soporte/resistencia dinámica de Ichimoku
- **ATR:** Volatilidad promedio del mercado
- **Momentum Score:** Sistema de puntuación 0-10+

### **Características Destacadas:**
- ✅ Análisis dual (Binance + TradingView)
- ✅ 7 timeframes diferentes
- ✅ Alertas automáticas con cooldown
- ✅ Mensajes enriquecidos con iconos
- ✅ Sistema anti-spam inteligente
- ✅ Integración con publicidad

---

Esta documentación proporciona una visión completa del módulo BTC Alerts para que el chatbot pueda responder preguntas técnicas, de uso y de solución de problemas relacionadas con el monitoreo y análisis de Bitcoin en el bot BitBread.