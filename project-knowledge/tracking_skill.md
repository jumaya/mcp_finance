# Skill: Seguimiento post-inversión — v5

## Propósito
Comparar el estado ACTUAL del portafolio del usuario contra el plan ORIGINAL entregado en una sesión previa, detectar desviaciones, generar alertas semáforo y recomendar acciones (rebalanceo, DCA, cierre, ampliación) sin inventar números.

## Principio clave — cómo funciona la "memoria" entre sesiones
Claude NO recuerda sesiones anteriores. La continuidad se logra por **persistencia externa**: el plan_template.md al final de cada plan nuevo incluye un bloque `BASELINE DE SEGUIMIENTO` en JSON. El usuario lo guarda y lo pega en la nueva sesión cuando dice "revisa mi portafolio". Si no lo tiene, el agente lo reconstruye preguntando al usuario (nunca inventando).

Las posiciones ACTUALES se leen directamente del MCP de eToro (`get_portfolio`), así que la parte "qué tengo hoy" está resuelta. Lo que no está en ningún MCP es el plan original (tesis, pesos objetivo, SL/TP, catalizadores) — eso vive en el BASELINE.

## Activación
- Usuario escribe cualquiera de: "revisa mi portafolio", "cómo va el plan", "seguimiento", "puedes hacer seguimiento", "haz seguimiento", "ya compré X", "ya invertí en X", "ya hice mi inversión", "cómo va mi posición", "rebalancear", "review portfolio", "cómo voy", "actualizar plan".
- Usuario pega un bloque `BASELINE DE SEGUIMIENTO` (JSON) de una sesión previa.
- Final de cada plan nuevo: el agente deja el bloque BASELINE para la próxima revisión.

## Regla de prioridad sobre los skills verticales
Si el mensaje contiene un disparador de tracking JUNTO con un ticker (p.ej.
"ya invertí en QQQ, hazme seguimiento", "cómo va mi posición de BTC"),
**este skill se carga en lugar de** equity/defi/forex_skill. El usuario
tiene una posición existente y pregunta por su evolución, no por un plan
nuevo del activo. Cargar el skill vertical aquí lleva al agente a buscar
precios teóricos en Yahoo / Alpha Vantage en vez de leer la posición real
del usuario en eToro — es exactamente el bug que estos skills previenen
y el chequeo bloqueante [B11] de system.md hace fallar la respuesta.

## Tool call obligatorio nº1: get_portfolio antes que cualquier otra cosa
En toda activación del Modo B (usuario pidió seguimiento, NO se está cerrando un plan nuevo), el **primer tool call del turno** es `etoro-server.get_portfolio` si el usuario tiene eToro conectado. No `yfinance_get_ticker_info`, no `web_search`, no `search_mcp_registry`, no nada más. Razones:
- La posición REAL (cantidad, precio de entrada, P&L de plataforma, valor actual) está en eToro, no en Yahoo. Yahoo da el precio de mercado teórico, no la posición del usuario.
- Si el agente abre con Yahoo, va a inventar el precio de entrada (porque Yahoo no lo tiene) y va a calcular el P&L a mano — violando el principio #1 de system.md.
- Si `etoro-server.get_portfolio` falla, decirlo explícito y pedir los datos al usuario. NO sustituir leyendo Yahoo.

Si una tool con prefijo `etoro-server:` aparece en `<available_tools>` del proyecto, está conectada. NO buscar en el directorio público de Anthropic ("eToro no está en el directorio MCP") — ese directorio lista conectores de Anthropic, no los servers MCP locales del proyecto, que se configuran en `claude_desktop_config.json`.

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

### Caso especial — primera inversión muy reciente sin baseline pegado
Patrón típico: el usuario dice "ya hice mi primera inversión en eToro a QQQ
puedes hacer seguimiento" pocos días después de que se le entregó un plan, y
no pega el bloque BASELINE. Protocolo:

1. Llamar `etoro-server.get_portfolio` (es el primer tool call siempre, ver
   regla en §"Tool call obligatorio nº1"). De ahí se lee `entry_price` real,
   `quantity`, `current_price`, `unrealizedPnL`, `valueInvestedAtOpen`.

