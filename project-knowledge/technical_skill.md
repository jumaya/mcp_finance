# Skill: Análisis técnico — v1.1

> **Changelog v1.1:** rotación de tickers en los ejemplos didácticos.
> El "Ejemplo real" pasa de NVDA a JPM (financial, perfil moderado),
> y la línea de cronograma del Tab 2 usa un ticker del set rotatorio
> en lugar de NVDA. Motivo: alineación con `equity_skill.md` v9.3 —
> evitar que los ejemplos del skill anclen al modelo en NVDA/AAPL/SPY
> como referencia narrativa por defecto. Ver § "Política de ejemplos"
> al final del documento.

## Qué es este skill y qué NO es

Este es un skill **transversal** (como `risk_rules.md`), no un vertical. No
reemplaza a `equity_skill.md`, `forex_skill.md` ni `defi_skill.md`: se
carga **junto** a ellos cuando el plan incluye posiciones con exposición
direccional al precio.

### Modo híbrido (lectura obligatoria antes de usar este skill)

```
VINCULANTE (estricto):
  → SL y TP de CADA posición direccional se derivan técnicamente.
  → No se permite "SL al -10% redondo" si hay un swing low identificable
    o un nivel de Fibonacci cercano. Los niveles técnicos se usan.
  → Si no hay ningún nivel técnico identificable en el rango relevante,
    se usa ATR × multiplicador (fallback documentado).

INFORMATIVO (sesgo, no bloqueo):
  → La postura técnica (bullish / neutral / bearish) modula el
    cronograma de entrada del Tab 2, pero NO descarta tickers que
    pasaron el gate eToro y los fundamentales del skill vertical.
  → Si la postura es bearish, la entrada se escalona o se retrasa.
    Nunca se convierte en "no entrar" salvo caso extremo documentado
    abajo (§ Invalidación técnica).
```

## Cuándo se activa

Activar automáticamente cuando el plan genera posiciones con exposición
direccional al precio:

| Caso                                                   | ¿Aplica?  | Notas                                      |
|--------------------------------------------------------|-----------|--------------------------------------------|
| Equity spot o CFD (equity_skill)                       | ✅ Sí     | Aplicación completa                        |
| Forex / CFDs commodities (forex_skill)                 | ✅ Sí     | Énfasis en S/R y ATR                       |
| Cripto spot direccional (BTC/ETH/SOL compra en eToro o Binance) | ✅ Sí | Solo al **comprar**, no al stakear   |
| Stablecoin lending (USDC en Binance Simple Earn, Aave) | ❌ No     | No hay exposición de precio                |
| ETH/BTC en staking (rendimiento del protocolo)         | ❌ No     | El precio sigue importando para el SL del capital, pero no para el rendimiento |
| Copy trading / Popular Investors (social_skill)        | ❌ No     | Se juzga al trader, no al activo           |
| Yield farming / LP                                     | ❌ No     | Dominan APY y riesgo de smart contract     |

**Regla:** si el vertical llama a este skill pero la posición no es
direccional (ej. USDC lending), el skill responde explícitamente "no
aplica análisis técnico a esta posición" y se sale. No se fuerzan
patrones sobre activos donde el precio es irrelevante para la tesis.

## Orden en el flujo del `system.md`

El skill se ejecuta **dentro de la Fase 3** del orquestador, después de
que el skill vertical haya:

1. Pasado el gate eToro (si aplica).
2. Obtenido precio, RSI, MACD, SMA50, SMA200 de Alpha Vantage.
3. Obtenido `yfinance_get_ticker_info` (en equity).
4. Obtenido señal de TradingView.

Entonces este skill toma esos datos ya recolectados y los **interpreta**.
No hace llamadas nuevas a Alpha Vantage o TradingView salvo que falte un
dato específico (ver § Tool calls adicionales).

## Datos que este skill consume

Todos deben venir del skill vertical que lo llamó — no los pedir dos veces.

