# Skill: Acciones y ETFs — v9.3

> **Changelog v9.3:** rotación deliberada de tickers en los ejemplos
> didácticos. Los ejemplos previos repetían NVDA/AAPL/SPY, lo cual no
> afecta funcionalidad pero entrena al modelo a "anclar" en esos
> nombres como referencia narrativa. A partir de v9.3 los ejemplos
> usan un **set rotatorio** (JPM, KO, BAC, LMT, XOM, JNJ, MSFT, V,
> PG, UNH, DIA, IWM, etc.) cubriendo distintos sectores y verticales.
> Las menciones a NVDA en las secciones de changelog v9.0/v9.1 se
> conservan porque están documentando precisamente el **anti-patrón**
> que se eliminó (no son ejemplos vivos). Ver § "Política de ejemplos"
> al final del documento.
>
> **Changelog v9.2:** el descubrimiento de candidatos ahora **arranca con
> el preset de TradingView** que `market_intelligence_skill.md §Paso 2`
> elige según el perfil del usuario, no con filtros propios del skill.
> El bloque de filtros por perfil (ALTO/MODERADO/BAJO) pasa de "fuente
> primaria" a "overlay que se anexa al preset" + "fallback si los presets
> caen". El motivo: los presets `tradingview.list_presets()` ya codifican
> estrategias bien probadas (momentum, quality_growth, dividend, value,
> deep_value, breakout, GARP…) que cubren mejor la intención del usuario
> ("dame momentum" → `momentum_stocks` directo) que reconstruirlas a mano
> aquí. Ver § "Descubrimiento dinámico de candidatos" → nuevo Paso 0' y
> Paso 2 del protocolo.
>
> **Changelog v9.1:** eliminada por completo la tabla de volatilidad/drawdown
> por categoría (que en v8.1 funcionaba como fallback documentado). La tabla,
> aunque genérica, seguía sembrando un universo de "anclas" que el agente
> podía usar como muleta narrativa ("NOW ~ Growth large-cap SaaS, vol≈0.30").
> El nuevo protocolo es estricto:
>   1. **Primaria:** cálculo en vivo desde Alpha Vantage (`TIME_SERIES_DAILY`).
>   2. **Fallback único:** `yfinance_get_ticker_info` (campos `beta`,
>      `fiftyDayAverage`, `twoHundredDayAverage`, `52WeekChange`) → derivar
>      `volatility_30d` y `max_drawdown_12m` por fórmula, no por tabla.
>   3. **Si ambas fallan → descartar el ticker para esta sesión.** No hay
>      tercera fuente, no hay categoría "conservadora por defecto".
> Ver § "Volatilidad y max drawdown: fuente primaria vs. fallback".
>
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
> *(Superado por v9.1: la tabla fue eliminada por completo.)*

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
nombres de empresa.

> **A partir de v9.2 estos bloques tienen DOS roles:**
>
> 1. **Overlays sobre el preset** (rol primario en el flujo nuevo): el
>    PASO 0 del protocolo recibe un preset elegido por
>    `market_intelligence_skill.md §Paso 2`. Los filtros de abajo se
>    anexan a los del preset (intersección) para acotar el universo del
>    preset al perfil del usuario.
> 2. **Filtros standalone** (rol fallback): si los presets de TradingView
>    caen, este skill opera con la matriz de abajo como filtros directos
>    al `screen_stocks`. Era el flujo de v9.1.
>
> En ambos casos los rangos siguen siendo los mismos.

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

### Protocolo de descubrimiento (5 pasos — v9.2)

