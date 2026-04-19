# Skill: Seguimiento post-inversión — v4

## Propósito
Comparar el estado ACTUAL del portafolio del usuario contra el plan ORIGINAL entregado en una sesión previa, detectar desviaciones, generar alertas semáforo y recomendar acciones (rebalanceo, DCA, cierre, ampliación) sin inventar números.

## Principio clave — cómo funciona la "memoria" entre sesiones
Claude NO recuerda sesiones anteriores. La continuidad se logra por **persistencia externa**: el plan_template.md al final de cada plan nuevo incluye un bloque `BASELINE DE SEGUIMIENTO` en JSON. El usuario lo guarda y lo pega en la nueva sesión cuando dice "revisa mi portafolio". Si no lo tiene, el agente lo reconstruye preguntando al usuario (nunca inventando).

Las posiciones ACTUALES se leen directamente del MCP de eToro (`get_portfolio`), así que la parte "qué tengo hoy" está resuelta. Lo que no está en ningún MCP es el plan original (tesis, pesos objetivo, SL/TP, catalizadores) — eso vive en el BASELINE.

## Activación
- Usuario escribe cualquiera de: "revisa mi portafolio", "cómo va el plan", "seguimiento", "rebalancear", "review portfolio".
- Usuario pega un bloque `BASELINE DE SEGUIMIENTO` (JSON) de una sesión previa.
- Final de cada plan nuevo: el agente deja el bloque BASELINE para la próxima revisión.

## Fases del protocolo

### Fase A — Reconstruir el baseline (plan original)
Intentar en este orden hasta tener el baseline:

1. **Si el usuario pegó el bloque `BASELINE DE SEGUIMIENTO`** → parsearlo y saltar a Fase B. Es la vía canónica.
2. **Si no lo pegó pero hay cuenta eToro conectada** → llamar `etoro-server.get_portfolio` primero para tener contexto de lo que tiene hoy. Luego preguntar al usuario: "Veo tus posiciones actuales en eToro. Para compararlas contra el plan original, ¿puedes pegarme el bloque BASELINE DE SEGUIMIENTO del plan que te generé, o prefieres que lo reconstruyamos juntos?"
3. **Si no hay baseline ni forma de recuperarlo** → reconstruirlo con preguntas mínimas, UNA por mensaje:
   - Capital total del plan original + fecha de inicio.
   - Perfil de riesgo declarado (conservador / moderado / agresivo).
   - Para cada posición: ticker, %_objetivo, precio_entrada, venue, tesis en una línea.

NUNCA asumas el baseline. Si falta data crítica (precios de entrada, pesos objetivo), pregunta. Vale usar precio de mercado del día del plan como proxy SOLO si el usuario confirma que no tiene el dato real — etiquetarlo `(proxy)` en todos los cálculos.

### Fase B — Capturar posiciones actuales

Fuente primaria — **eToro MCP**:
- `etoro-server.get_portfolio` → devuelve `positions[]` con ticker, cantidad, precio de entrada real, valor actual, `unrealizedPnL` ya calculado por la plataforma, más `credit` (cash libre) y `mirrors` (copy trading activo).
- Esto es la fuente de verdad para posiciones en eToro. No pedir al usuario lo que la plataforma ya expone.

Fuente secundaria — **posiciones fuera de eToro** (Binance, Aave, MetaTrader, etc.):
- MetaTrader → `metatrader.get_all_positions` + `metatrader.get_account_info`.
- Binance / DEX / wallets → preguntar al usuario en UNA pregunta estructurada: "Para las posiciones fuera de eToro, pégame: ticker, cantidad, precio de entrada, venue".

Precios actuales para validación cruzada o si falta:
- Cripto → `coingecko.get_simple_price`.
- Equity / ETF → `yahoo-finance.yfinance_get_ticker_info` (`regularMarketPrice`).
- Forex → `metatrader.get_symbol_price` o `alphavantage`.
- eToro (cualquier clase) → `etoro-server.get_rates` con el instrumentId (útil para confirmar el precio del plan).

### Fase C — Calcular desviaciones (usar tools, no estimar a ojo)

Para cada posición del baseline, calcular y mostrar:
- **P&L absoluto**: `cantidad × (precio_actual − precio_entrada)`.
- **P&L porcentual**: `(precio_actual / precio_entrada) − 1`.
- Para posiciones en eToro, usar el `unrealizedPnL` que ya devuelve `get_portfolio` — no recalcular, solo verificar que cuadra.
- **Peso actual**: `valor_actual_posición / valor_total_portfolio`.
- **Desviación de peso**: `peso_actual − peso_objetivo` (en puntos porcentuales).
- **P&L total del portafolio**: suma de P&L absolutos / capital total del plan.
- **Tiempo transcurrido**: días desde `fecha_inicio` del baseline.

