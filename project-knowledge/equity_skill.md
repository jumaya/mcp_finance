# Skill: Acciones y ETFs — v9.0

> **Changelog v9.0:** eliminado el universo cerrado de tickers (listas fijas
> por riesgo tipo `ALTO: NVDA, TSLA, AMD…`). Los candidatos ahora se
> **descubren dinámicamente** vía `tradingview.screen_stocks` con filtros
> derivados del **perfil** del usuario (volatilidad, beta, market cap,
> liquidez, sector). Esto elimina el sesgo hacia NVDA y otros tickers
> "favoritos" que estaban hardcoded, y garantiza que cada sesión se trabaje
> con el universo real del mercado en ese momento. Ver § "Descubrimiento
> dinámico de candidatos".
>
> **Changelog v8.1:** la tabla de volatilidades pasa de "valores exactos
> obligatorios" a **fallback documentado**. Fuente primaria ahora es el
> cálculo en vivo desde Alpha Vantage (`TIME_SERIES_DAILY`, últimos 30 días
> para `volatility_30d` y ~252 días para `max_drawdown_12m`). La tabla
> solo se usa cuando la tool falla, con motivo logueado al usuario.
> Ver § "Volatilidad y max drawdown: fuente primaria vs. fallback".

## Descubrimiento dinámico de candidatos (OBLIGATORIO antes de cualquier análisis)

**Regla dura:** este skill NO mantiene listas fijas de tickers por riesgo.
El universo de candidatos se genera en vivo vía `tradingview.screen_stocks`
usando filtros derivados del **perfil** del usuario. No hay shortcuts tipo
"NVDA porque siempre sale" ni "VOO porque es el default conservador".

### Por qué esta regla

Las listas fijas de tickers crean tres problemas:
  1. **Sesgo de autor**: los tickers que aparecen son los que el diseñador
     del skill conocía al momento de escribirlo (ej. NVDA post-2023). El
     mercado rota; la lista no.
  2. **Universo cerrado**: un candidato que cumple el perfil del usuario
     pero no está en la lista nunca se considera. El usuario pierde
     oportunidades.
  3. **Falsa diversificación**: 3 de 5 "tickers ALTO" pueden ser del mismo
     sector (semiconductores/IA). Descubrir en vivo permite exigir
     diversificación sectorial explícita en los filtros.

### Perfiles por características (NO por tickers)

Cada perfil de riesgo se define por rangos de métricas observables, no por
nombres de empresa. El agente mapea el perfil del usuario → filtros de
screener → candidatos.

```
PERFIL RIESGO ALTO (growth / momentum / convicción con leverage)
  Objetivo: activos con movimiento suficiente para justificar CFD 2x.
  Filtros screen_stocks:
    - Volatility.M            > 6       (vol mensual > 6%, ~35% anualizada)
    - market_cap_basic        > 10_000_000_000   (>$10B, evita micro-caps)
    - average_volume_30d_calc > 5_000_000        (>5M sh/día, liquidez)
    - Perf.3M                 > 0       (momentum positivo 3m, opcional)
    - exchange in [NASDAQ, NYSE]
    - is_primary = true
    - typespecs has ["common"]          (evita ADRs sin liquidez, warrants)
  Ordenamiento sugerido: sort_by="Volatility.M", sort_order="desc"
  Límite: 20 candidatos brutos (luego se filtra por gate eToro)

PERFIL RIESGO MODERADO (core growth, large cap tech/consumer)
  Objetivo: exposición a crecimiento sin volatilidad extrema.
  Filtros screen_stocks:
    - Volatility.M            in [3, 6]          (vol mensual 3-6%)
    - market_cap_basic        > 50_000_000_000   (>$50B, blue-chip)
    - beta_1_year             in [0.8, 1.5]
    - average_volume_30d_calc > 3_000_000
    - Perf.Y                  > -0.15            (no en drawdown severo)
    - exchange in [NASDAQ, NYSE]
    - is_primary = true
  Ordenamiento: sort_by="market_cap_basic", sort_order="desc"
  Límite: 15-20 candidatos

PERFIL RIESGO BAJO (income / preservación / ETFs amplios)
  Objetivo: yield sostenible + baja volatilidad + baja correlación con
  la acción individual.
  Filtros screen_stocks:
    - dividend_yield_recent   > 2       (>2% yield)
    - beta_1_year             < 1
    - Volatility.M            < 3       (vol mensual < 3%)
    - market_cap_basic        > 20_000_000_000
    - continuous_dividend_payout > 5    (≥5 años pagando dividendo)
    - exchange in [NASDAQ, NYSE]
    - is_primary = true
  Ordenamiento: sort_by="dividend_yield_recent", sort_order="desc"
  Límite: 15 candidatos
```

