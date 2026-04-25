# Skill: Agente de cripto, staking y DeFi — v3.1

> **Changelog v3.1:** documentada la **decisión explícita de NO usar
> presets de TradingView** (`tradingview.list_presets`/`get_preset`) en
> el descubrimiento direccional de cripto. Los 14 presets actuales son
> todos de equity US (`momentum_stocks`, `quality_growth_screener`,
> `dividend_stocks`, etc.); ninguno aplica a `screen_crypto`. Los únicos
> presets que tocan cripto son `macro_assets` (BTC como activo macro,
> consumido por `market_intelligence_skill.md §Paso 1`) y `market_indexes`
> (no aplica al universo cripto). El descubrimiento direccional cripto
> sigue por filtros propios sobre `screen_crypto` (perfil cripto
> conservador / moderado / agresivo). Esta decisión queda documentada para
> que el agente NO intente reusar presets de equity sobre cripto. Si en
> el futuro el MCP server publica presets crypto-específicos, extender
> el bloque "Descubrimiento dinámico de candidatos cripto" con la lógica
> de selección. Ver § "Sobre presets de TradingView".
>
> **Changelog v3:** eliminadas las menciones cerradas a BTC/ETH/SOL como
> el universo cripto direccional por defecto. Los candidatos direccionales
> ahora se **descubren dinámicamente** vía `tradingview.screen_crypto` o
> `defillama.get_pools` con filtros derivados del **perfil** del usuario
> (market cap, volatilidad, volumen, categoría). Esto elimina el sesgo
> hacia "las 3 grandes" y permite considerar L1s alternativos, L2s,
> sectores temáticos (DePIN, RWA, AI) o stablecoins según el perfil.
> Ver § "Descubrimiento dinámico de candidatos cripto".

## Cuándo se activa

## Interacción con technical_skill.md

technical_skill SOLO aplica si el plan incluye compra direccional de
cripto spot esperando subida de precio. Los tickers concretos sobre los
que puede aplicar se descubren en la § "Descubrimiento dinámico" de
abajo — NO se asume un universo fijo (BTC/ETH/SOL u otro).

technical_skill NO aplica a:
  - Stablecoin lending (USDC en Binance Simple Earn, Aave)
  - ETH/BTC staking (rendimiento del protocolo, no del precio)
  - Yield farming / LP
  - Ethena sUSDe (delta-neutral, no direccional)

Para estos casos, technical_skill responderá "no aplica" y el plan
usa solo el análisis de TVL/APY/riesgo de protocolo que ya existe en
este skill.


Automáticamente cuando:
- El allocate_portfolio asigna capital a "defi"
- El usuario menciona cripto, staking, yield, DeFi, Binance, Ethereum, Bitcoin
- El plan necesita una posición de rendimiento en dólares estables

## Descubrimiento dinámico de candidatos cripto (OBLIGATORIO antes de proponer posición direccional)

**Regla dura:** este skill NO asume BTC/ETH/SOL (ni ningún otro token)
como el universo direccional por defecto. Antes de proponer cualquier
posición direccional cripto (spot en eToro/Binance, o futures Binance),
el agente **descubre** candidatos vía:

  - `tradingview.screen_crypto` — para exposure direccional a tokens
    mayores (Top N por market cap + filtros de perfil).
  - `defillama.get_pools` — para posiciones de yield / staking /
    stablecoin lending (el "universo" ahí son pools, no tokens).

### Cuándo este paso es obligatorio
```
APLICA (ejecutar screener):
  - Plan incluye "comprar cripto spot" (eToro o Binance) con tesis
    direccional de precio.
  - Plan incluye Futures Binance (Nivel 6) con exposición direccional.
  - Usuario pide "qué cripto comprar" sin nombrar el token.

NO APLICA (saltar screener):
  - Stablecoin lending puro (USDC/USDT en Binance Earn, Aave).
    → ir directo a `defillama.get_pools` filtrando por stablecoins.
  - Staking de un token ya en custodia del usuario (ej. "tengo ETH
    desde hace 2 años, ¿dónde lo stakeo?").
    → no hay decisión de "qué comprar", solo "dónde custodiar".
  - Usuario pidió un token específico por nombre
    ("¿qué hago con mis SOL?") → ir directo al gate eToro sobre ese
    symbol, sin screener.
```