Identificar también:
- Posiciones NUEVAS (están hoy pero no en el baseline) → marcar como "fuera de plan".
- Posiciones ELIMINADAS (estaban en el baseline, no están hoy) → preguntar al usuario qué pasó (cerradas manualmente, SL, TP).

Si hay CFDs o posiciones apalancadas, recalcular **stress test con los pesos ACTUALES** (no los objetivo) vía `calculate_scenarios` / `stress_test_portfolio` para saber cuánto se arriesga HOY, no cuánto se planificaba arriesgar.

Si hubo rebalanceos o cierres desde la última revisión, recalcular **correlación actual** entre las posiciones vivas vía `calculate_correlation` — la correlación cambia con el tiempo y puede invalidar una de las tesis del plan original.

### Fase D — Diagnóstico con alertas semáforo

Clasificar cada posición (y el portafolio global) según estos umbrales:

```
🔴 CRÍTICO — acción en ≤ 48h
  - Pérdida absoluta > 15% en cualquier posición
  - SL técnico del plan original alcanzado (ver technical_skill.md en el baseline)
  - DeFi APY cayó > 50% vs baseline
  - Copy trader: drawdown > 20% o cambio de estrategia detectado
  - Desviación de peso > 15 p.p. vs objetivo
  - Correlación recalculada > 0.85 entre 2 posiciones grandes del portafolio

🟡 ATENCIÓN — revisar en días
  - Pérdida entre 5% y 15%
  - Correlación recalculada entre 0.7 y 0.85
  - Un vertical > 40% del portafolio total
  - Desviación de peso entre 5 y 15 p.p.
  - Earnings de una acción del plan en < 7 días
    (consultar yfinance_get_ticker_info → earningsTimestampStart)
  - Stress test severo actual excede el del plan original en > 10 p.p.

🟢 OK
  - P&L dentro del rango base proyectado
  - Asignación dentro de ±5 p.p. del objetivo
  - Correlaciones estables
```

Para CADA alerta, proponer una acción concreta basada en las reglas del plan original y de `risk_rules.md`:

- **Desviación > 5 p.p.** → rebalancear. Indicar cantidad exacta a vender/comprar en USD.
- **Posición +50% vs entrada** → realizar parcial (vender 25%) y mover stop a break-even.
- **Posición −20% con fundamentales intactos** → DCA SOLO si: (a) perfil lo permite, (b) hay capital nuevo, (c) la tesis del baseline sigue viva. Si la tesis cambió, no es DCA, es cierre.
- **SL técnico alcanzado** → cerrar. No negociar con el SL del plan.
- **Capital nuevo disponible** → asignar a la posición más subponderada que siga dentro de tesis.

### Fase E — Contexto fiscal Colombia

Si hubo cierres realizados desde la última revisión o el rebalanceo propuesto implica cierres:
- Llamar `calculate_tax_impact` por cada operación cerrada o a cerrar.
- Mostrar impuesto DIAN acumulado del año en curso.
- Delegar reglas específicas a `tax_colombia.md`.
- Si el rebalanceo genera impuesto significativo, ofrecer alternativa de rebalanceo "solo con capital nuevo" que no dispare evento gravable.

### Fase F — Entregar el reporte de seguimiento

Estructura obligatoria (es un artifact más liviano que el plan_template, NO los 4 tabs del plan):

```
🎯 SEGUIMIENTO — [fecha DD-MM-AAAA] | [N días desde el plan original]

1. RESUMEN EJECUTIVO (3 líneas máximo)
   - P&L total: +/−X% ($Y de $Z inicial) — fuente: eToro get_portfolio
   - Alertas: N 🔴 + M 🟡 + K 🟢
   - Acción principal recomendada (o "sin acción requerida")

2. POSICIÓN POR POSICIÓN (tabla)
   | Ticker | Venue | Peso actual | Peso obj. | Desv p.p. | P&L % | P&L $ | Estado |
   Posiciones nuevas (fuera del plan) en una fila marcada "⚠️ fuera de plan".
   Posiciones cerradas desde última revisión listadas aparte con motivo y P&L realizado.

3. ALERTAS 🔴 / 🟡 (ordenadas por gravedad)
   Por cada alerta:
   - Qué pasó (con números)
   - Por qué es alerta (umbral cruzado)
   - Acción recomendada (concreta, con cantidades)
   - Pasos operativos en la plataforma

4. REBALANCEO SUGERIDO (si aplica)
   - Tabla: qué vender, qué comprar, cuánto USD, en qué plataforma.
   - Verificar cada ticker de eToro pasa el gate search_instruments antes de escribirlo.
   - Impacto fiscal del rebalanceo (calculate_tax_impact).
   - Alternativa sin cierres si el fiscal es alto.

5. NUEVO BASELINE DE SEGUIMIENTO (JSON actualizado)
   Bloque listo para que el usuario guarde y pegue en la próxima sesión.
   Actualiza: pesos actuales como nuevo objetivo SOLO si se ejecutó el rebalanceo;
   si no, mantener pesos objetivo originales.

6. PRÓXIMA REVISIÓN SUGERIDA
   - Fecha concreta (DD-MM-AAAA).
   - Qué va a chequear específicamente.
```