> **Nota sobre unidades de `Volatility.M`:** TradingView expone este campo
> como percent (ej. `6` = 6% mensual). Para convertir a volatilidad anual
> aproximada, usar `σ_anual ≈ Volatility.M/100 × sqrt(12)`. Un filtro
> `Volatility.M > 6` captura activos con σ_anual ≳ 0.21; `> 10` captura
> σ_anual ≳ 0.35. Ajustar el umbral si el usuario tiene un sesgo
> específico en su perfil documentado.

### Protocolo de descubrimiento (4 pasos)

```
PASO 1 — Mapear perfil del usuario → filtros
  Leer el perfil del usuario (riesgo_general, verticales_activos, sesgos
  declarados). Elegir el bloque de filtros de arriba (ALTO | MODERADO |
  BAJO). Si el usuario pidió algo específico en la sesión ("quiero
  semiconductores") añadir filtro `sector equal "Electronic Technology"`
  o equivalente.

PASO 2 — Llamar al screener
  tradingview.screen_stocks(
    filters=[...bloque del perfil...],
    columns=["name", "close", "market_cap_basic", "Volatility.M",
             "beta_1_year", "dividend_yield_recent", "Perf.3M",
             "Perf.Y", "sector", "average_volume_30d_calc",
             "RSI", "SMA50", "SMA200"],
    sort_by=...,
    sort_order="desc",
    limit=20,
    markets=["america"]
  )

  Si el screener devuelve < 5 candidatos → relajar UN filtro a la vez
  (en este orden: average_volume_30d_calc → Perf.3M → market_cap_basic).
  Loguear al usuario qué filtro se relajó y por qué.

PASO 3 — Diversificación sectorial (pre-gate)
  Sobre los N candidatos brutos, antes del gate eToro:
    - Agrupar por `sector`.
    - Si un sector concentra > 60% de los candidatos (ej. 14 de 20 son
      "Electronic Technology"), recortar a máximo 5 por sector antes
      de seguir. Esto evita pasar el gate solo para acabar recomendando
      3 semiconductores.
  Si el usuario pidió explícitamente un sector, este paso se omite
  (pero se loguea).

PASO 4 — Gate eToro sobre TODOS los candidatos
  Ejecutar el gate de disponibilidad eToro (sección más abajo) sobre
  los N candidatos que sobrevivieron al PASO 3 — NO solo sobre los 3
  que el agente "ya eligió". Solo después de que el gate filtre a
  operables, el agente reduce a los 3 finales a presentar al usuario
  aplicando:
    - R:R técnico (via technical_skill.md)
    - correlación entre sí (via calculate_correlation)
    - match con sesgos/tesis del usuario
```

> ⚠️ Los candidatos que salen del screener son el **universo dinámico**
> de la sesión. Ningún ticker se presenta al usuario hasta pasar el
> **Gate de disponibilidad eToro** (ver sección dedicada abajo).

### Qué hacer si el screener falla