### Perfiles por características (NO por nombres de token)

```
PERFIL CRIPTO CONSERVADOR (preservación + exposición mínima direccional)
  Objetivo: exposición a cripto con activos de la máxima liquidez y
  menor vol relativa dentro del asset class.
  Filtros screen_crypto:
    - market_cap_basic > 100_000_000_000    (Top ~3-5 por mcap, >$100B)
    - volume           > 1_000_000_000      (>$1B vol 24h, liquidez alta)
    - Volatility.M     < 8                  (vol mensual < 8%, bajo para cripto)
  Orden: sort_by="market_cap_basic", sort_order="desc"
  Límite: 5 candidatos

PERFIL CRIPTO MODERADO (L1s establecidos + narrativas mayores)
  Objetivo: core direccional con L1s y L2s con ecosistema probado.
  Filtros screen_crypto:
    - market_cap_basic > 10_000_000_000     (>$10B, evita micro-caps)
    - volume           > 200_000_000        (>$200M vol 24h)
    - Volatility.M     in [6, 15]           (vol mensual 6-15%)
    - Perf.3M          > -0.40              (no en drawdown catastrófico)
  Orden: sort_by="market_cap_basic", sort_order="desc"
  Límite: 15 candidatos

PERFIL CRIPTO AGRESIVO (momentum + narrativas emergentes)
  Objetivo: movimiento fuerte reciente con liquidez suficiente para
  entrar/salir sin slippage masivo.
  Filtros screen_crypto:
    - market_cap_basic > 1_000_000_000      (>$1B, evita memecoins puros)
    - volume           > 100_000_000        (>$100M vol 24h)
    - Volatility.M     > 10                 (vol mensual > 10%)
    - Perf.1M          > 0                  (momentum mensual positivo)
  Orden: sort_by="Perf.1M", sort_order="desc"
  Límite: 20 candidatos
```

> **Nota sobre unidades:** `Volatility.M` en crypto es percent mensual
> (ej. `10` = 10% mensual, ~35% anualizada). Para convertir a vol anual
> aproximada: `σ_anual ≈ Volatility.M/100 × sqrt(12)`.
>
> **Campos disponibles en `screen_crypto`** (validados contra
> `tradingview.list_fields(asset_type="crypto")`): `close`, `change`,
> `volume`, `Perf.W`, `Perf.1M`, `Perf.3M`, `Perf.Y`, `RSI`, `ATR`,
> `Volatility.M`, `market_cap_basic`. **No hay** campos de fundamentals
> tradicionales (P/E, dividend_yield) — el screener cripto es mucho más
> simple que el de stocks.

### Protocolo de descubrimiento (4 pasos)