| Dato                            | Fuente primaria        | Fallback            |
|---------------------------------|------------------------|---------------------|
| OHLCV diario últimos 90-180 días| Alpha Vantage TIME_SERIES_DAILY | yahoo-finance price_history |
| OHLCV semanal últimos 2 años    | Alpha Vantage WEEKLY   | yahoo-finance       |
| RSI (14)                        | Alpha Vantage RSI      | calcular de OHLC    |
| MACD (12, 26, 9)                | Alpha Vantage MACD     | calcular de OHLC    |
| SMA 50, SMA 200                 | `fiftyDayAverage`, `twoHundredDayAverage` de yfinance | Alpha Vantage SMA |
| ATR (14)                        | Alpha Vantage ATR      | calcular de OHLC    |
| Señal TradingView               | tradingview.screen_*   | N/A                 |

Si **falta** un dato crítico (ej. no hay OHLC diario), decir literal:
"No puedo derivar SL técnico de <TICKER> — falta OHLC diario vía
<fuente>. Usando fallback ATR" **o** pedir el dato al usuario. Nunca
inventar niveles.

## Parte 1 — Patrones de precio (postura INFORMATIVA)

Los patrones determinan la **postura técnica** (bullish / neutral / bearish)
que modula el cronograma, no bloquea la entrada.

### Patrones reversales (requieren formación completa)

```
DOBLE SUELO (W) — bullish
  Estructura: low₁ ≈ low₂ (±3%), separados por ≥ 15 días
              precio rompe el "cuello" (máximo entre low₁ y low₂)
  Confirmación: ruptura del cuello CON volumen > 1.5× promedio 20d
  Target teórico: cuello + (cuello − low) — medido verticalmente
  Invalidación: cierre diario < low₂ con volumen

DOBLE TECHO (M) — bearish
  Espejo del doble suelo. Estructura: high₁ ≈ high₂ (±3%), ≥ 15 días.
  Target teórico: cuello − (high − cuello)
  Invalidación: cierre > high₂.

CABEZA-HOMBROS — bearish
  Estructura: hombro izq → cabeza (más alto) → hombro der (≈ hombro izq)
              cuello une los dos valles
  Confirmación: ruptura del cuello a la baja
  Target teórico: cuello − (cabeza − cuello)
  Invalidación: recuperación del cuello en 2-3 sesiones.

CABEZA-HOMBROS INVERTIDO — bullish (espejo del anterior)
```

### Patrones de continuación (confirman la tendencia previa)

```
BANDERA alcista / bajista
  Contexto: rally fuerte (≥ +15% en 2-4 semanas) → consolidación estrecha
  Duración típica: 1-3 semanas
  Ruptura en dirección previa = continuación de la tendencia

TRIÁNGULO (ascendente / descendente / simétrico)
  Ascendente: resistencia plana + mínimos crecientes → sesgo bullish
  Descendente: soporte plano + máximos decrecientes → sesgo bearish
  Simétrico: sin sesgo direccional hasta la ruptura
  Invalidez: si se llega al vértice sin ruptura, el patrón "expira".
```

### Cómo traducir patrón a postura

```
Patrón identificado + volumen confirmatorio → postura clara (bullish/bearish)
Patrón sin confirmación de volumen            → postura "tentativa"
Solo indicadores, sin patrón                  → postura "mixta"
Nada identificable                            → postura "neutral"
```

### Reglas duras de identificación

1. **No forzar patrones.** Si los swing points no cumplen la tolerancia
   (±3% entre los dos lows del doble suelo, simetría de los hombros), el
   patrón no existe. Es mejor "neutral" que un patrón inventado.
2. **Ventana mínima:** solo identificar patrones formados en ventana ≥ 15
   días. Patrones intradía no aplican al horizonte del agente (semanas-meses).
3. **Volumen es confirmatorio, no opcional.** Una ruptura sin volumen se
   anota como "ruptura débil", no como confirmación.
4. **Un patrón por ticker por timeframe.** Si se identifican dos patrones
   contradictorios (ej. doble suelo diario + cabeza-hombros semanal), el
   timeframe mayor manda. Se reporta el conflicto al usuario.

## Parte 2 — Divergencias (refuerzan la postura)

Una divergencia entre precio e indicador precede frecuentemente a
reversiones. Se usan para confirmar o invalidar un patrón.