Prioridad de fallback (en este orden):
  1. Reintentar con el preset equivalente:
     - ALTO → `tradingview.get_preset("momentum_stocks")` o
       `"growth_stocks"`, luego `screen_stocks` con esos filtros.
     - MODERADO → `get_preset("quality_growth_screener")`.
     - BAJO → `get_preset("dividend_stocks")` o `"quality_stocks"`.
  2. Si los presets también fallan: NO caer a una lista hardcoded.
     Informar al usuario literal:
     > "El screener de TradingView no está respondiendo ahora. Puedo
     > trabajar con tickers que tú me des explícitamente (3-6 símbolos),
     > o esperar y reintentar en unos minutos."
     Esto es preferible a inventar una lista sesgada sobre la marcha.

## Apalancamiento eToro CFDs
```
Riesgo ALTO → CFD 2x en acciones de convicción
  NUNCA 5x con capital < $1000
  Ganancia +20% con 2x = +40% real
  Pérdida -50% con 2x = LIQUIDACIÓN TOTAL

ETFs apalancados (TQQQ, SOXL, etc.): solo si el screener los devuelve
  Y el usuario explícitamente pidió momentum con hold < 3 meses.
  NO son el default para perfil ALTO.
PROHIBIDO para perfil ALTO: ETFs amplios sin apalancamiento (VOO, VT,
  SCHD, QQQ sin leverage) — no ofrecen convicción direccional suficiente.
```

## Volatilidad y max drawdown: fuente primaria vs. fallback

**Regla dura (v8.1):** el valor de `volatility_30d` y `max_drawdown_12m`
que se pasa a `calculate_risk_score` SIEMPRE se prefiere calculado en
vivo desde Alpha Vantage sobre los últimos 30 días (vol) y últimos
12 meses (drawdown). El fallback por categoría (sección de abajo) es
**solo fallback documentado** cuando la tool falla, devuelve rate-limit,
o no tiene data suficiente para el ticker.

### Protocolo de cálculo (fuente primaria — Alpha Vantage)

```
POR CADA ticker, antes de llamar calculate_risk_score:

  1. Pedir serie diaria:
     alphavantage.TOOL_CALL(
       name="TIME_SERIES_DAILY",
       symbol="<TICKER>",
       outputsize="compact"    ← últimos ~100 días, suficiente
     )

  2. Calcular volatility_30d:
     → tomar los últimos 30 cierres diarios
     → calcular retornos logarítmicos: r_t = ln(P_t / P_{t-1})
     → stdev muestral de esos 30 retornos → σ_daily
     → anualizar: volatility_30d = σ_daily * sqrt(252)
     → redondear a 2 decimales

  3. Calcular max_drawdown_12m:
     → con outputsize="compact" (~100 días) solo cubre ~5 meses,
       así que si se necesita drawdown real 12m pedir:
       alphavantage.TOOL_CALL(name="TIME_SERIES_DAILY",
                              symbol="<TICKER>", outputsize="full")
     → tomar los últimos 252 cierres (~12 meses)
     → running_max = max acumulado del precio
     → drawdown_t = (P_t - running_max_t) / running_max_t
     → max_drawdown_12m = min(drawdown_t)  (número negativo)

  4. Loguear en la respuesta al usuario (sección datos):
     "volatility_30d=0.XX (calculada en vivo desde Alpha Vantage,
      30d hasta <fecha>)"

Criterios para caer a fallback:
  - La tool devuelve error, rate-limit (nota "call frequency"),
    o payload vacío.
  - Hay < 20 cierres diarios disponibles (ticker nuevo o suspendido).
  - El número calculado sale fuera de [0.03, 1.50] para vol anual
    (claro síntoma de data corrupta).
```

### Fallback por perfil/sector (usar SOLO si falla el cálculo en vivo)