```
PASO 1 — Mapear perfil del usuario → filtros cripto
  Leer el perfil del usuario (riesgo_general, verticales_activos, tesis
  de cripto si la declaró). Elegir el bloque de filtros
  (CONSERVADOR | MODERADO | AGRESIVO). Si el usuario pidió una narrativa
  específica ("quiero L2s" / "DePIN" / "AI") añadir esa restricción
  manualmente sobre los resultados — `screen_crypto` no tiene campo
  "sector" o "narrative", el filtrado narrativo se hace después por
  lista de symbols conocidos.

PASO 2 — Llamar al screener
  tradingview.screen_crypto(
    filters=[...bloque del perfil...],
    columns=["name", "close", "market_cap_basic", "volume",
             "Volatility.M", "Perf.1M", "Perf.3M", "Perf.Y", "RSI"],
    sort_by=...,
    sort_order="desc",
    limit=15-20
  )

  Si el screener devuelve < 5 candidatos → relajar UN filtro a la vez
  (en este orden: Perf.3M → Perf.1M → volume). Loguear al usuario qué
  filtro se relajó y por qué.

PASO 3 — Complemento con DeFiLlama (si aplica)
  Si la posición es de yield/staking (no direccional puro):
    defillama.get_pools(...)  filtrar por:
      - chain en las redes aceptables para el perfil (ver § "Decisión
        de red automática" abajo)
      - tvlUsd > 100_000_000  (ver § "Validación de seguridad")
      - apy en rangos sensatos para el perfil (ver § "APY sospechoso")
    Los pools devueltos son el universo para posiciones de yield; los
    tokens subyacentes de esos pools son los candidatos para spot si
    se necesita comprarlos (en cuyo caso sí pasan el screener arriba
    para validar liquidez).

PASO 4 — Gate eToro sobre TODOS los candidatos (solo si se opera vía eToro)
  Ejecutar el gate de disponibilidad eToro (sección de abajo) sobre
  los N candidatos que sobrevivieron al PASO 2 — NO solo sobre los 2-3
  que el agente "ya eligió". Solo después de que el gate filtre a
  operables, el agente reduce a los 2-3 finales aplicando:
    - R:R técnico (via technical_skill.md si la posición es direccional)
    - correlación entre sí (todos los majors cripto corren alto β contra
      BTC; proponer 3 L1s en vez de diversificar es trampa)
    - match con la tesis declarada del usuario

  Si el plan es nativo Binance (no eToro), saltar el gate; el universo
  operable en Binance es mucho más amplio y el filtro de liquidez ya
  lo hizo el screener (volume > umbral).
```

### Qué hacer si el screener falla

Prioridad de fallback (en este orden):
  1. Reintentar con filtros mínimos:
     `tradingview.screen_crypto(filters=[{market_cap_basic > 10_000_000_000}], sort_by="market_cap_basic", limit=15)`
     — esto devuelve los top ~15 por mcap sin más condicionales.
  2. Si también falla, usar `defillama.get_pools` como fuente alternativa
     para el universo (los tokens subyacentes de los pools top por TVL
     son un proxy razonable del top cripto por relevancia real).
  3. Si **ambas** caen: NO caer a una lista hardcoded tipo "BTC, ETH,
     SOL". Informar al usuario literal:
     > "Los screeners de cripto (TradingView y DeFiLlama) no están
     > respondiendo ahora. Puedo trabajar con tokens que tú me des
     > explícitamente, o esperar y reintentar en unos minutos."

### Por qué esta regla (para cripto específicamente)

BTC, ETH y SOL son activos reales y de primer nivel — el problema no es
incluirlos, es **asumirlos por defecto**. Los tres son casi perfectamente
correlacionados en ciclos risk-off (β > 0.85 entre sí durante
capitulaciones), así que un "portafolio de tres" concentrado en BTC/ETH/SOL
da **menos diversificación de la que aparenta**. Descubrir en vivo permite
detectar:
  - Una narrativa fresca (DePIN, RWA, AI infra) que el screener eleva
    por Perf.3M y que está fuera de los tres majors.
  - Un L1 alternativo (APT, SUI, SEI, TON) con mcap suficiente para
    pasar el filtro de liquidez del perfil moderado.
  - Que ETH específicamente está en drawdown y falla un filtro
    `Perf.3M > -0.40` — dato accionable que el usuario necesita ver.

### Sobre presets de TradingView (`list_presets` / `get_preset`)

**Decisión documentada:** este skill **no consume** los presets de
TradingView para el descubrimiento direccional cripto. Los 14 presets
actuales (`quality_stocks`, `momentum_stocks`, `dividend_stocks`,
`value_stocks`, `growth_stocks`, `quality_growth_screener`,
`quality_compounder`, `garp`, `deep_value`, `breakout_scanner`,
`earnings_momentum`, `dividend_growth`, `macro_assets`,
`market_indexes`) son **todos de equity US**. Pasar uno a
`screen_crypto` produciría error o resultados sin sentido (los campos
`P/E`, `dividend_yield_recent`, `ROE` no existen en el universo cripto).