```
PASO 0 — Recibir el preset elegido por market_intelligence_skill
  Antes de este skill, market_intelligence_skill.md §Paso 2 ya corrió y
  entregó un bloque "PRESET VERTICAL ELEGIDO" con:
    - preset_key (ej. "momentum_stocks", "quality_growth_screener",
                  "dividend_stocks", "deep_value", "breakout_scanner"…)
    - filters_base (los filters del preset, ya con sort_by/sort_order/markets)
    - overlays_perfil_sugeridos (filters adicionales del perfil del usuario)
    - razón_elección

  Si market_intelligence_skill NO corrió (caso raro: omitido por el
  orquestador o pidió explícitamente que se saltara), elegir preset
  localmente con la tabla resumida:
    PERFIL ALTO     + sin sesgo → "momentum_stocks"
    PERFIL MODERADO + sin sesgo → "quality_growth_screener"
    PERFIL BAJO     + sin sesgo → "dividend_stocks" o "quality_stocks"
  Y ejecutar:
    config = tradingview.get_preset(preset_key)
  El payload trae filters/sort_by/sort_order/markets listos para usar.

PASO 1 — Componer filtros finales: preset + overlays del perfil
  filtros_finales = filters_base ∪ overlays_perfil_sugeridos

  Los overlays del perfil sirven para acotar el universo del preset al
  perfil de riesgo del usuario (ver § "Perfiles por características"):
    PERFIL ALTO:
      + market_cap_basic        > 10_000_000_000
      + average_volume_30d_calc > 5_000_000
      + typespecs has ["common"]
    PERFIL MODERADO:
      + market_cap_basic        > 50_000_000_000
      + average_volume_30d_calc > 3_000_000
    PERFIL BAJO:
      + market_cap_basic        > 20_000_000_000
      + beta_1_year             < 1.2

  Si el usuario pidió un sector específico ("quiero semiconductores"),
  añadir aquí también: `sector equal "Electronic Technology"`.

  Conflicto: si un overlay del perfil contradice un filter del preset
  (ej. el preset trae `RSI in [50, 70]` y el overlay quería `RSI < 30`),
  el filter del PRESET gana — el preset codifica la estrategia, el
  overlay sólo la acota. Loguear el conflicto.

PASO 2 — Llamar al screener con filtros compuestos
  tradingview.screen_stocks(
    filters=filtros_finales,
    columns=["name", "close", "market_cap_basic", "Volatility.M",
             "beta_1_year", "dividend_yield_recent", "Perf.3M",
             "Perf.Y", "sector", "average_volume_30d_calc",
             "RSI", "SMA50", "SMA200"],
    sort_by=config.sort_by,          ← del preset
    sort_order=config.sort_order,    ← del preset
    limit=20,
    markets=config.markets           ← del preset (típicamente ["america"])
  )

  Si el screener devuelve < 5 candidatos → relajar overlays del PERFIL
  primero, no del preset (en este orden: average_volume_30d_calc →
  beta_1_year → market_cap_basic). Loguear al usuario qué filtro se
  relajó y por qué. Si tras relajar todos los overlays sigue < 5,
  mantener el preset puro (filters_base solo).

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

> 🪪 **Trazabilidad obligatoria:** en el plan final, dejar mención
> explícita del preset usado y los overlays. Ejemplo:
> > "Universo descubierto vía preset 'quality_growth_screener' de
> >  TradingView (ROE >15%, márgenes >12%, golden cross, RSI 45-65) +
> >  overlays de perfil moderado (mcap >$50B, volumen >3M/día). De los
> >  18 candidatos, 14 pasaron el gate eToro."
> Esto permite al usuario auditar el universo si pregunta "¿por qué
> estos tickers?".

### Qué hacer si los presets caen / fallan

Prioridad de fallback (en este orden):
  1. **Otro preset del mismo eje** del PASO 0 (ej. si `momentum_stocks`
     no responde para perfil ALTO → probar `growth_stocks`; si
     `quality_growth_screener` cae para MODERADO → probar `garp` o
     `quality_compounder`; si `dividend_stocks` cae para BAJO → probar
     `dividend_growth` o `quality_stocks`).
  2. **Filtros directos del perfil sin preset** (la matriz de
     "Perfiles por características" arriba — flujo v9.1 anterior). El
     vertical opera entonces sin preset, con su propia matriz de filtros.
     Loguear al usuario que el preset no respondió.
  3. **Si el screener directo también falla:** NO caer a una lista hardcoded.
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

**Regla dura (v9.1):** el valor de `volatility_30d` y `max_drawdown_12m`
que se pasa a `calculate_risk_score` se obtiene en este orden ESTRICTO:

  1. **Primaria — Alpha Vantage en vivo** (`TIME_SERIES_DAILY` → cálculo).
  2. **Fallback único — `yfinance_get_ticker_info`** (campos `beta`,
     `fiftyDayAverage`, `twoHundredDayAverage`, `52WeekChange`) → derivar
     ambos números por fórmula, no por tabla de categorías.
  3. **Si ambas fuentes fallan → DESCARTAR el ticker para esta sesión.**
     No existe una tercera fuente, ni una "categoría conservadora por
     defecto", ni un valor inventado "aproximado".

No hay tabla de tickers/categorías con valores hardcoded. La tabla previa
(v8.1) fue eliminada en v9.1 porque seguía actuando como ancla narrativa
("vol≈0.30 porque suena a SaaS") incluso cuando había datos reales
disponibles.

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

Criterios para caer al fallback de yfinance:
  - La tool de Alpha Vantage devuelve error, rate-limit (nota
    "call frequency"), o payload vacío.
  - Hay < 20 cierres diarios disponibles (ticker nuevo o suspendido).
  - El número calculado sale fuera de [0.03, 1.50] para vol anual
    (claro síntoma de data corrupta).
```