```
⚠️ Estos rangos son **genéricos por categoría**, no listas de tickers
hardcoded. Se usan únicamente cuando Alpha Vantage falla y TradingView
tampoco tiene `Volatility.M` disponible para el ticker descubierto por
el screener. Los rangos son anclas conservadoras, no valores exactos.

| Categoría del activo                      | volatility_30d | max_drawdown_12m |
|-------------------------------------------|---------------|------------------|
| ETF amplio mercado (S&P 500, MSCI World)  | 0.10          | -0.15            |
| ETF sectorial large-cap (QQQ, XLK, XLF)   | 0.15          | -0.22            |
| Blue-chip large-cap estable (mega-cap)    | 0.15          | -0.22            |
| Blue-chip large-cap con beta>1            | 0.20          | -0.28            |
| Growth large-cap (SaaS, consumer tech)    | 0.30          | -0.40            |
| Growth mid-cap / semiconductores          | 0.35          | -0.45            |
| High-beta / fintech / discretionary alto  | 0.40          | -0.50            |
| Proxy cripto (mineros, exchanges, BTC-related) | 0.55     | -0.65            |
| ETF apalancado 2x-3x                      | 0.60          | -0.70            |

Cómo clasificar un ticker en una categoría (sin lista fija):
  1. Obtener del screener (o de `yfinance_get_ticker_info`):
       sector, market_cap_basic, beta_1_year, Volatility.M (si la hay).
  2. Mapear con reglas simples:
       - market_cap > $200B y beta < 1.1 → "Blue-chip estable".
       - market_cap > $50B y beta in [1.1, 1.5] → "Blue-chip con beta>1".
       - sector "Electronic Technology" y market_cap 10-100B → "Growth
         mid-cap / semis".
       - industry "Information Technology Services" o "Packaged Software"
         y market_cap > 10B → "Growth large-cap SaaS".
       - Nombre del instrumento contiene "2X"/"3X"/"Ultra"/"Bull" → ETF
         apalancado.
       - Ticker aparece en industry "Investment Trusts/Mutual Funds" o
         "Finance/Rental/Leasing" con "Bitcoin"/"Crypto" en el nombre
         → "Proxy cripto".
  3. Si no encaja claro en ninguna, usar la categoría inmediatamente más
     conservadora (mayor vol) para no subestimar el riesgo.

Cuándo usar este fallback:
  1. Alpha Vantage falló Y TradingView no devolvió `Volatility.M` válido
     para el ticker:
       → clasificar el ticker en una categoría (pasos 1-3 de arriba)
       → usar el valor de la categoría Y loguear explícitamente:
         "volatility_30d=0.XX (FALLBACK categoría '<Growth large-cap SaaS>',
          Alpha Vantage y Volatility.M no disponibles: <motivo>)"
  2. Alpha Vantage falló PERO TradingView sí devolvió `Volatility.M`:
       → usar `Volatility.M/100 × sqrt(12)` como aproximación de
         `volatility_30d` anualizada y loguear:
         "volatility_30d=0.XX (FALLBACK derivado de Volatility.M de
          TradingView, Alpha Vantage no disponible)"
  3. Si ninguna fuente responde → NO inventar: informar al usuario
     "no es posible calcular risk score confiable para <TICKER>
      ahora mismo" y descartar el ticker para esta sesión.

El fallback NUNCA se usa si la tool devolvió un número válido. El número
real del mercado manda.
```

