# Skill: Acciones y ETFs — v8

## Activos por riesgo
```
ALTO: NVDA, TSLA, AMD, COIN, MSTR, PLTR, SOFI, RIOT, MARA, SNOW, NOW, INTU, CRM
  ETFs apalancados: TQQQ, SOXL (solo momentum, NO hold >3 meses)
  PROHIBIDO: VOO, VT, SCHD, QQQ sin apalancamiento

MODERADO: QQQ, XLK, AAPL, MSFT, GOOGL, AMZN
BAJO: VOO, VT, SCHD
```

> ⚠️ Esta lista es el **universo teórico**. Ningún ticker se presenta al
> usuario hasta pasar el **Gate de disponibilidad eToro** (ver abajo).

## Apalancamiento eToro CFDs
```
Riesgo ALTO → CFD 2x en acciones de convicción
  NUNCA 5x con capital < $1000
  Ganancia +20% con 2x = +40% real
  Pérdida -50% con 2x = LIQUIDACIÓN TOTAL
```

## Tabla de volatilidades por ticker (usar en calculate_risk_score)
```
USAR ESTOS VALORES EXACTOS — no estimar ni usar rangos:

| Ticker | volatility_30d | max_drawdown_12m | Notas                    |
|--------|---------------|------------------|--------------------------|
| NVDA   | 0.35          | -0.45            | Semiconductores/IA       |
| TSLA   | 0.45          | -0.55            | Muy volátil, polarizante |
| AMD    | 0.30          | -0.40            | Semiconductores          |
| COIN   | 0.50          | -0.60            | Proxy cripto, beta ~3x   |
| MSTR   | 0.55          | -0.65            | Proxy BTC apalancado     |
| PLTR   | 0.35          | -0.40            | IA gobierno/empresa      |
| SNOW   | 0.35          | -0.45            | SaaS cloud data          |
| NOW    | 0.30          | -0.40            | SaaS enterprise          |
| RIOT   | 0.55          | -0.65            | Minero BTC               |
| MARA   | 0.55          | -0.65            | Minero BTC               |
| SOFI   | 0.40          | -0.50            | Fintech                  |
| INTU   | 0.25          | -0.35            | SaaS finanzas            |
| CRM    | 0.25          | -0.35            | SaaS enterprise          |
| AAPL   | 0.12          | -0.20            | Blue-chip                |
| MSFT   | 0.12          | -0.18            | Blue-chip                |
| GOOGL  | 0.15          | -0.22            | Blue-chip                |
| AMZN   | 0.18          | -0.25            | E-commerce + cloud       |
| QQQ    | 0.12          | -0.20            | ETF Nasdaq 100           |
| VOO    | 0.08          | -0.15            | ETF S&P 500              |

Si el ticker NO está en esta tabla:
  → Buscar volatilidad real en Alpha Vantage o TradingView
  → Usar como referencia el activo más similar de la tabla
```

## Cómo llamar calculate_risk_score (ejemplo)
```
Para NOW con CFD 2x, peso 35%:
  calculate_risk_score(
    volatility_30d=0.30,      ← de la tabla
    max_drawdown_12m=-0.40,   ← de la tabla
    liquidity="instant",
    platform_regulated=true,
    weight_in_portfolio_pct=35,
    leverage=2.0
  )
  Resultado esperado: ~7.5-8.5 "high" (por la tabla + leverage floor del server.py)

Para AAPL spot, peso 20%:
  calculate_risk_score(
    volatility_30d=0.12,
    max_drawdown_12m=-0.20,
    liquidity="instant",
    platform_regulated=true,
    weight_in_portfolio_pct=20,
    leverage=1.0
  )
  Resultado esperado: ~2.5-3.5 "low"
```

## Overnight fees (SIEMPRE incluir en CFDs)
```
Fee mensual ≈ monto × apalancamiento × 0.015% × 30
  $175 con 2x → ~$1.58/mes
  $200 con 2x → ~$1.80/mes

Pasar como monthly_cost_usd en calculate_scenarios:
  calculate_scenarios(monto, apy, vol, 0, meses, leverage=2.0, monthly_cost_usd=1.58)
```

## Retención de dividendos USA (SIEMPRE incluir si hay dividendos)