### Fallback único: `yfinance_get_ticker_info` (usar SOLO si Alpha Vantage falló)

```
POR CADA ticker que cayó al fallback:

  1. Llamar (si no se llamó ya en el paso 2 del protocolo general):
       yfinance.yfinance_get_ticker_info(symbol="<TICKER>")

  2. Derivar volatility_30d desde el payload:
     Estrategia preferida — proxy por `beta` y `52WeekChange`:
       → Si el payload trae `beta` (beta de 5 años vs. S&P 500):
           σ_market_anual = 0.18   (vol anualizada del S&P en régimen
                                    normal; si la sesión tiene clara
                                    señal de régimen alto en VIX, usar
                                    0.25 — DOCUMENTAR la elección).
           volatility_30d ≈ |beta| × σ_market_anual
       → Si el payload NO trae `beta` pero trae `fiftyDayAverage` y
         `currentPrice`, usar como proxy CONSERVADOR (no preferido):
           volatility_30d ≈ máx(0.20,
                                |currentPrice - fiftyDayAverage| /
                                fiftyDayAverage × sqrt(12))
         (este proxy infraestima si la acción ha sido lateral durante
          50 días — por eso el piso de 0.20).

  3. Derivar max_drawdown_12m desde el payload:
     → Si el payload trae `52WeekChange`:
         max_drawdown_12m ≈ mín(52WeekChange, -0.10)
       (es un proxy: el 52WeekChange es el retorno punta a punta,
        no el drawdown intra-período. El piso de -0.10 reconoce que
        incluso una acción que termina plana en 12 meses casi seguro
        tuvo un drawdown intra-período ≥ 10%. Si 52WeekChange es
        positivo, el drawdown real es desconocido — usar -0.15 como
        cota inferior conservadora.)
     → Si el payload trae `twoHundredDayAverage` y `currentPrice`
       y NO trae `52WeekChange`:
         dd_proxy = mín(0, (currentPrice - twoHundredDayAverage) /
                            twoHundredDayAverage)
         max_drawdown_12m ≈ mín(dd_proxy, -0.15)

  4. Loguear EXPLÍCITAMENTE al usuario en la sección de datos:
     "volatility_30d=0.XX (FALLBACK yfinance: derivado de beta=Y.YY ×
      σ_market 0.18; Alpha Vantage no disponible: <motivo>)"
     "max_drawdown_12m=-0.XX (FALLBACK yfinance: derivado de
      52WeekChange=-0.YY)"

  5. Aplicar bandas de cordura: si volatility_30d derivada cae fuera
     de [0.05, 1.20] o max_drawdown_12m fuera de [-0.85, 0], el proxy
     está mal calibrado para este ticker → tratar como "fallback falló"
     y pasar al paso de descarte.
```

### Si ambas fuentes fallan → descartar el ticker

```
Cuando NI Alpha Vantage NI yfinance_get_ticker_info devuelven datos
suficientes para derivar volatility_30d y max_drawdown_12m dentro de
las bandas de cordura:

  → NO inventar números.
  → NO usar TradingView `Volatility.M` como tercera fuente
    (en v9.1 se cerró esa puerta: el screener ya entregó el ticker;
     no se vuelve a ese pozo para datos de riesgo).
  → NO clasificar por "categoría" (no hay tabla a la que recurrir).

Acción única:
  → Informar al usuario:
    "No es posible calcular risk score confiable para <TICKER> en
     esta sesión (Alpha Vantage: <motivo>; yfinance: <motivo>).
     Descartado para esta recomendación."
  → Tomar el siguiente candidato del universo del screener
    (paso 0' del protocolo general) y reiniciar desde el paso 0
    (gate eToro).
  → Si tras agotar el universo del screener no quedan ≥ 3 candidatos
    operables con datos de riesgo válidos, informar al usuario y
    proponer relajar UN filtro del perfil antes de seguir.
```

