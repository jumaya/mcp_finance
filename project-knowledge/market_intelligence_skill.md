# Skill: Inteligencia de mercado — v5

> **Changelog v5:** integrados los presets de TradingView (`list_presets` /
> `get_preset`) como **fuente primaria** del descubrimiento de candidatos
> en Fase 3, antes del skill vertical. Antes los presets sólo se mencionaban
> como fallback en `equity_skill.md`; ahora son el arranque del flujo. La
> lógica de selección preset ↔ perfil vive aquí (skill transversal) para
> no duplicarla entre `equity_skill` y `defi_skill`. Se añade además el
> uso del preset `macro_assets` para el Paso 1 de contexto macro
> (sustituye llamadas ad-hoc a SPY/QQQ por un universo macro coherente).

## Qué hace este skill (y qué NO hace)

Skill **transversal** (como `risk_rules.md` o `technical_skill.md`). Aporta
el **contexto macro**, detecta **asimetrías entre verticales** que ningún
skill vertical ve por su cuenta (equity no ve TVL, defi no ve RSI del SPY),
y **selecciona el preset de TradingView** que va a sembrar el universo
de candidatos del skill vertical.

**NO define** calibración por riesgo → la dueña es `equity_skill.md` (filtros
por perfil), `defi_skill.md` y los topes defensivos de `plan_template.md`
(Bajo ≤60% / Moderado ≤30% / Alto ≤10% / Extremo ≤5%).

**NO define** señales de entrada/salida → la dueña es `technical_skill.md`
(matriz de conteo bullish/bearish, Fibonacci, ATR). RSI < 30 aquí significa
"candidato a mirar", no "comprar".

**NO ejecuta** `screen_stocks` directamente: entrega al skill vertical el
**preset elegido + overlays sugeridos** y es el vertical el que llama al
screener (mantiene la responsabilidad del universo final en su skill).

## Cuándo se activa

En Fase 3 del orquestador de `system.md`, **antes** del skill vertical,
cuando el pedido es un plan nuevo o una evaluación de mercado. Se omite
en `tracking_skill` (Fase 7 pura de seguimiento sobre baseline existente).

## Paso 1 — Tool calls de contexto macro (únicas, transversales)

```
EJECUTAR (no inventar):
  TradingView → get_preset("macro_assets") → screen_stocks con esos filtros
                → universo macro coherente (SPY, QQQ, VIX, DXY, 10Y, Gold,
                  Oil, BTC) en una sola llamada
  Alpha Vantage → RSI(14) sobre los tickers que devuelva el preset macro
                  (típicamente SPY y QQQ; el resto son índices/futuros que
                  pueden no tener RSI vía AV → usar Perf.1M del propio
                  payload del screener como proxy)
  DeFiLlama → get_v2_chains + get_protocols (top 10) → TVL agregado
```

Estos son los **únicos** datos que este skill pide. Cualquier dato por
ticker específico lo pide el skill vertical correspondiente.

> **Por qué `macro_assets` y no SPY/QQQ ad-hoc:** el preset garantiza un
> set consistente y mantenible (si TradingView lo amplía con nuevos
> activos macro, el agente los recoge automáticamente). Las llamadas
> sueltas a SPY/QQQ generaban un universo arbitrario que olvidaba VIX,
> DXY o Gold.

## Paso 2 — Selección del preset vertical (NUEVO en v5)

**Antes de devolver control al skill vertical**, este skill elige el
preset de TradingView que se va a usar como semilla del descubrimiento
de candidatos. La elección es **determinista** (tabla perfil → preset),
no subjetiva.

### Paso 2.1 — Listar presets disponibles

```
EJECUTAR (cachear durante la sesión):
  tradingview.list_presets()
```

La lista define el menú real disponible. No asumas que un preset existe
sin verificarlo aquí — los nombres de preset pueden cambiar entre versiones
del MCP server. Si un preset esperado por la tabla de abajo NO aparece en
`list_presets()`, caer al fallback documentado al final de esta sección.

### Paso 2.2 — Mapeo perfil → preset (equity)