### MACD

```
DIVERGENCIA ALCISTA (bullish):
  Precio hace low₂ < low₁
  MACD histogram hace low₂ > low₁ (sube aunque precio cae)
  → El momentum bajista se está agotando.
  → Refuerza doble suelo o cabeza-hombros invertido.

DIVERGENCIA BAJISTA (bearish):
  Precio hace high₂ > high₁
  MACD histogram hace high₂ < high₁
  → El momentum alcista se agota.
  → Refuerza doble techo o cabeza-hombros.

CRUCE MACD (confirmación adicional):
  MACD line cruza sobre signal line con histogram > 0 → momentum positivo.
  Cruce abajo con histogram < 0 → momentum negativo.
```

### RSI

```
Zonas absolutas:
  RSI > 70 → sobrecompra (no significa "vender ya"; significa "no es
             zona de entrada óptima")
  RSI < 30 → sobreventa (no significa "comprar ya"; significa "no es
             zona de salida óptima")
  30-70    → zona neutral, usar otros criterios

DIVERGENCIA RSI (misma lógica que MACD):
  Precio low₂ < low₁ + RSI low₂ > low₁ → divergencia alcista
  Precio high₂ > high₁ + RSI high₂ < high₁ → divergencia bajista
```

### Regla de uso

Una divergencia **sola** no es señal. Divergencia + patrón + volumen = tres
confirmaciones (confluencia fuerte). Si solo hay divergencia sin patrón de
precio, se anota como "momentum debilitándose" sin cambiar la postura.

## Parte 3 — Niveles de Fibonacci (VINCULANTE para SL/TP)

Fibonacci se usa para derivar niveles concretos de stop loss y take
profit. Es la parte **vinculante** del modo híbrido.

### Cómo trazar los niveles

```
1. Identificar el swing relevante:
   - Long setup: low → high del movimiento alcista reciente (últimos
     60-90 días típicamente)
   - Short setup: high → low del movimiento bajista reciente

2. Calcular retrocesos (para SL y puntos de entrada en pullback):
   0.382 (38.2%)
   0.500 (50%)    ← no es Fibonacci estricto pero se usa
   0.618 (61.8%)  ← "golden ratio", el más respetado
   0.786 (78.6%)  ← último retroceso antes de invalidar el swing

3. Calcular extensiones (para TP):
   1.272 — TP conservador
   1.618 — TP medio (más usado)
   2.000 — TP agresivo
   2.618 — TP extremo (raro, solo tendencias muy fuertes)
```

### Reglas de uso para SL

```
En setup LONG con swing low→high identificado:
  → Entrada en pullback a 0.382, 0.500 o 0.618
  → SL justo DEBAJO del siguiente nivel (ej. entrada en 0.500, SL en 0.618)
  → Si entrada es en 0.786, SL debajo del swing low original (0% de Fibo)

En setup SHORT con swing high→low:
  → Espejo del anterior.

Si NO hay swing claro (mercado lateral, consolidación):
  → Fibonacci no aplica
  → Fallback: SL = precio − (ATR × 1.5) para long, + ATR × 1.5 para short
```

### Reglas de uso para TP

```
TP1 (cerrar 50% de la posición): extensión 1.272 o el siguiente nivel
     de resistencia técnica, lo que esté más cerca.
TP2 (cerrar el 50% restante): extensión 1.618 o siguiente resistencia
     mayor.

Si el TP1 calculado da un R:R < 1:1.5 respecto al SL:
  → El setup NO vale la pena
  → Reportar al usuario: "El R:R técnico de <TICKER> es <X:Y>, por debajo
    del mínimo 1:1.5 que pide el plan. Posponer entrada o buscar mejor
    nivel de swing."
```

### Confluencias con SMA y S/R

```
Si un nivel de Fibonacci coincide (±1.5%) con:
  - SMA 50 o SMA 200
  - Un swing low/high previo (S/R horizontal)
  - Un número psicológico redondo ($100, $200, etc.)

→ CONFLUENCIA. Se marca como nivel "fuerte". Los SL y TP deben usar
  niveles de confluencia cuando estén disponibles.
```