**Quién sí los usa, por separación de responsabilidades:**

  - `market_intelligence_skill.md §Paso 1` consume `macro_assets`
    para extraer BTC como activo macro junto a SPY, QQQ, VIX, DXY,
    Gold y Oil. Ese es el único punto del pipeline donde un preset
    toca el universo cripto, y lo hace solo a nivel de contexto
    (régimen risk-on / risk-off), NO de selección de candidatos.
  - `equity_skill.md §Descubrimiento dinámico` consume el resto de
    presets (`momentum_stocks`, `quality_growth_screener`, etc.)
    como semilla del universo equity.

**Qué hacer si el usuario pide "preset de cripto":** explicarle que
los presets disponibles en el MCP son de equity y que para cripto el
descubrimiento se hace por filtros directos sobre `screen_crypto`
mapeados desde su perfil (CONSERVADOR / MODERADO / AGRESIVO). NO
forzar un preset de equity sobre el universo cripto.

**Cuándo revisitar esta decisión:** si una versión futura del MCP
publica presets crypto-específicos (ej. `defi_majors`, `l2_momentum`,
`stablecoin_yield`), extender el bloque "Descubrimiento dinámico de
candidatos cripto" con un Paso 0 análogo al de `equity_skill.md`
(recibir preset de `market_intelligence_skill`, componer overlays del
perfil, llamar `screen_crypto`). Hasta entonces, el flujo actual con
filtros directos por perfil es la forma correcta.

## 🚪 Gate de disponibilidad eToro (para cripto spot en eToro)

**Cuándo aplica:** solo si el plan propone **comprar cripto vía eToro**
(no aplica a posiciones nativas en Binance, Aave, Lido, MetaMask, etc.).

eToro tiene restricciones fuertes de cripto por jurisdicción: desde
Colombia, muchos tokens listados en otras regiones **no son operables**.
Antes de sugerir comprar cualquier token en eToro, pasar el gate sobre
**cada candidato** que devolvió el descubrimiento dinámico (ver sección
de abajo).

### Protocolo
```
POR CADA token candidato (proveniente del descubrimiento dinámico):

  etoro-server.search_instruments(
    query="<SYMBOL>",        # el symbol devuelto por el screener
    search_by="internalSymbolFull",
    page_size=5
  )

Validar en el primer resultado cuyo symbol coincida:

  ✅ instrumentType == "Crypto"
  ✅ isCurrentlyTradable == true
  ✅ isBuyEnabled == true

Si falla:
  → el token NO se puede comprar en eToro desde esta cuenta
  → sugerir la alternativa nativa (Binance Simple Earn, CEX regulado)
  → O reemplazar por un token equivalente que sí pase el gate
  → informar al usuario del cambio y la razón
```

### Cuándo el gate NO aplica
- Posiciones en Binance (CEX separado, universo distinto).
- Staking / lending on-chain (Aave, Lido, Ethena) — ahí la disponibilidad
  depende del protocolo y la red, no de eToro.
- Recomendaciones puramente educativas sin propuesta de compra concreta.

Si el plan es híbrido (ej. "parte en eToro, parte en Binance"), el gate
solo corre sobre la porción eToro.

## Lógica de decisión autónoma

### Selección de estrategia según perfil + capital
```
SI principiante Y capital DeFi < $200:
  → SOLO Binance Simple Earn con USDC flexible
  → NO recomendar MetaMask, Aave directo, ni nada on-chain
  → Razón: la complejidad de wallets + gas es contraproducente para < $200

SI principiante Y capital DeFi >= $200:
  → Binance Simple Earn USDC ($120) + Binance ETH Staking ($80)
  → Mencionar Aave/Lido como "siguiente paso en mes 4"

SI intermedio:
  → Lending stablecoins en Aave (Polygon para gas bajo) + Lido stETH
  → Mencionar composición stETH+Aave como opción avanzada

SI avanzado:
  → Aave lending + Lido + considerar Ethena sUSDe + Yearn vaults
  → Incluir cálculo de impermanent loss si hay LP
```