2. Como no hay BASELINE pegado, el `compare_portfolio_to_baseline` aún no
   se puede llamar de forma útil (le faltan los pesos objetivo del plan
   original). Aquí dos caminos:

   **Camino corto** (preferido cuando hay UNA sola posición y muy reciente):
   - Reportar el estado actual de la posición leyendo SOLO los campos que
     vinieron de `get_portfolio` (precio entrada, P&L absoluto y % que dio
     la propia plataforma — no recalcular).
   - Marcar explícitamente: "No tengo el baseline pegado, así que no puedo
     comparar peso vs objetivo ni aplicar las alertas de desviación. Lo
     que ves arriba viene 100% de eToro."
   - Pedir al usuario el BASELINE para la próxima vez (UNA pregunta), o
     reconstruir lo mínimo: "¿Cuál era el capital total del plan y cuál
     era el peso objetivo de QQQ?".
   - Aún así, dar la sección 4 (Qué hacer con cada posición) con la lógica
     más conservadora del árbol — para una posición de pocos días, la
     respuesta por defecto es "MANTENER, es muy pronto para evaluar tesis,
     próxima revisión real en X días".

   **Camino completo** (cuando el usuario reconstruye el BASELINE):
   - Una vez con el BASELINE reconstruido, pasar a Fase B → C → D → E
     normalmente.

3. NUNCA estimar P&L desde un precio de entrada inventado o desde un precio
   de Yahoo. Si `get_portfolio` falla y el usuario tampoco pegó el BASELINE,
   decirlo explícito y detenerse — no rellenar.

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

### Fase C — Calcular desviaciones (una sola tool)

**Esto NO se hace en prompting.** La aritmética del tracking (P&L absoluto y %, desviaciones de peso, detección de nuevas/cerradas, clasificación semáforo por umbrales) es una checkpoint determinística en el MCP propio. En un portafolio con 5+ posiciones, hacer estos cálculos a mano es propenso a errores de arrastre (un peso mal calculado desplaza todos los demás) y viola el principio #1 de system.md.

Llamar **una sola tool**: `investment-calculators.compare_portfolio_to_baseline`.

Entrada:
- `baseline`: el bloque `BASELINE DE SEGUIMIENTO` parseado (schema al final de este documento).
- `current_positions`: lista construida a partir de las fuentes de Fase B. Cada posición debe traer al menos `ticker`, `quantity`, `current_price` y (si se pudo obtener) `current_value_usd`, `unrealized_pnl_usd`, `venue`.
  - Para posiciones de eToro: mapear directo desde `etoro-server.get_portfolio` (ya viene `unrealizedPnL`, valor actual y precio de entrada real — preferir siempre el `unrealized_pnl_usd` que da la plataforma sobre recálculos propios).
  - Para posiciones en MetaTrader: usar `metatrader.get_all_positions`.
  - Para posiciones fuera de eToro/MT5: construir con los datos que el usuario pegó + precio actual de `coingecko.get_simple_price` / `yahoo-finance.yfinance_get_ticker_info` / `metatrader.get_symbol_price`.

Salida de la tool (todo lo que el reporte necesita ya viene calculado):
- `summary`: P&L total absoluto y %, valor actual total, capital inicial, conteos.
- `positions[]`: por posición, peso actual, peso objetivo, desviación en p.p., P&L abs y %, **status semáforo** y `status_reasons`.
- `new_positions[]`: posiciones fuera de plan.
- `closed_positions[]`: posiciones del baseline que ya no están (el agente debe preguntar motivo y P&L realizado).
- `alerts[]`: alertas ordenadas por severidad (🔴 → 🟡), con `ticker` y `reasons`.
- `warnings[]`: problemas de data (campos faltantes, pesos que no suman 100, etc.) — si hay, mencionarlos en el reporte antes de las conclusiones.

**El agente no recalcula nada de esto en prompting.** Lee el dict y lo presenta.

Las capas que la tool NO cubre (cualitativas o que requieren datos adicionales) sí siguen en prompting y requieren sus propias tools:

- **Stress test con pesos actuales**: si hay CFDs o posiciones apalancadas, llamar `stress_test_portfolio` con los pesos actuales que devolvió `compare_portfolio_to_baseline` (campo `weight_current_pct`), no con los objetivo.
- **Correlación actual**: si hubo rebalanceos o cierres, usar `calculate_correlation` sobre las posiciones vivas.
- **Catalizadores pendientes**: earnings en < 7 días → `yfinance_get_ticker_info.earningsTimestampStart`.
- **SL técnico alcanzado**: comparar `current_price` del reporte contra `stop_loss` del baseline posición por posición (comparación simple, una línea de lógica — no es "aritmética de portafolio").
- **DeFi APY vs baseline**: refetch del APY actual del pool vs el del baseline.
- **Copy trader: drawdown o cambio de estrategia**: `etoro-server.get_user_performance`.
- **Tiempo transcurrido**: días entre `baseline.plan_date` y hoy.