## Parte 4 — Confluencias y postura final

La postura técnica final se deriva contando señales. Es informativa; no
sustituye al sizing de `risk_rules.md`.

### Matriz de decisión

```
SEÑALES ALCISTAS:                              SEÑALES BAJISTAS:
  [ ] Patrón bullish confirmado                  [ ] Patrón bearish confirmado
  [ ] Divergencia MACD alcista                   [ ] Divergencia MACD bajista
  [ ] Divergencia RSI alcista                    [ ] Divergencia RSI bajista
  [ ] Precio sobre SMA 50 y SMA 200              [ ] Precio bajo SMA 50 y SMA 200
  [ ] SMA 50 sobre SMA 200 (golden cross)        [ ] SMA 50 bajo SMA 200 (death cross)
  [ ] RSI saliendo de sobreventa (<30 → >30)     [ ] RSI saliendo de sobrecompra (>70 → <70)
  [ ] Ruptura con volumen > 1.5× promedio        [ ] Ruptura a la baja con volumen

CONTEO → POSTURA:
  ≥ 3 alcistas y ≤ 1 bajista           → BULLISH
  ≥ 3 bajistas y ≤ 1 alcista           → BEARISH
  1-2 de cada lado, o mezcla           → NEUTRAL
  0 señales identificables             → "Sin señal clara"
```

### Cómo la postura modula el cronograma (Tab 2 del `plan_template.md`)

```
POSTURA = BULLISH
  → Entrada completa en Semana 1 del cronograma.
  → Si el setup pide pullback a 0.382, entrada al tocar ese nivel.

POSTURA = NEUTRAL
  → Entrada escalonada: 50% en Semana 1, 50% en Semana 2 al confirmar dirección.
  → Nota en el Tab 2: "Entrada dividida por ausencia de señal técnica clara."

POSTURA = BEARISH
  → Entrada MÍNIMA en Semana 1 (25-33% de la posición objetivo).
  → Resto condicionado a invalidación del patrón bearish o al toque del SL
    técnico sin ser activado.
  → Nota en el Tab 2 y en el Tab 4 (Riesgo).

POSTURA = "SIN SEÑAL CLARA"
  → Entrada escalonada en 3 semanas (33%/33%/33%).
  → No se usa como razón para descartar — la decisión de incluir el ticker
    ya la tomó el skill vertical por fundamentales.
```

**Invariante:** la postura técnica NO modifica el peso de la posición
(eso lo dicta `risk_rules.md` R1-R6 y `allocate_portfolio`). Solo modifica
**cuándo** se entra dentro del cronograma del mes 1.

### Invalidación técnica (único caso donde lo técnico SÍ descarta)

Excepción estricta al principio híbrido. Se descarta el ticker solo si
se cumplen las tres condiciones:

```
1. Postura BEARISH con ≥ 4 señales bajistas confirmadas
2. Precio actual por debajo de SMA 200
3. Fundamentales neutros o débiles (no hay tesis que justifique comprar
   en contra-tendencia macro)

→ Entonces: reportar al usuario "el ticker tiene setup técnico
  fuertemente bearish y los fundamentales no compensan. Sugiero
  sustituir por <equivalente del sector con mejor setup>."
→ NO descartarlo en silencio. El usuario puede aceptar el riesgo.
```

## Parte 5 — Cuándo NO concluir (saber callar)

Consistente con `forex_skill.md` ("saber cuándo no actuar es inteligencia").
No se fuerza una postura si los datos no la soportan.

```
Si se cumple alguna de estas condiciones, reportar "sin señal técnica
clara" en vez de inventar una postura:

  - Menos de 60 días de OHLC disponibles
  - Volatilidad realizada 30d < mitad de la histórica 1y (mercado
    anormalmente quieto, patrones poco fiables)
  - Gap de fin de semana > 5% reciente (distorsiona swings)
  - Ticker con earnings en < 5 días (el reporte invalidará el setup)
  - Volumen promedio 20d < 500k acciones/día (ilíquido, patrones ruidosos)

En estos casos:
  → SL/TP se derivan con ATR fallback, NO con Fibonacci forzado.
  → Postura informativa se reporta como "sin señal clara".
  → El cronograma usa entrada escalonada a 3 semanas.
```