## Calendario de revisión (referencia)
```
DIARIO: solo si el usuario tiene CFDs o forex apalancado abierto.
SEMANAL: copy trading rendimiento, DeFi APY.
MENSUAL: ETFs rendimiento, DCA con ahorro nuevo, rebalanceo si desviación > 5 p.p.
TRIMESTRAL: stress test completo, re-evaluar tesis por posición, impuesto DIAN acumulado.
ANUAL: preparar declaración DIAN, consolidar rendimientos reales del año.
```

## Reglas de interacción específicas

- **Nunca inventar precios de entrada.** Si el baseline no los tiene y el usuario tampoco los recuerda, pedirlos. Como último recurso, usar precio de mercado del día del plan original como proxy y etiquetar TODOS los cálculos con `(proxy)`.
- **Gate eToro sigue aplicando en el rebalanceo.** Si la acción propuesta incluye comprar más de X en eToro, validar con `search_instruments` antes de escribirla en el reporte.
- **No alterar risk_rules.** Si el rebalanceo propuesto empujaría el portafolio fuera de los límites del perfil (concentración, % defensivo, leverage promedio), marcarlo y proponer alternativa que respete los límites.
- **Honestidad cuando no hay señal.** Si el plan va razonablemente y no hay nada que hacer, decirlo explícito: "Plan en rango. Próxima revisión: [fecha]. No hay acción requerida." No inventar "ajustes tácticos" para parecer útil.
- **Si `get_portfolio` falla o devuelve vacío**, decirlo explícito y ofrecer el camino alternativo (pedir posiciones al usuario). No rellenar.

## Schema del BASELINE DE SEGUIMIENTO

El bloque que el plan_template deja al final de cada plan tiene esta forma. El tracking_skill lo espera en este formato para parsearlo:

```json
{
  "baseline_version": "1.0",
  "plan_date": "DD-MM-AAAA",
  "user_profile": {
    "capital_usd": 0,
    "risk_profile": "conservador|moderado|agresivo",
    "horizon": "corto|medio|largo",
    "tramo_capital": "<200|200-500|500-2000|>2000",
    "minimo_rendimiento_6m_pct": 0
  },
  "positions": [
    {
      "ticker": "",
      "venue": "etoro|binance|aave|mt5|...",
      "instrument_id": "",
      "instrument_type": "equity|etf|crypto|forex|cfd|copy|smart_portfolio|stablecoin_lending",
      "weight_target_pct": 0,
      "capital_assigned_usd": 0,
      "entry_price": 0,
      "entry_date": "DD-MM-AAAA",
      "thesis": "",
      "catalyst": "",
      "catalyst_date": "DD-MM-AAAA",
      "stop_loss": 0,
      "take_profit_1": 0,
      "take_profit_2": 0,
      "risk_score": 0,
      "leverage": 1.0
    }
  ],
  "portfolio_level": {
    "total_risk_score": 0,
    "defensive_pct": 0,
    "correlation_matrix_hash": "",
    "stress_moderate_loss_pct": 0,
    "stress_severe_loss_pct": 0
  },
  "schedule": {
    "next_review_date": "DD-MM-AAAA",
    "next_review_focus": ""
  }
}
```

## Recordatorio que el plan_template deja al final de cada plan nuevo

```
📌 PRÓXIMAS REVISIONES
- Semana 2: rendimiento de copy trading (si aplica).
- Mes 1: primera revisión completa + DCA si hay ahorro nuevo.
- Mes 3: stress test completo + revisión fiscal parcial.

Para la próxima revisión, escríbeme "revisa mi portafolio" y pega el bloque
BASELINE DE SEGUIMIENTO que está justo encima. Sin él tendré que reconstruir
desde cero (más preguntas, más tiempo).
```