### Fase D — Diagnóstico con alertas semáforo

Las alertas por P&L y desviación de peso ya vienen clasificadas en `result["alerts"]` por `compare_portfolio_to_baseline`. Umbrales usados (fuente de verdad en `mcp-server/server.py` → `_TRACKING_THRESHOLDS`):

```
🔴 CRÍTICO (acción en ≤ 48h) — ya clasificado por la tool
  - Pérdida > 15% en una posición
  - Desviación de peso > 15 p.p. vs objetivo

🟡 ATENCIÓN (revisar en días) — ya clasificado por la tool
  - Pérdida entre 5% y 15%
  - Desviación de peso entre 5 y 15 p.p.
  - Posiciones nuevas fuera de plan
  - Posiciones del baseline que ya no están abiertas
```

A la lista que devuelve la tool, el agente AÑADE las alertas que dependen de otras tools (y que por tanto no están en el payload de `compare_portfolio_to_baseline`):

```
🔴 CRÍTICO adicional (requiere otras tools)
  - SL técnico del plan original alcanzado (comparar current_price vs baseline.stop_loss)
  - DeFi APY cayó > 50% vs baseline (refetch APY del pool)
  - Copy trader: drawdown > 20% o cambio de estrategia (get_user_performance)
  - Correlación recalculada > 0.85 entre 2 posiciones grandes (calculate_correlation)

🟡 ATENCIÓN adicional
  - Correlación recalculada entre 0.7 y 0.85
  - Un vertical > 40% del portafolio total
  - Earnings de una acción del plan en < 7 días (yfinance earningsTimestampStart)
  - Stress test severo actual excede el del plan original en > 10 p.p.

🟢 OK
  - Posiciones que la tool devuelve con status "🟢" y sin alertas adicionales
```

Si se cambia un umbral aquí, cambiar también `_TRACKING_THRESHOLDS` en `server.py` — son la misma fuente de verdad.

Para CADA alerta, proponer una acción concreta basada en las reglas del plan original y de `risk_rules.md`:

- **Desviación > 5 p.p.** → rebalancear. Indicar cantidad exacta a vender/comprar en USD.
- **Posición +50% vs entrada** → realizar parcial (vender 25%) y mover stop a break-even.
- **Posición −20% con fundamentales intactos** → DCA SOLO si: (a) perfil lo permite, (b) hay capital nuevo, (c) la tesis del baseline sigue viva. Si la tesis cambió, no es DCA, es cierre.
- **SL técnico alcanzado** → cerrar. No negociar con el SL del plan.
- **Capital nuevo disponible** → asignar a la posición más subponderada que siga dentro de tesis.

### Fase E — Entregar el reporte de seguimiento

Todo el contenido numérico viene de la respuesta de `compare_portfolio_to_baseline`. El agente mapea del dict al reporte — no reinterpreta ni recalcula.

Estructura obligatoria (es un artifact más liviano que el plan_template, NO los 4 tabs del plan):