## Tool calls adicionales (solo si el vertical no los trajo)

```
Si falta ATR (necesario para fallback SL/TP):
  alphavantage.TOOL_CALL(name="ATR", symbol="<TICKER>", interval="daily", time_period=14)

Si falta OHLC diario suficiente:
  alphavantage.TOOL_CALL(name="TIME_SERIES_DAILY", symbol="<TICKER>", outputsize="compact")
  → compact = últimos 100 días, suficiente para swings recientes
  → outputsize="full" solo si se necesita identificar un patrón semanal largo

Si el ticker es de forex y falta data:
  alphavantage.TOOL_CALL(name="FX_DAILY", from_symbol="EUR", to_symbol="USD")
```

## Protocolo numerado (cómo ejecuta el skill)

```
POR CADA posición direccional del plan:

  1. Verificar si aplica (ver tabla de § "Cuándo se activa").
     Si no aplica: responder "no aplica análisis técnico — posición no
     direccional" y salir.

  2. Cargar datos recolectados por el vertical:
     - OHLC diario 90-180 días
     - RSI, MACD, SMA50, SMA200, ATR
     - Señal de TradingView

  3. Identificar swing relevante (low→high para long, high→low para short)
     en los últimos 60-90 días.

  4. PATRONES:
     - Buscar patrones reversales y de continuación en ventana ≥ 15 días.
     - Confirmar con volumen (> 1.5× promedio 20d en la ruptura).
     - Anotar: patrón / patrón tentativo / sin patrón.

  5. DIVERGENCIAS:
     - Checkear MACD y RSI contra los últimos 2 swings.
     - Anotar: divergencia alcista / bajista / ninguna.

  6. POSTURA FINAL:
     - Aplicar la matriz de conteo (§ Parte 4).
     - Resultado: BULLISH / NEUTRAL / BEARISH / SIN SEÑAL CLARA.

  7. FIBONACCI → SL y TP (VINCULANTE):
     - Trazar retrocesos y extensiones sobre el swing del paso 3.
     - Derivar entrada, SL, TP1, TP2.
     - Buscar confluencias con SMA 50/200 y swing highs/lows previos.
     - Si no hay swing claro: fallback ATR × 1.5 para SL, R:R 1:2 para TP.

  8. VERIFICAR R:R:
     - R:R = (TP1 − entrada) / (entrada − SL) para long.
     - Si R:R < 1:1.5 → reportar al usuario, sugerir posponer o mejor nivel.

  9. MODULAR CRONOGRAMA (§ Parte 4):
     - Escribir la pauta de entrada para el Tab 2 del plan según postura.

  10. INVALIDACIÓN TÉCNICA (§ Parte 4):
      - Verificar las 3 condiciones. Si se cumplen, proponer sustituto
        y notificar al usuario.
```

## Integración con `plan_template.md`

**No crear tabs nuevos.** El plan JSX tiene exactamente 4 tabs, y eso es
inamovible. La salida técnica se inserta así:

```
Tab 1 "📊 Plan" — Paso 4 (posiciones con detalle):
  Por cada posición direccional, añadir bloque:

  "Setup técnico <TICKER>:
   - Postura: <BULLISH|NEUTRAL|BEARISH|sin señal clara>
   - Patrón: <nombre del patrón o 'ninguno'>
   - Divergencias: <MACD alcista / RSI bajista / ninguna>
   - Entrada sugerida: $<nivel> (Fibonacci 0.<X> del swing $<low>-$<high>)
   - SL: $<nivel> (Fibonacci 0.<X> / swing low / ATR×1.5)
   - TP1: $<nivel> (Fibonacci 1.272 — cerrar 50%)
   - TP2: $<nivel> (Fibonacci 1.618 — cerrar 50% restante)
   - R:R: 1:<X.Y>"

Tab 2 "📅 Cronograma" — Semana 1 a 4:
  Respetar la modulación por postura (§ Parte 4).
  Ejemplo Semana 1: "Comprar 33% de LMT a mercado (postura BEARISH
  informativa — entrada escalonada)."

Tab 4 "⚠️ Riesgo" — Sección "Triggers de salida":
  Cada SL y TP técnicos aparecen aquí como triggers automáticos,
  complementando los exit triggers por vertical que ya define risk_rules.md.
  NO duplicar: los triggers técnicos son por ticker, los de risk_rules son
  por vertical.
```