La elección depende de **tres** señales del usuario, en este orden de
prioridad:

  1. **Sesgo declarado en la sesión** ("quiero dividendos", "quiero
     momentum", "deep value", "buy and hold tipo Buffett") — gana sobre
     todo lo demás.
  2. **Objetivo del usuario** (ingresos pasivos / crecimiento / mixto)
     — declarado en Fase 1 del orquestador.
  3. **Perfil de riesgo** (conservador / moderado / agresivo) — declarado
     en Fase 1.

Tabla de mapeo (claves de preset validadas contra `list_presets()`):

```
SI sesgo declarado:
  "dividendos" / "ingresos pasivos en acciones"   → "dividend_stocks"
  "dividendos crecientes" / "compounding income"  → "dividend_growth"
  "value" / "barato" / "P/E bajo"                 → "value_stocks"
  "deep value" / "contrarian"                     → "deep_value"
  "momentum" / "lo que sube"                      → "momentum_stocks"
  "breakout" / "rompimiento" / "52W highs"        → "breakout_scanner"
  "growth" / "crecimiento"                        → "growth_stocks"
  "calidad" / "Buffett" / "Munger" / "moat"       → "quality_compounder"
  "GARP" / "growth a precio razonable"            → "garp"
  "earnings" / "buenos resultados"                → "earnings_momentum"

SI no hay sesgo declarado, usar perfil + objetivo:
  PERFIL ALTO + objetivo crecimiento     → "momentum_stocks"
  PERFIL ALTO + objetivo mixto           → "growth_stocks"
  PERFIL MODERADO + objetivo crecimiento → "quality_growth_screener"
  PERFIL MODERADO + objetivo mixto       → "garp"
  PERFIL MODERADO + ingresos pasivos     → "dividend_growth"
  PERFIL BAJO + ingresos pasivos         → "dividend_stocks"
  PERFIL BAJO + objetivo crecimiento     → "quality_stocks"
  PERFIL BAJO + objetivo mixto           → "quality_stocks"
```

Si la tabla no cubre una combinación específica, el default es el preset
**más conservador del eje del perfil**:

```
Default por perfil (fallback de la tabla):
  ALTO     → "momentum_stocks"
  MODERADO → "quality_growth_screener"
  BAJO     → "quality_stocks"
```

### Paso 2.3 — Crypto: los presets de TV NO aplican

Los 14 presets actuales de TradingView (`quality_stocks`, `momentum_stocks`,
`dividend_stocks`, etc.) son **todos de equity US**. Para `defi_skill.md`
no hay preset directamente reutilizable.

Decisión documentada: para crypto, este skill **no entrega un preset
vertical**. El skill `defi_skill.md` mantiene su descubrimiento por
filtros directos sobre `screen_crypto` (perfil cripto conservador /
moderado / agresivo). Los únicos presets que tocan crypto son
`macro_assets` (BTC como activo macro, ya cubierto en Paso 1) y
`market_indexes` (no aplica al universo cripto).

Si en el futuro TradingView publica presets crypto-específicos,
extender la tabla del Paso 2.2 con un bloque `MAPEO PERFIL → PRESET (crypto)`.

### Paso 2.4 — Recuperar el preset elegido

```
EJECUTAR (1 llamada):
  config = tradingview.get_preset(preset_key)
```

El payload incluye `filters`, `sort_by`, `sort_order`, `markets`. Estos
campos **se pasan tal cual al vertical** como punto de partida del
screener. El vertical decide si:
  - Los usa como están (vertical "ligero" — confía en el preset).
  - Les añade overlays del perfil (vertical "estricto" — combina ambos).

### Paso 2.5 — Overlays del perfil (sugerencia al vertical)

Para que el preset no devuelva un universo demasiado amplio o desalineado
con el perfil del usuario, este skill sugiere overlays mínimos que el
vertical puede anexar a `config.filters`:

```
PERFIL ALTO (sobre cualquier preset):
  + market_cap_basic        > 10_000_000_000   (evita micro-caps)
  + average_volume_30d_calc > 5_000_000        (liquidez para CFD)
  + typespecs has ["common"]                   (sin warrants/ADRs raros)

PERFIL MODERADO (sobre cualquier preset):
  + market_cap_basic        > 50_000_000_000   (blue-chip)
  + average_volume_30d_calc > 3_000_000

PERFIL BAJO (sobre cualquier preset):
  + market_cap_basic        > 20_000_000_000
  + beta_1_year             < 1.2              (suaviza vol del preset)
```

Regla: los overlays **se añaden** a los filtros del preset (intersección),
no los reemplazan. Si la combinación devuelve < 5 candidatos, el vertical
relaja overlays primero (un filtro a la vez), no los del preset.

### Paso 2.6 — Si `list_presets` o `get_preset` fallan

Fallback documentado, en este orden:

  1. **Reintento con preset alternativo del mismo eje** (ej. si
     `momentum_stocks` no responde → `growth_stocks` para perfil ALTO).
  2. **Saltar a filtros directos del perfil** documentados en
     `equity_skill.md §"Perfiles por características"`. El vertical
     opera entonces sin preset, con su propia matriz de filtros (que
     era el flujo v9.1 anterior). Loguear al usuario que el preset no
     respondió y que se usaron filtros del perfil.
  3. **Nunca** caer a una lista hardcoded de tickers.

## Paso 3 — Framework de asimetrías (5 patrones)

Con los datos del Paso 1 + los que el skill vertical ya recolectó, buscar:

```
1. SOBREVENTA MACRO + FUNDAMENTALES OK
   RSI(SPY) < 40 o RSI(QQQ) < 40 + tickers individuales con RSI < 30
   → candidatos para que equity_skill los evalúe con rigor
   (NO es señal de compra — technical_skill decide SL/TP)
   Implicación para preset: si SPY está en sobreventa, considerar
   añadir "deep_value" al menú propuesto al vertical incluso si el
   perfil base sugería "momentum_stocks".

2. DIVERGENCIA TVL / PRECIO (cripto)
   TVL del protocolo sube > 20% en 30d + precio token flat o bajista
   → posible catch-up pendiente, pasar a defi_skill

3. EARNINGS PRÓXIMOS < 30 DÍAS (equity)
   Si algún candidato de equity_skill tiene earningsTimestampStart
   en < 30d, marcarlo como EVENTO BINARIO (ver equity_skill)

4. MOMENTUM IGNORADO
   Activo con > 10% en 7d sin cobertura en búsquedas/tendencias
   (ratio bajo de menciones vs. movimiento de precio)
   Implicación para preset: confirma "momentum_stocks" o
   "breakout_scanner" como preset apropiado.

5. SPREAD APY ENTRE PLATAFORMAS (defi)
   Diferencia > 200 bps en yield del mismo activo entre protocolos
   de tier similar → oportunidad de arbitraje, pasar a defi_skill
```

## Paso 4 — Narrativas dominantes

```
Identificar 3 narrativas macro dominantes a partir de:
  - Qué sector lidera QQQ/SPY en 30d (AI, semis, energy, etc.)
  - Qué categorías de DeFiLlama ganan TVL más rápido
  - Qué activos del preset macro_assets están en máximos (gold,
    oil, BTC) o mínimos (DXY, 10Y) — son señales de régimen.

Output: lista de 3 narrativas con 1 línea cada una y qué verticales las
tocan. No recomendar tickers aquí — eso es trabajo del vertical.
```

## Output de este skill al orquestador

Un bloque estructurado que el skill vertical consume:

```
CONTEXTO MACRO:
  - RSI SPY: <valor> | RSI QQQ: <valor>
  - VIX: <valor> | DXY: <valor> | 10Y: <valor>%
  - Gold: <Perf.1M>% | Oil: <Perf.1M>% | BTC: <Perf.1M>%
  - BTC dominance: <%> | TVL total DeFi: $<valor>

PRESET VERTICAL ELEGIDO (equity):
  - preset_key: <key>                  (ej. "quality_growth_screener")
  - preset_name: <nombre>              (ej. "Quality Growth Screener")
  - razón_elección: <perfil + objetivo + sesgo declarado, en una línea>
  - filters_base: <array de filters del preset>
  - overlays_perfil_sugeridos: <array de filters adicionales por perfil>
  - sort_by / sort_order / markets: <del preset, salvo override>

ASIMETRÍAS DETECTADAS: <lista de 0-5 patrones encontrados>

NARRATIVAS DOMINANTES: <3 narrativas, 1 línea cada una>
```

Este bloque NO va al usuario directamente. Lo consume el skill vertical
para llamar a `screen_stocks` con `filters = filters_base + overlays_perfil_sugeridos`
(ver `equity_skill.md §"Descubrimiento dinámico de candidatos"` para el
flujo concreto).

> **Trazabilidad:** en el plan final que ve el usuario, `equity_skill`
> debe mencionar qué preset se usó (ej. "candidatos descubiertos vía
> preset 'quality_growth_screener' de TradingView + overlays de perfil
> moderado: mcap > $50B, volumen > 3M/día"). Esto cumple el principio
> #1 de `system.md` (transparencia de origen de datos) y permite al
> usuario auditar el universo si pregunta "¿por qué estos tickers y no
> otros?".