Los dividendos pagados por emisores US a residentes no-US sin tratado
(Colombia NO tiene tratado fiscal con US) se pagan **netos del 30% de
retención en origen** — ver `platforms_skill.md §1.5`.

```
Regla:
  - Si el activo es US (stock, ETF domiciliado en US: SPY, QQQ, VOO, VTI,
    DIA, IWM, etc.) Y paga dividendo:
       dividend_withholding_pct = 0.30

  - Si el activo es US pero NO paga dividendo (TSLA, GOOGL, BRK.B, AMZN,
    muchos de tech growth): el parámetro es irrelevante, dejar en 0.0.

  - Si el activo es no-US (ETFs UCITS irlandeses, acciones UK, DE, HK,
    etc.): la retención varía por país. Como proxy conservador:
       - UCITS (IE): 0.00  (ya incorporado al NAV)
       - UK listed: 0.00  (UK no retiene a no-UK holders en la mayoría)
       - DE listed: 0.26  (Kapitalertragsteuer)
       - HK listed: 0.00
    Si hay duda, preguntar al usuario antes que asumir.

Pasar passive_income_annual_usd como BRUTO (dividend_yield × monto, o
el forward dividend reportado por yfinance) y dejar que
calculate_scenarios aplique la retención. NO descontar a mano.
```

### Ejemplo concreto (SPY long spot, 12 meses)
```
SPY: precio $550, posición $5,000, dividend_yield ~1.3% → $65 anual bruto
APY esperado 10%, vol 15%

calculate_scenarios(
  amount_usd=5000,
  expected_apy=0.10,
  volatility_annual=0.15,
  passive_income_annual_usd=65,        ← BRUTO (no neto)
  months=12,
  leverage=1.0,
  monthly_cost_usd=0.0,
  dividend_withholding_pct=0.30,       ← US → 30%
)

Resultado en escenario base:
  passive_income_gross_usd: 65
  passive_income_net_usd:   45.50      ← lo que recibe el usuario
  withholding_deducted_usd: 19.50      ← IRS lo retiene
```

### Ejemplo con CFD 2x + dividendo (SPY CFD)
```
CFDs en eToro reciben dividendos equivalentes (adjustment) que también
están sujetos a retención. Combinación típica:

calculate_scenarios(
  amount_usd=500,                     ← margen
  expected_apy=0.10,
  volatility_annual=0.15,
  passive_income_annual_usd=13,       ← 1.3% sobre notional de $1,000
  months=6,
  leverage=2.0,
  monthly_cost_usd=4.50,              ← overnight fee mensual
  dividend_withholding_pct=0.30,      ← SPY = US
  funding_rate_daily_pct=0.0,         ← CFDs NO tienen funding (tienen overnight)
)
```

## 🚪 Gate de disponibilidad eToro (OBLIGATORIO antes de recomendar)

**Regla dura:** no se muestra al usuario ningún ticker que no haya pasado
este gate. eToro restringe instrumentos por jurisdicción, por tipo de
cuenta (demo/real) y por estado del mercado. Un ticker "famoso" puede
no estar listado para la cuenta del usuario desde Colombia.

### Protocolo
```
POR CADA ticker candidato (antes de cualquier otra tool):

  etoro-server.search_instruments(
    query="<TICKER>",
    search_by="internalSymbolFull",
    page_size=5
  )

Validar en el primer resultado cuyo internalSymbolFull coincida
(case-insensitive) con el ticker buscado:

  ✅ instrumentType ∈ {"Stocks", "Etf"}    → tipo correcto
  ✅ isCurrentlyTradable == true           → mercado operable ahora
  ✅ isBuyEnabled == true                  → se puede abrir long

Si las 3 pasan:
  → guardar instrumentId para get_rates / get_candles posteriores
  → continuar al resto del protocolo

Si alguna falla (o el ticker no aparece en results):
  → DESCARTAR el ticker para esta sesión
  → registrar el motivo: "not_listed" | "not_tradable" | "buy_disabled" | "wrong_type"
  → buscar reemplazo equivalente (mismo sector + volatilidad similar
    de la tabla de arriba) y repetir el gate con ese
  → si tras 2 intentos ningún candidato del sector pasa el gate,
    informar al usuario explícitamente antes de seguir
```