```
🎯 SEGUIMIENTO — [fecha DD-MM-AAAA] | [N días desde el plan original]

1. RESUMEN EJECUTIVO (3 líneas máximo)
   - P&L total: {summary.pnl_total_pct} ({summary.pnl_total_abs_usd} de
     {summary.capital_initial_usd} inicial) — fuente: compare_portfolio_to_baseline,
     alimentada por eToro get_portfolio / MetaTrader / datos del usuario.
   - Alertas: {summary.alert_counts.red} 🔴 + {summary.alert_counts.yellow} 🟡
     + {summary.alert_counts.green} 🟢.
   - Acción principal recomendada (derivada de alerts[0] si hay 🔴,
     o "sin acción requerida" si todas son 🟢).
   - Si el payload trae warnings[] no vacío, mencionar "⚠️ data incompleta:
     {warnings}" antes de cualquier conclusión.

2. POSICIÓN POR POSICIÓN (tabla)
   Una fila por cada elemento de positions[]:
   | Ticker | Venue | Peso actual | Peso obj. | Desv p.p. | P&L % | P&L $ | Estado |
   Mapeo: ticker → ticker, venue → venue, weight_current_pct → "Peso actual",
   weight_target_pct → "Peso obj.", weight_deviation_pp → "Desv p.p.",
   pnl_pct → "P&L %", pnl_abs_usd → "P&L $", status → "Estado".
   Si pnl_abs_source = "computed" (no platform), anotar "(computed)" junto al P&L.

   Debajo de la tabla principal:
   - Posiciones de new_positions[]: fila marcada "⚠️ fuera de plan"
     con ticker, venue, current_value_usd, weight_current_pct y note.
   - Posiciones de closed_positions[]: listarlas aparte y PREGUNTAR AL USUARIO
     motivo de cierre y P&L realizado. La tool avisa explícitamente que no
     puede saberlo — no inventar.

3. ALERTAS 🔴 / 🟡 (iterar sobre alerts[], ya vienen ordenadas por severidad)
   Por cada alerta:
   - Qué pasó: ticker + reasons[] (los motivos ya están redactados por la tool).
   - Números: pnl_pct y weight_deviation_pp si no son null.
   - Acción recomendada (concreta, con cantidades) — aquí el agente SÍ aporta,
     cruzando con risk_rules.md y platforms_skill.md.
   - Pasos operativos en la plataforma.

   Añadir a esta lista las alertas de Fase D que NO vienen en el payload
   (SL técnico, correlación recalculada, earnings < 7 días, DeFi APY,
   copy trader drawdown) y que el agente calculó con otras tools.

4. QUÉ HACER CON CADA POSICIÓN — recomendación accionable obligatoria
   **Esta sección es OBLIGATORIA en TODA respuesta de tracking, incluso si todo
   está 🟢.** No basta con "va bien, sigue así". El usuario pidió seguimiento
   para saber qué hacer ahora — el reporte cierra esa pregunta.

   Para CADA posición del payload (incluso las 🟢), dar UNA acción explícita.
   Árbol de decisión sugerido:

   - status="🟢" Y abs(weight_deviation_pp) ≤ 5 Y pnl_pct entre -5% y +20% Y
     tesis del baseline sigue viva
       → "MANTENER. Continuar DCA mensual si el plan original lo contemplaba,
          al monto y calendario originales. Próxima revisión: [fecha]."
   - status="🟢" Y pnl_pct > +20% Y todavía no se realizó parcial
       → "REALIZAR PARCIAL: vender 25% de la posición para asegurar ganancia
          y mover stop a break-even (precio de entrada del baseline = $X).
          El 75% restante mantiene la tesis original."
   - status="🟡" por desviación de peso 5-15 p.p.
       → "REBALANCEAR: vender/comprar $Z USD para volver al peso objetivo.
          (Detalle en sección 5 abajo.)"
   - status="🟡" por pérdida 5-15% pero tesis intacta y perfil lo permite
       → "DCA: comprar $W USD adicionales si tienes capital nuevo disponible.
          NO vender. La tesis original sigue vigente: [resumen 1 línea]."
   - status="🔴" por SL técnico alcanzado
       → "CERRAR. El SL del baseline era $X y hoy cotiza por debajo. No
          negociar con el SL del plan."
   - status="🔴" por desviación > 15 p.p. o pérdida > 15% con tesis rota
       → "CERRAR Y REASIGNAR: cerrar la posición, evaluar si el capital
          libre se reasigna a otra posición subponderada del plan o a
          reserva."
   - posición es muy reciente (días desde entry < 7) y no hay alerta
       → "MANTENER. Es muy pronto para evaluar tesis (< 7 días). El
          rendimiento de corto plazo es ruido. Próxima revisión real:
          [fecha del schedule del baseline]."
   - posición está en new_positions[] (no estaba en el baseline original)
       → preguntar al usuario tesis y peso objetivo; NO recomendar
         mantener/cerrar sin contexto.

   El árbol de arriba es guía, no exhaustivo. La acción concreta SIEMPRE
   se cruza contra risk_rules.md (límites de concentración, defensivo,
   correlación) y platforms_skill.md (mínimos por venue antes de proponer
   un trade).

5. REBALANCEO SUGERIDO (si aplica)
   Gatillo: alguna posición con abs(weight_deviation_pp) > 5 en el payload.
   - Tabla: qué vender, qué comprar, cuánto USD, en qué plataforma.
   - Verificar cada ticker de eToro pasa el gate search_instruments antes de escribirlo.

6. NUEVO BASELINE DE SEGUIMIENTO (JSON actualizado) — OBLIGATORIO al final
   Bloque listo para que el usuario guarde y pegue en la próxima sesión.
   Actualiza: pesos actuales como nuevo objetivo SOLO si se ejecutó el rebalanceo;
   si no, mantener pesos objetivo originales.
   Si la respuesta NO incluye este bloque, viola [B13] de system.md y se reescribe.

7. PRÓXIMA REVISIÓN SUGERIDA
   - Fecha concreta (DD-MM-AAAA).
   - Qué va a chequear específicamente.
   - Recordatorio textual: "Para revisarla, escríbeme 'revisa mi portafolio'
     y pega el bloque BASELINE de arriba."
```