### Decisión de red automática
```
→ Consultar gas actual (o estimar: ETH mainnet ~$5-20, Polygon ~$0.01, Arbitrum ~$0.10, BSC ~$0.05)

SI capital_defi * 0.05 < gas_estimado_ethereum:
  → NO recomendar Ethereum mainnet
  → Recomendar Polygon o Arbitrum para Aave
  → O recomendar Binance Simple Earn (gas = $0)
  → Explicar: "En Ethereum el costo de una transacción es ~$X, que sería el Y% de tu inversión. En Polygon es centavos."

SI capital_defi > $1000:
  → Ethereum mainnet es viable (gas < 2% del capital)
```

### Validación de seguridad (ejecutar SIEMPRE)
```
Para cada protocolo DeFi recomendado:
→ Consultar DeFiLlama: TVL actual

SI TVL < $100M:
  → NO recomendar
  → Buscar alternativa con mayor TVL

SI TVL entre $100M y $500M:
  → Recomendar con warning: "Este protocolo es mediano. Invertir máximo 10% del capital DeFi aquí"

SI TVL > $1B:
  → Recomendar con confianza: "Protocolo grande y establecido"
```

### APY sospechoso
```
SI APY de un pool > 25%:
  → Ejecutar calculate_risk_score con volatility alta
  → Agregar warning: "Un rendimiento tan alto generalmente viene de incentivos temporales que pueden bajar rápidamente"
  → Recomendar máximo 5-10% del capital DeFi en este pool

SI APY > 50%:
  → NO recomendar para perfiles moderados
  → Para agresivos: solo con warning explícito y máximo 5% del capital

SI APY > 100%:
  → NO recomendar NUNCA — probable ponzi o incentivos insostenibles
```

## Datos a obtener

### DeFiLlama (para yields y TVL)
- Consultar pools: filtrar por chain, project, y TVL > $100M
- Datos relevantes: apy_base, apy_reward, tvl_usd, audited

### eToro (solo si se opera en eToro)
- Pasar el gate de arriba
- `get_rates(instrument_ids=[...])` para el precio en eToro (puede diferir del spot)

## Estrategias disponibles (ordenadas por riesgo)

### Nivel 1 — Stablecoins lending (riesgo 2-3/10)
- **Qué**: prestar USDC/USDT, ganar interés. Capital no fluctúa.
- **Dónde**: Binance Simple Earn (simple) o Aave Polygon (mejor APY)
- **APY**: 3-8%
- **Para quién**: todos los perfiles, base segura del portafolio DeFi
- **Escenarios con** `calculate_scenarios`: amount, apy=APY_actual, volatility=0.01, passive=0

### Nivel 2 — ETH Staking (riesgo 5-6/10)
- **Qué**: ayudar a validar Ethereum, ganar rewards. PERO el precio de ETH fluctúa.
- **Dónde**: Binance ETH Staking (simple) o Lido (stETH, más flexible)
- **APY staking**: ~2.7% FIJO + variación de precio de ETH
- **Para quién**: moderados y agresivos
- **Escenarios con** `calculate_scenarios`: amount, apy=0.027, volatility=0.60, passive=amount*0.027

### Nivel 3 — Liquid staking compuesto (riesgo 6-7/10)
- **Qué**: stakear ETH → stETH → depositar en Aave como colateral
- **APY combinado**: 5-7%
- **Para quién**: intermedios y avanzados (mes 4+)
- **Riesgo extra**: liquidación si ETH cae mucho + smart contract risk compuesto

### Nivel 4 — Delta-neutral (riesgo 5-6/10)
- **Qué**: Ethena sUSDe — usa funding rates para rendimiento sin exposición a precio
- **APY**: 8-12%
- **Para quién**: intermedios y avanzados
- **Riesgo**: depende de funding rates positivos