## Cómo llamar calculate_risk_score (ejemplo)
```
Para NOW con CFD 2x, peso 35% (cálculo en vivo, caso normal):
  # Paso previo: alphavantage TIME_SERIES_DAILY → σ_anual ≈ 0.31
  # Paso previo: running max sobre 252 cierres → dd ≈ -0.38
  calculate_risk_score(
    volatility_30d=0.31,      ← calculada en vivo (Alpha Vantage 30d)
    max_drawdown_12m=-0.38,   ← calculada en vivo (AV 12m)
    liquidity="instant",
    platform_regulated=true,
    weight_in_portfolio_pct=35,
    leverage=2.0
  )
  Resultado esperado: ~7.5-8.5 "high" (leverage floor del server.py)

Para NOW con CFD 2x (modo fallback, si Alpha Vantage cayó):
  # Clasificación: sector=Technology Services, market_cap ~$170B, beta~1.1
  #   → categoría "Growth large-cap SaaS" → vol≈0.30, dd≈-0.40
  calculate_risk_score(
    volatility_30d=0.30,      ← FALLBACK categoría "Growth large-cap SaaS" (loguear)
    max_drawdown_12m=-0.40,   ← FALLBACK misma categoría (loguear)
    liquidity="instant",
    platform_regulated=true,
    weight_in_portfolio_pct=35,
    leverage=2.0
  )

Para un ETF S&P 500 spot, peso 20% (ej. ticker descubierto por screener
con filtros de perfil BAJO):
  calculate_risk_score(
    volatility_30d=0.12,      ← calculada en vivo si AV responde,
    max_drawdown_12m=-0.20,   ←  si no, fallback categoría "ETF amplio mercado"
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
  → NO buscar reemplazo "a ojo": el reemplazo sale de la lista de
    candidatos que ya devolvió el screener (siguiente ticker con perfil
    similar en sector y volatilidad). Si se agota la lista de candidatos
    operables en un sector, pasar al siguiente sector del screener.
  → Si tras procesar todos los candidatos del screener no hay
    suficientes operables (< 3), informar al usuario explícitamente
    antes de seguir y ofrecer relajar un filtro del perfil.
```

### Batch al inicio del análisis
Sobre los N candidatos que devolvió `tradingview.screen_stocks` (después
de la diversificación sectorial), ejecuta el gate eToro para **todos**
antes de llamar a Alpha Vantage / Yahoo / TradingView para datos
fundamentales. Evita trabajar datos detallados sobre activos que luego
vas a descartar por no estar operables.

Orden recomendado en una sesión típica:
```
  screen_stocks (20 candidatos)
    → diversificación sectorial (≤ 5 por sector → p.ej. 15 candidatos)
    → gate eToro batch sobre los 15
    → los operables (ej. 11 pasan) → análisis fundamental/técnico
    → reducir a 3 finales por R:R, correlación y match con tesis
```

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
AL INICIO DE LA SESIÓN (una sola vez, antes del loop por candidato):

  0'. 🔭 Descubrimiento dinámico (bloqueante):
      tradingview.screen_stocks(filters=<según perfil del usuario>, limit=15-20)
      → aplicar diversificación sectorial (≤ 5 por sector salvo petición
        explícita del usuario)
      → si el screener falla: intentar presets equivalentes
        (get_preset → screen_stocks); si también fallan, NO inventar
        lista — pedir tickers al usuario o reintentar luego.
      → resultado: lista de N candidatos brutos para esta sesión.