El fallback de yfinance NUNCA se usa si Alpha Vantage devolvió un
número válido. El número real del mercado manda. Y el descarte NUNCA
se sustituye por una "estimación a ojo" — la opción a la derecha del
fallback es siempre "no recomendar este ticker", nunca "inventar".

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
  # Paso previo: yfinance_get_ticker_info("NOW") devolvió beta=1.32,
  #   52WeekChange=-0.15
  # Derivación: volatility_30d ≈ 1.32 × 0.18 = 0.24
  #             max_drawdown_12m ≈ mín(-0.15, -0.10) = -0.15
  calculate_risk_score(
    volatility_30d=0.24,      ← FALLBACK yfinance: beta=1.32 × σ_market 0.18 (loguear)
    max_drawdown_12m=-0.15,   ← FALLBACK yfinance: 52WeekChange=-0.15 (loguear)
    liquidity="instant",
    platform_regulated=true,
    weight_in_portfolio_pct=35,
    leverage=2.0
  )

Para un ETF S&P 500 spot, peso 20% (ej. ticker descubierto por screener
con filtros de perfil BAJO):
  calculate_risk_score(
    volatility_30d=0.12,      ← calculada en vivo si AV responde,
    max_drawdown_12m=-0.20,   ←  si no, fallback yfinance (beta×σ_market
                                  y 52WeekChange); si yfinance tampoco
                                  → DESCARTAR ticker, no inventar.
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
  - Si el activo es US (stock, ETF domiciliado en US: DIA, IWM, IVV, VTI,
    SCHD, RSP, etc.) Y paga dividendo:
       dividend_withholding_pct = 0.30

  - Si el activo es US pero NO paga dividendo (ej. growth puro o no payer
    histórico — verificar con yfinance `dividendYield` antes de asumir):
    el parámetro es irrelevante, dejar en 0.0.

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

### Ejemplo concreto (JPM long spot, 12 meses)
```
JPM: precio $215, posición $5,000, dividend_yield ~2.4% → $120 anual bruto
APY esperado 9%, vol 22%

calculate_scenarios(
  amount_usd=5000,
  expected_apy=0.09,
  volatility_annual=0.22,
  passive_income_annual_usd=120,       ← BRUTO (no neto)
  months=12,
  leverage=1.0,
  monthly_cost_usd=0.0,
  dividend_withholding_pct=0.30,       ← US → 30%
)

Resultado en escenario base:
  passive_income_gross_usd: 120
  passive_income_net_usd:    84.00     ← lo que recibe el usuario
  withholding_deducted_usd:  36.00     ← IRS lo retiene
```

### Ejemplo con CFD 2x + dividendo (KO CFD)
```
CFDs en eToro reciben dividendos equivalentes (adjustment) que también
están sujetos a retención. Combinación típica:

calculate_scenarios(
  amount_usd=500,                     ← margen
  expected_apy=0.07,
  volatility_annual=0.16,
  passive_income_annual_usd=30,       ← 3.0% sobre notional de $1,000
  months=6,
  leverage=2.0,
  monthly_cost_usd=4.50,              ← overnight fee mensual
  dividend_withholding_pct=0.30,      ← KO = US
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
> operable en este momento). Lo reemplacé por NOW, que sale del mismo
> universo del screener (perfil de riesgo y sector compatibles). NOW sí
> pasó el gate; la volatilidad real se calcula en vivo desde Alpha Vantage
> en el siguiente paso."

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

  0'. 🔭 Descubrimiento dinámico (bloqueante) — v9.2 con preset:

      a) Recoger del bloque "PRESET VERTICAL ELEGIDO" que entregó
         market_intelligence_skill.md §Paso 2:
           - preset_key, filters_base, sort_by/sort_order/markets
           - overlays_perfil_sugeridos
         (Si market_intelligence_skill no corrió, elegir preset por
          tabla resumida: ALTO→momentum_stocks, MODERADO→quality_growth_screener,
          BAJO→dividend_stocks; ejecutar tradingview.get_preset(preset_key)
          y obtener config localmente.)

      b) Componer filtros: filtros_finales = filters_base ∪ overlays_perfil

      c) Ejecutar:
         tradingview.screen_stocks(
           filters=filtros_finales,
           columns=[<lista del PASO 2 arriba>],
           sort_by=config.sort_by,
           sort_order=config.sort_order,
           limit=15-20,
           markets=config.markets
         )

      d) Aplicar diversificación sectorial (≤ 5 por sector salvo petición
         explícita del usuario).

      e) Si el screener falla: probar otro preset del mismo eje
         (ver § "Qué hacer si los presets caen / fallan"); si todos
         caen, usar filtros del perfil sin preset; si también falla,
         NO inventar lista — pedir tickers al usuario o reintentar luego.

      → resultado: lista de N candidatos brutos para esta sesión, con
        el preset_key y los filtros usados loguueados para trazabilidad.

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
         caer al fallback ÚNICO: derivar volatility_30d y
         max_drawdown_12m desde `yfinance_get_ticker_info` (campos
         `beta`, `52WeekChange`, `fiftyDayAverage`, `twoHundredDayAverage`)
         siguiendo las fórmulas del § "Fallback único: yfinance_get_ticker_info".
         LOGUEAR explícitamente al usuario qué fuente y qué fórmula se usó.
     → Si TAMBIÉN yfinance falla o el proxy cae fuera de bandas de
       cordura → DESCARTAR el ticker para esta sesión y pasar al
       siguiente del universo del screener. NO inventar números, NO
       usar TradingView Volatility.M como tercera fuente.
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
     → vol y dd vienen del paso 1 (preferente: cálculo en vivo desde
       Alpha Vantage; fallback único: derivación desde yfinance_get_ticker_info,
       con motivo logueado; si ambas fallan: ticker descartado, no se
       llega a este paso).
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
  2. Derivación por fórmula desde `yfinance_get_ticker_info`
     (`beta` × σ_market y/o `52WeekChange`), con motivo logueado al
     usuario, SOLO si Alpha Vantage falló.
Si ninguna de las dos responde con datos dentro de bandas de cordura,
DESCARTAR el ticker; no inventar un número "aproximado", no recurrir a
una categoría hardcoded (esa puerta se cerró en v9.1), no usar
TradingView Volatility.M como tercera fuente.

**Invariante universo:** ningún ticker llega al usuario sin haber pasado
por el paso 0' (descubrimiento) o haber sido pedido explícitamente por
nombre. Si el agente encuentra que está recomendando siempre los mismos
3-4 tickers sesión tras sesión, eso es señal de que el screener no se
está ejecutando realmente o los filtros son demasiado estrechos —
revisar y ampliar el perfil antes de recomendar.

## Política de ejemplos (v9.3)

**Regla de diseño:** los ejemplos didácticos de este documento (y de
`technical_skill.md`) **rotan deliberadamente** entre tickers de
sectores y perfiles distintos. Esto es intencional: si todos los
ejemplos usaran NVDA/AAPL/SPY, el modelo aprendería a tratarlos como
referencia narrativa por defecto y los traería a las recomendaciones
incluso cuando el screener devolvió otros candidatos más adecuados.

### Set rotatorio de ejemplos

Los ejemplos de tickers en este skill se eligen del siguiente set,
balanceando sectores:

| Sector              | Tickers ejemplo (rotar entre éstos)        |
|---------------------|--------------------------------------------|
| Financials          | JPM, BAC, V, GS                            |
| Consumer staples    | KO, PG, JNJ, PEP                           |
| Healthcare          | UNH, MRK, ABT, LLY                         |
| Industrials/Defense | LMT, CAT, HON, RTX                         |
| Energy              | XOM, CVX, COP                              |
| Tech (no estrella)  | MSFT, ORCL, IBM, CSCO                      |
| ETFs amplios        | DIA, IWM, IVV, SCHD, RSP                   |
| ETFs sectoriales    | XLF, XLE, XLV, XLI, XLP                    |

### Reglas de rotación

```
1. Un mismo ticker NO debe aparecer como protagonista de dos ejemplos
   consecutivos en este documento.

2. Si un ejemplo necesita un ticker concreto para ilustrar un payload
   real (ej. CRM en § "Ejemplo real" de yfinance), conservarlo —
   cambiarlo perdería realismo del payload.

3. Para ejemplos genéricos (cálculo de scenarios, ilustración de
   filtros, plantillas de respuesta), preferir un placeholder
   `<TICKER>` o un ticker del set rotatorio, NUNCA NVDA/AAPL/SPY/QQQ
   por defecto.

4. Las menciones a NVDA en los changelogs v9.0/v9.1/v9.2 se conservan
   intactas: están documentando el anti-patrón histórico, no
   sirviendo de ejemplo vivo.

5. Cuando un ejemplo necesita un ETF US que pague dividendo, preferir
   DIA, IWM, IVV o SCHD sobre SPY/QQQ/VOO. Cuando necesita un US
   stock que pague dividendo, preferir JPM, KO, JNJ, PG, XOM, LMT
   sobre los favoritos de tech.
```

### Por qué importa

Esta regla protege el invariante universo (arriba): si los ejemplos
del skill anclan al modelo en NVDA/AAPL/SPY, el agente puede terminar
"recordando" esos tickers como respaldo cuando el screener dudosamente
los devolvió. La rotación deliberada elimina ese sesgo desde la
documentación misma. Si un mantenedor agrega un nuevo ejemplo, debe
elegir un ticker del set rotatorio (o uno nuevo equivalente) — no
volver a NVDA por inercia.