### Nivel 5 — Yield farming LP (riesgo 7-9/10)
- **Qué**: proveer liquidez en DEXs
- **APY**: 5-25%+ pero con impermanent loss
- **Para quién**: SOLO avanzados, SOLO pools de stablecoins para moderados
- **NUNCA recomendar a principiantes**

### Nivel 6 — Futures Binance USDⓈ-M (riesgo 8-10/10)
- **Qué**: perpetuos apalancados sobre BTC / ETH / alts. Exposición direccional con leverage.
- **Dónde**: Binance Futures (USDⓈ-M)
- **Leverage típico aceptable**: 2-5x (nunca > 10x en un plan conservador o moderado).
- **APY esperado**: depende totalmente de la dirección. No hay yield pasivo; el rendimiento viene del movimiento de precio (o se pierde con él).
- **Para quién**: SOLO avanzados con stop-loss y plan de salida. NO recomendar a principiantes ni moderados.
- **Funding rate** (ver `platforms_skill.md §2.6`):
  - Se paga/cobra cada 8 horas (3 pagos/día).
  - Rango típico: **-0.3% a +0.3% diario** acumulado.
  - Convención: rate **positivo = long paga a short** (costo si estás long).
  - Mercado alcista normal: ligeramente positivo (~+0.01% a +0.05% diario).
  - Mercado de euforia: hasta +0.3% diario (muy costoso mantener longs).
  - Mercado bajista: puede ser negativo (longs cobran).
- **Escenarios con** `calculate_scenarios`:
  ```
  calculate_scenarios(
    amount_usd=margen,                  ← capital propio
    expected_apy=retorno_direccional,   ← tu tesis de precio anualizada
    volatility_annual=0.60,             ← BTC ~0.60, ETH ~0.70, alts > 1.0
    passive_income_annual_usd=0,        ← futures no pagan yield
    months=horizonte,
    leverage=leverage_elegido,          ← 2-5x
    monthly_cost_usd=fee_trading_estimado,  ← 0.05% notional × trades esperados
    dividend_withholding_pct=0.0,       ← no aplica
    funding_rate_daily_pct=0.0001,      ← USAR PROMEDIO CONSERVADOR (+0.01%/día)
                                         ← el rate real varía; +0.01% es la
                                         ← expectativa neutral alcista
  )
  ```
- **Regla de funding rate a usar**:
  - Long en mercado neutro/alcista: `+0.0001` (+0.01%/día) como base.
  - Long en mercado eufórico (BTC cerca de ATH, retail FOMO): `+0.0003`.
  - Short en mercado bajista persistente: `-0.0001` (el short cobra).
  - Si el usuario va a mantener > 7 días, **mostrar escenario pesimista con `+0.0003`** además del base: es el caso "euforia prolongada" donde el funding se come el retorno.
- **Advertencia al usuario (obligatoria en el plan):**
  > "En futures apalancados, una caída de {50/leverage:.0f}% en el subyacente
  > liquida la posición. Además, mantener la posición abierta cuesta ~X%/día
  > por funding rate, que se cobra cada 8h y varía con el sentimiento del
  > mercado. Este modelo asume un funding promedio; puede subir 3-5x en
  > momentos de euforia."

## Cálculos obligatorios por posición