POR CADA acción candidata de la lista anterior (en este ORDEN):

  0. 🚪 GATE eToro (bloqueante):
     etoro-server.search_instruments(query="<TICKER>", ...)
     → si no pasa, DESCARTAR y no seguir con esta candidata
     → recomendado: ejecutar este gate en BATCH sobre todos los N
       candidatos antes de entrar al paso 1, para no gastar API
       de Alpha Vantage en activos no operables.

  1. Alpha Vantage → precio, RSI, MACD, SMA50, SMA200, TIME_SERIES_DAILY
     → Calcular EN VIVO volatility_30d y max_drawdown_12m desde la
       serie diaria (ver § "Volatilidad y max drawdown: fuente primaria
       vs. fallback" arriba para la fórmula exacta).
     → Si la tool falla / rate-limit / data insuficiente:
         usar el fallback por categoría (ver § "Fallback por perfil/sector")
         clasificando el ticker según sector + market_cap + beta. LOGUEAR
         explícitamente el motivo en la sección de datos del plan.
     → Guardar vol_calculada y dd_calculado para pasos 4 y 5.
  2. Yahoo Finance → yfinance_get_ticker_info(symbol="<TICKER>")
     → extraer TODOS los campos obligatorios de la sección
       "Extracción de datos de ticker_info" (earnings + consenso
       analistas + momentum relativo al S&P). No basta con llamar
       la tool; hay que LEER el payload y presentar los campos.
  3. TradingView → señal técnica (datos ya recolectados en paso 0'
     si se hizo screening; si no, llamar screen_stocks con filtro
     puntual para este ticker).
  3.5. 🧭 technical_skill.md (si la posición es direccional):
     → Pasa a este skill los datos recolectados en los pasos 1-3
       (OHLC, RSI, MACD, SMA50, SMA200, señal TradingView).
     → Espera recibir de vuelta: postura técnica, patrón, divergencias,
       entrada sugerida, SL, TP1, TP2, R:R, pauta de cronograma.
     → Si technical_skill reporta R:R < 1:1.5, anotar la limitación en
       el Tab 1 y considerar reemplazo o entrada pospuesta.
     → Los SL/TP técnicos SUSTITUYEN a cualquier SL/TP "redondo"
       (ej. -10%) que se hubiera considerado.
  4. calculate_risk_score(vol_calculada, dd_calculado, "instant", true, peso, leverage)
     → vol y dd vienen del paso 1 (preferente: cálculo en vivo;
       fallback: categoría, con motivo logueado).
  5. calculate_scenarios(
        monto, apy, vol_calculada, passive_bruto, meses, leverage, monthly_cost,
        dividend_withholding_pct=0.30 si US y paga dividendo (else 0.0)
     )
     → Pasar dividendo BRUTO; la tool aplica la retención.
     → Ver sección "Retención de dividendos USA" arriba.
  6. Si 2+ acciones: calculate_correlation
```

**Invariante:** los pasos 1-6 nunca se ejecutan sobre un ticker que
falló el paso 0. El paso 0 nunca se ejecuta sobre un ticker que no
viene del paso 0' (o, excepcionalmente, que el usuario pidió por
nombre explícito). Si lo haces, estás sesgando el universo con
"tickers de memoria" del agente.

**Invariante técnico:** si se presenta una acción como "entrada ahora"
en el plan, los SL y TP de esa posición deben venir de technical_skill.md
(Fibonacci, swing, o ATR fallback documentado). SL genéricos tipo "-10%"
no son aceptables salvo que technical_skill haya reportado explícitamente
"sin señal clara — usar ATR fallback".

**Invariante earnings:** si el paso 2 se ejecutó pero la respuesta al
usuario no contiene una fecha concreta de earnings (o la nota
"no disponible vía Yahoo Finance"), el paso 2 no está completo.
Volver a leer el payload.

**Invariante volatilidad:** el número que entra a `calculate_risk_score`
y `calculate_scenarios` como `volatility_30d` debe ser trazable a una
de estas dos fuentes (en este orden de preferencia):
  1. Cálculo en vivo sobre TIME_SERIES_DAILY de Alpha Vantage (preferido).
  2. Fallback por categoría documentado en este skill (solo si 1 falló,
     con el motivo logueado al usuario; la categoría se deriva de
     sector + market_cap + beta del ticker, NO de una tabla fija
     por nombre).
Si no se puede garantizar ninguna de las dos, descartar el ticker;
no inventar un número "aproximado".

**Invariante universo:** ningún ticker llega al usuario sin haber pasado
por el paso 0' (descubrimiento) o haber sido pedido explícitamente por
nombre. Si el agente encuentra que está recomendando siempre los mismos
3-4 tickers sesión tras sesión, eso es señal de que el screener no se
está ejecutando realmente o los filtros son demasiado estrechos —
revisar y ampliar el perfil antes de recomendar.