### Batch al inicio del análisis
Si vas a evaluar una lista de N tickers (ej. todo el grupo ALTO),
ejecuta el gate para todos **antes** de llamar a Alpha Vantage / Yahoo
/ TradingView. Evita trabajar datos fundamentales de activos que luego
vas a descartar.

### Qué decirle al usuario cuando se descarta un ticker
No ocultes la restricción — es información útil:

> "CRM no está disponible en tu cuenta eToro desde Colombia (o no es
> operable en este momento). Lo reemplacé por NOW, que tiene perfil
> similar (SaaS enterprise, volatilidad ~0.30). NOW sí pasó el gate."

## Extracción de datos de `yfinance_get_ticker_info` (obligatorio)

**Contexto crítico:** no existe una tool dedicada tipo `get_earnings` en
el MCP de yahoo-finance. Toda la información de earnings, consenso de
analistas y momentum viene **dentro del payload de `ticker_info`**. El
agente debe extraer explícitamente estos campos — no basta con llamar
la tool y resumir "en general".

### Campos obligatorios a extraer y presentar

| Campo JSON                    | Qué es                             | Cuándo mostrar |
|-------------------------------|------------------------------------|----------------|
| `earningsTimestampStart`      | Próximo earnings — inicio ventana  | SIEMPRE        |
| `earningsTimestampEnd`        | Próximo earnings — fin ventana     | SIEMPRE        |
| `isEarningsDateEstimate`      | `true` = no confirmada por empresa | SIEMPRE        |
| `earningsQuarterlyGrowth`     | Crecimiento EPS YoY último Q       | SIEMPRE        |
| `targetMeanPrice`             | Precio objetivo medio analistas    | SIEMPRE        |
| `currentPrice`                | Precio actual                      | SIEMPRE        |
| `recommendationKey`           | Consenso ("buy"/"hold"/"sell")     | SIEMPRE        |
| `numberOfAnalystOpinions`     | Nº de analistas cubriendo          | SIEMPRE        |
| `52WeekChange`                | Retorno 52 semanas acción          | SIEMPRE        |
| `SandP52WeekChange`           | Retorno 52 semanas S&P (benchmark) | SIEMPRE        |
| `fiftyDayAverage`             | SMA 50 (momentum corto)            | Opcional       |
| `twoHundredDayAverage`        | SMA 200 (tendencia larga)          | Opcional       |
| `earningsTimestamp`           | Último earnings reportado          | Opcional       |
| `earningsCallTimestampStart`  | Earnings call (si aplica)          | Opcional       |

### Formato de presentación

**Earnings:**
- Si `earningsTimestampStart == earningsTimestampEnd`:
  `"Próximo earnings: <dd-mm-yyyy> (estimada)" ` o `"(confirmada)"`
  según `isEarningsDateEstimate`.
- Si son distintos (ventana):
  `"Próximo earnings: entre <start> y <end> (estimada|confirmada)"`.
- Convertir el timestamp a formato es-CO (dd-mm-yyyy).
- Si `isEarningsDateEstimate == true` → añadir literal:
  "(estimada por Yahoo, no confirmada por la empresa)".

**Consenso analistas:**
- `"Consenso <N> analistas: <recommendationKey>. Target medio
  $<targetMeanPrice> vs actual $<currentPrice> (<upside>%)"`.

**Momentum relativo:**
- `"52W: <52WeekChange>% vs S&P <SandP52WeekChange>% → <outperform|underperform> por <diff> pts"`.

### Si los campos no están en el payload

No inventar. Literal:
> "Fecha de earnings no disponible vía Yahoo Finance para <TICKER>.
> Consultar directamente en investor.<empresa>.com."

**Prohibido:** frases vagas tipo *"Earnings season Q1 2026"*,
*"reporta en mayo"*, *"próximo trimestre"*. Violan el principio #1
del `system.md` (nunca inventes números).

### Por qué importa para el plan

Un earnings en < 30 días con CFD leverage ≥ 2x es un **evento binario
material**. Un reporte con guidance débil puede mover la acción -10%
intraday, que con 2x se convierte en -20% sobre la posición.

Añadir SIEMPRE al plan, en la sección de riesgos del ticker:
> "Earnings el <fecha>: evento binario. Considerar cerrar o reducir
> posición 24-48h antes si no hay apetito por gap overnight."