## Ejemplo real (JPM, validado con datos ilustrativos)

> **Nota de la v1.1:** este ejemplo migró de NVDA a JPM. Misma
> estructura pedagógica (postura neutral con sesgo bullish, R:R
> favorable, confluencia Fibonacci + SMA), distinto sector (financials
> en lugar de semiconductores) para evitar anclaje del modelo en
> "tickers favoritos". Los números son ilustrativos.

Datos recolectados por `equity_skill` para JPM:

```
OHLC 90d: swing low $185.00 (día -45) → swing high $232.00 (día -12)
Precio actual: $208.50
RSI (14): 49
MACD: line -0.6, signal -0.2, histogram -0.4 (cruzó bajo hace 6 días)
SMA 50: $215.00
SMA 200: $198.00
Volumen 20d promedio: 12M; últimos 3 días: 9.5M (bajo)
ATR (14): $3.10
Señal TradingView: "neutral"
```

Aplicación del protocolo:

```
Paso 3 — Swing: $185.00 → $232.00 (rango $47.00)

Paso 4 — Patrón: NO hay doble suelo (solo un low reciente). Consolidación
en rango $205-$215 últimas 2 semanas → triángulo simétrico en formación,
aún no confirmado. Postura tentativa: neutral-a-bullish.

Paso 5 — Divergencia: MACD sigue bajo cero pero histogram dejó de caer
hace 4 días (mini-divergencia alcista tentativa). RSI sin divergencia
clara.

Paso 6 — Conteo:
  Alcistas: precio sobre SMA 200 ✅, divergencia MACD tentativa ✅
            → 2 señales débiles
  Bajistas: precio bajo SMA 50 ✅, MACD bajo cero ✅
            → 2 señales
  Postura: NEUTRAL

Paso 7 — Fibonacci sobre swing $185.00-$232.00:
  0.382 retroceso → $214.05
  0.500 retroceso → $208.50  ← precio actual está aquí ($208.50)
  0.618 retroceso → $202.95
  0.786 retroceso → $195.06
  Extensión 1.272 → $244.78
  Extensión 1.618 → $261.05

  Confluencia: 0.618 ($202.95) coincide con SMA 200 ($198.00) dentro de
  ~2.5% → nivel fuerte.

  Entrada sugerida: $208.50 (precio actual, ya en 0.500)
  SL: $200.00 (justo bajo 0.618 + SMA 200 — confluencia fuerte)
  TP1: $232.00 (swing high previo, más cerca que extensión 1.272)
  TP2: $244.78 (extensión 1.272)

Paso 8 — R:R:
  Riesgo: $208.50 − $200.00 = $8.50
  Recompensa TP1: $232.00 − $208.50 = $23.50
  R:R = 1:2.76 ✅ favorable

Paso 9 — Cronograma modulado:
  Postura NEUTRAL → entrada 50% en Semana 1, 50% en Semana 2 al
  confirmar ruptura del triángulo.

Paso 10 — Invalidación técnica: NO aplica (postura no es bearish).
```

Salida al bloque del Tab 1:

```
Setup técnico JPM:
  - Postura: NEUTRAL (2 señales alcistas, 2 bajistas)
  - Patrón: triángulo simétrico en formación (no confirmado)
  - Divergencias: MACD alcista tentativa
  - Entrada sugerida: $208.50 (Fibonacci 0.500 del swing $185.00-$232.00)
  - SL: $200.00 (confluencia Fibonacci 0.618 + SMA 200)
  - TP1: $232.00 (swing high previo)
  - TP2: $244.78 (extensión Fibonacci 1.272)
  - R:R: 1:2.76
```

## Invariantes del skill