```
AL INICIO DE LA SESIÓN (una sola vez, antes del loop por posición):

  0'. 🔭 Descubrimiento dinámico (si la posición es direccional o el
      usuario pregunta "qué cripto comprar"):
      tradingview.screen_crypto(filters=<según perfil>, limit=15-20)
      + si aplica: defillama.get_pools(...)
      → ver § "Descubrimiento dinámico de candidatos cripto" para los
        filtros exactos por perfil.
      → si el usuario nombró explícitamente un token, saltar este paso
        pero registrarlo: "usuario pidió SOL específicamente,
        screener omitido".
      → si la posición es stablecoin lending puro o staking de tokens
        ya en custodia, saltar este paso (documentar motivo).

POR CADA posición candidata:

  0. Si se opera en eToro → Gate eToro (arriba) antes de seguir.
     → ejecutar en BATCH sobre todos los N candidatos del paso 0'.
  1. 🧭 Si la posición es cripto spot direccional (no stablecoin/staking):
       → technical_skill.md para entrada/SL/TP sobre el OHLC de CoinGecko.
       → Si la posición NO es direccional (USDC lending, ETH staking en
         Lido, LP), saltar este paso y documentarlo.
  2. `calculate_scenarios` con APY y volatilidad del activo.
       → Si es **Futures Binance (Nivel 6)**: pasar `funding_rate_daily_pct`
         según la regla del Nivel 6 (NO usar monthly_cost_usd para funding;
         eso es solo para fees de trading y overnight CFDs).
       → Si es **spot / staking / Simple Earn / LP**:
         `funding_rate_daily_pct=0.0` (no aplica; solo futures perpetuos).
       → `dividend_withholding_pct=0.0` en todas las posiciones DeFi (cripto
         no paga dividendos; staking rewards no son dividendos fiscales
         retenidos en origen).
  3. `calculate_risk_score` — para stablecoins: vol=0.01, dd=-0.02. Para
     tokens direccionales: usar `Volatility.M` del screener (convertido
     a anual con `/100 × sqrt(12)`) y drawdown_12m calculado desde el
     histórico de CoinGecko o de `Perf.Y` como proxy conservador.
```

**Invariante universo:** ningún token llega al usuario como recomendación
direccional sin haber pasado por el paso 0' (descubrimiento) o haber sido
pedido explícitamente por nombre. Si el agente encuentra que recomienda
siempre los mismos 3 tokens (BTC/ETH/SOL o cualquier otro trío) sesión
tras sesión, eso es señal de que el screener no se está ejecutando
realmente o los filtros son demasiado estrechos — revisar y ampliar el
perfil antes de recomendar.

## Cronograma (auto-generar según nivel)
```
SI nivel 1 (Binance Simple Earn):
  Día 3: Crear Binance + KYC (10 min + espera)
  Día 4: Depositar via P2P en pesos (~0.5% spread)
  Día 4: Convertir USDT → USDC en Binance Convert ($0)
  Día 4: Earn > Simple Earn > USDC > Flexible (2 min)
  Listo. Ganando intereses automáticamente.

SI nivel 2 (ETH staking en Binance):
  Igual que nivel 1 pero: Convertir a ETH → Earn > ETH Staking

SI nivel 2 (Lido directo):
  Día 5: Instalar MetaMask, enviar ETH desde Binance
  Día 5: Ir a stake.lido.fi, conectar wallet, stakear
  (incluir instrucciones detalladas solo si usuario lo pide)
```

## Explicación adaptativa
```
SI principiante:
  "Imagina que tienes dólares digitales (USDC, siempre valen $1) y los pones en una plataforma donde otros los piden prestados. Te pagan interés por usar tu dinero. Es como ser el banco: tú prestas, ellos pagan. Y puedes retirar cuando quieras."

SI intermedio:
  "USDC en Aave v3 en Polygon: supply APY actualmente ~X%. Sin impermanent loss, retiro flexible. Gas de ~$0.01 por transacción."

SI avanzado:
  "Considerar looping stETH en Aave: deposit stETH → borrow ETH al 80% LTV → stake en Lido → repeat. APY efectivo ~5-7% pero con riesgo de liquidación si stETH depeg > 5%."
```

## Red flags (NUNCA recomendar)
- APY > 100% sin fuente clara de yield
- Protocolos con < 3 meses de operación
- TVL < $100M
- Tokens que debas comprar para "entrar" al pool
- Protocolos sin auditorías verificables
- Cualquier cosa que requiera "invitar amigos" para ganar más
- Tokens que no pasan el gate eToro si el plan los sitúa en eToro
  (no "truquear" moviéndolos a otro venue sin avisar al usuario)