## Calendario de revisión (referencia)
```
DIARIO: solo si el usuario tiene CFDs o forex apalancado abierto.
SEMANAL: copy trading rendimiento, DeFi APY.
MENSUAL: ETFs rendimiento, DCA con ahorro nuevo, rebalanceo si desviación > 5 p.p.
TRIMESTRAL: stress test completo, re-evaluar tesis por posición.
ANUAL: consolidar rendimientos reales del año.
```

## Reglas de interacción específicas

- **Nunca inventar precios de entrada.** Si el baseline no los tiene y el usuario tampoco los recuerda, pedirlos. Como último recurso, usar precio de mercado del día del plan original como proxy y etiquetar TODOS los cálculos con `(proxy)`.
- **Nunca calcular el P&L a mano desde precios de Yahoo.** El P&L correcto está en `get_portfolio.unrealizedPnL` (lo da la plataforma). Calcularlo "a mano" desde `(current_price - entry_price) / entry_price` cuando ambos son adivinados es el patrón #1 de fallo del tracking — ver [B12] de system.md.
- **eToro propio del proyecto vs directorio público de Anthropic.** Si en `<available_tools>` ves tools con prefijo `etoro-server:` están conectadas vía `claude_desktop_config.json`. NO buscar "etoro" en `search_mcp_registry` ni decir al usuario "eToro no está como conector" — `search_mcp_registry` lista conectores oficiales de Anthropic, no los servers MCP locales del proyecto. Si la tool aparece en el listado de tools, está disponible.
- **Gate eToro sigue aplicando en el rebalanceo.** Si la acción propuesta incluye comprar más de X en eToro, validar con `search_instruments` antes de escribirla en el reporte.
- **No alterar risk_rules.** Si el rebalanceo propuesto empujaría el portafolio fuera de los límites del perfil (concentración, % defensivo, leverage promedio), marcarlo y proponer alternativa que respete los límites.
- **Honestidad cuando no hay señal.** Si el plan va razonablemente y no hay nada táctico que hacer, decirlo explícito: "Plan en rango. Próxima revisión: [fecha]. Acción: MANTENER, continuar DCA mensual al monto del plan original." No inventar "ajustes tácticos" para parecer útil — pero TAMPOCO omitir la sección 4 (Qué hacer con cada posición). "Mantener" SÍ es una acción concreta y va en esa sección.
- **Si `get_portfolio` falla o devuelve vacío**, decirlo explícito y ofrecer el camino alternativo (pedir posiciones al usuario). No rellenar.
- **No recalcular la aritmética del tracking en prompting.** Si el agente necesita P&L, desviación de peso o clasificación semáforo por umbrales, la fuente es `compare_portfolio_to_baseline`. Hacer la aritmética "a mano" viola el principio #1 de system.md.
- **Warnings de la tool siempre visibles.** Si `compare_portfolio_to_baseline` devuelve `warnings[]` no vacío (capital=0, pesos que no suman 100, entry_price faltante, etc.), mencionarlos explícitamente al inicio del reporte antes de presentar conclusiones. El usuario debe saber qué parte del análisis está sobre data incompleta.
- **Rally muy fuerte en pocos días NO es razón para cambiar el plan.** Si el P&L de una posición está por encima del escenario optimista del baseline en una fracción del horizonte (p.ej. supera el +16% de 6M en 1 mes), la acción correcta NO es "mantener y dejar correr" sin más — es revisar el árbol de decisión §4: si pnl > +20% considerar realizar parcial 25% y mover stop a break-even; si pnl entre +5 y +20% mantener; en ambos casos NO cambiar la tesis original por el rendimiento de corto plazo.

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