```
1. Los SL y TP presentados al usuario DEBEN venir del paso 7 del
   protocolo. No se permite "SL al -10% redondo" si el paso 7 dio un
   nivel técnico. Si lo ves, el skill falló: volver al paso 7.

2. Si el R:R técnico < 1:1.5, NO se puede presentar el ticker como
   "entrada ahora". O se pospone, o se reporta la limitación.

3. La postura técnica NO modifica el peso de la posición. Eso es
   jurisdicción de risk_rules.md R1-R6.

4. Si el vertical que llamó al skill es `defi_skill` y la posición es
   stablecoin/staking/LP, responder "no aplica" y salir. No forzar
   patrones sobre USDC en Aave.

5. No duplicar llamadas a tools. Los datos ya están en memoria del
   vertical. Solo pedir ATR o OHLC si genuinamente faltan.

6. Si falta data crítica (< 60 días de OHLC, volumen ilíquido, earnings
   en < 5 días), reportar "sin señal clara" en vez de inventar.

7. Los patrones identificados deben tener ≥ 15 días de formación. Nada
   intradía.

8. Volumen en la ruptura es confirmatorio. Patrón sin volumen =
   "tentativo", no "confirmado".
```

## Auto-chequeo antes de devolver control al vertical

Antes de que el vertical siga con `calculate_scenarios`, este skill debe
haber entregado, por cada posición direccional:

```
□ Postura técnica declarada (BULLISH / NEUTRAL / BEARISH / sin señal clara)
□ Patrón (nombre o "ninguno") con flag confirmado / tentativo
□ Divergencias MACD y RSI chequeadas
□ Entrada sugerida con justificación (nivel de Fibonacci o swing)
□ SL técnico (Fibonacci, swing low, o ATR fallback documentado)
□ TP1 y TP2 técnicos con R:R calculado
□ R:R ≥ 1:1.5 verificado (o reporte de limitación)
□ Pauta de cronograma para el Tab 2 según postura
□ Verificación de invalidación técnica (§ Parte 4)
```

Si algún punto queda vacío, el skill no terminó. No continuar.

## Política de ejemplos (v1.1)

**Regla de diseño:** los ejemplos didácticos de este skill rotan
deliberadamente entre tickers de sectores distintos (ver
`equity_skill.md` § "Política de ejemplos" para el set rotatorio
canónico: JPM, KO, BAC, LMT, XOM, JNJ, MSFT, V, PG, UNH, DIA, IWM, etc.).

### Por qué importa para este skill

El "Ejemplo real" (§ arriba) es el bloque más copiado por el modelo
cuando aprende patrones de salida. Si siempre fuera NVDA, el agente
internalizaría asociaciones espurias del tipo:
  - "rango $95-$142" → suena a NVDA → sugerir NVDA
  - "neutral con divergencia MACD" → respuesta tipo NVDA
  - "R:R 1:4.47" → magnitud típica del ejemplo NVDA

Rotando el ticker del ejemplo (en v1.1, NVDA → JPM), el modelo asocia
el **patrón estructural** (postura neutral, confluencia Fib+SMA, R:R
favorable) con la **forma del análisis**, no con un símbolo concreto.

### Reglas de rotación para futuros ejemplos en este archivo

```
1. Cuando se actualice este "Ejemplo real" en una versión futura,
   cambiar también el ticker — no reescribir números manteniendo NVDA
   por inercia.

2. Los precios y rangos del ejemplo deben ser plausibles para el
   ticker elegido en el momento de la edición (ej. JPM en rango
   $185-$232 es realista para 2026; un rango $40-$70 no lo sería).

3. El sector del ticker debe variar entre versiones: si v1.1 es
   financials (JPM), v1.2 podría ser healthcare (UNH), v1.3 industrials
   (LMT), etc.

4. Conservar las mismas señales pedagógicas (postura NEUTRAL, MACD
   divergente, confluencia Fib + SMA, R:R favorable). Lo que rota es
   el ticker y los precios, no el aprendizaje.

5. Las menciones genéricas a `<TICKER>` en plantillas (Tab 1, salidas
   estándar) NO se cambian — son placeholders por diseño.
```