### Ejemplo real (CRM, validado 18-abr-2026)

Payload real de `yfinance_get_ticker_info("CRM")`:
```json
{
  "earningsTimestampStart": "2026-05-27 15:00:00",
  "earningsTimestampEnd":   "2026-05-27 15:00:00",
  "isEarningsDateEstimate": true,
  "earningsQuarterlyGrowth": 0.138,
  "currentPrice": 182.14,
  "targetMeanPrice": 268.87,
  "recommendationKey": "buy",
  "numberOfAnalystOpinions": 52,
  "52WeekChange": -0.229,
  "SandP52WeekChange": 0.3815,
  "fiftyDayAverage": 188.0,
  "twoHundredDayAverage": 232.75
}
```

**Salida correcta al usuario:**
> - Próximo earnings: **27-05-2026** (estimada por Yahoo, no confirmada).
> - Último Q: +13.8% crecimiento EPS YoY.
> - Consenso 52 analistas: **buy**. Target medio $268.87 vs actual
>   $182.14 → upside +47.6%.
> - 52W: -22.9% vs S&P +38.2% → underperform -61 pts (CRM en drawdown
>   fuerte relativo al mercado).
> - Precio bajo SMA50 ($188) y SMA200 ($232.75) → momentum bearish.
> - Si la posición CFD 2x sigue abierta el 26-05, considerar reducir
>   antes del reporte.

**Salida incorrecta (NO hacer):**
- ❌ "Earnings season Q1 2026: monitorear si CRM reporta"
- ❌ "CRM reporta en mayo"
- ❌ "Los analistas son positivos"

## Tool calls obligatorios
```
POR CADA acción candidata (en este ORDEN):

  0. 🚪 GATE eToro (bloqueante):
     etoro-server.search_instruments(query="<TICKER>", ...)
     → si no pasa, DESCARTAR y no seguir con esta candidata

  1. Alpha Vantage → precio, RSI, MACD, SMA50, SMA200
  2. Yahoo Finance → yfinance_get_ticker_info(symbol="<TICKER>")
     → extraer TODOS los campos obligatorios de la sección
       "Extracción de datos de ticker_info" (earnings + consenso
       analistas + momentum relativo al S&P). No basta con llamar
       la tool; hay que LEER el payload y presentar los campos.
  3. TradingView → señal técnica
  3.5. 🧭 technical_skill.md (si la posición es direccional):
     → Pasa a este skill los datos recolectados en los pasos 1-3
       (OHLC, RSI, MACD, SMA50, SMA200, señal TradingView).
     → Espera recibir de vuelta: postura técnica, patrón, divergencias,
       entrada sugerida, SL, TP1, TP2, R:R, pauta de cronograma.
     → Si technical_skill reporta R:R < 1:1.5, anotar la limitación en
       el Tab 1 y considerar reemplazo o entrada pospuesta.
     → Los SL/TP técnicos SUSTITUYEN a cualquier SL/TP "redondo"
       (ej. -10%) que se hubiera considerado.
  4. calculate_risk_score(vol_tabla, dd_tabla, "instant", true, peso, leverage)
  5. calculate_scenarios(
        monto, apy, vol_tabla, passive_bruto, meses, leverage, monthly_cost,
        dividend_withholding_pct=0.30 si US y paga dividendo (else 0.0)
     )
     → Pasar dividendo BRUTO; la tool aplica la retención.
     → Ver sección "Retención de dividendos USA" arriba.
  6. Si 2+ acciones: calculate_correlation
```

**Invariante:** los pasos 1-6 nunca se ejecutan sobre un ticker que
falló el paso 0. Si lo haces, estás quemando llamadas de API en algo
que el usuario no puede operar.

**Invariante técnico:** si se presenta una acción como "entrada ahora"
en el plan, los SL y TP de esa posición deben venir de technical_skill.md
(Fibonacci, swing, o ATR fallback documentado). SL genéricos tipo "-10%"
no son aceptables salvo que technical_skill haya reportado explícitamente
"sin señal clara — usar ATR fallback".

**Invariante earnings:** si el paso 2 se ejecutó pero la respuesta al
usuario no contiene una fecha concreta de earnings (o la nota
"no disponible vía Yahoo Finance"), el paso 2 no está completo.
Volver a leer el payload.
