# Skill: Inteligencia de mercado — v4

## Qué hace este skill (y qué NO hace)

Skill **transversal** (como `risk_rules.md` o `technical_skill.md`). Aporta
el **contexto macro** y detecta **asimetrías entre verticales** que ningún
skill vertical ve por su cuenta (equity no ve TVL, defi no ve RSI del SPY).

**NO define** calibración por riesgo → la dueña es `equity_skill.md` (tabla
de volatilidades), `defi_skill.md` y los topes defensivos de
`plan_template.md` (Bajo ≤60% / Moderado ≤30% / Alto ≤10% / Extremo ≤5%).

**NO define** señales de entrada/salida → la dueña es `technical_skill.md`
(matriz de conteo bullish/bearish, Fibonacci, ATR). RSI < 30 aquí significa
"candidato a mirar", no "comprar".

## Cuándo se activa

En Fase 3 del orquestador de `system.md`, **antes** del skill vertical,
cuando el pedido es un plan nuevo o una evaluación de mercado. Se omite
en tracking_skill (Fase 7 pura de seguimiento sobre baseline existente).

## Paso 1 — Tool calls de contexto macro (únicas, transversales)

```
EJECUTAR (no inventar):
  Alpha Vantage → RSI(14) de SPY y QQQ (sobreventa/sobrecompra del mercado)
  CoinGecko → get_global → dominancia BTC + market cap total cripto
  CoinGecko → get_simple_price → BTC, ETH, SOL (24h y 7d)
  DeFiLlama → get_v2_chains + get_protocols (top 10) → TVL agregado
  TradingView → screen_stocks preset oversold → lista candidatos RSI bajo
```

Estos son los **únicos** datos que este skill pide. Cualquier dato por
ticker específico lo pide el skill vertical correspondiente.

## Paso 2 — Framework de asimetrías (5 patrones)

Con los datos del Paso 1 + los que el skill vertical ya recolectó, buscar:

```
1. SOBREVENTA MACRO + FUNDAMENTALES OK
   RSI(SPY) < 40 o RSI(QQQ) < 40 + tickers individuales con RSI < 30
   → candidatos para que equity_skill los evalúe con rigor
   (NO es señal de compra — technical_skill decide SL/TP)

2. DIVERGENCIA TVL / PRECIO (cripto)
   TVL del protocolo sube > 20% en 30d + precio token flat o bajista
   → posible catch-up pendiente, pasar a defi_skill

3. EARNINGS PRÓXIMOS < 30 DÍAS (equity)
   Si algún candidato de equity_skill tiene earningsTimestampStart
   en < 30d, marcarlo como EVENTO BINARIO (ver equity_skill)

4. MOMENTUM IGNORADO
   Activo con > 10% en 7d sin cobertura en búsquedas/tendencias
   (ratio bajo de menciones vs. movimiento de precio)

5. SPREAD APY ENTRE PLATAFORMAS (defi)
   Diferencia > 200 bps en yield del mismo activo entre protocolos
   de tier similar → oportunidad de arbitraje, pasar a defi_skill
```

## Paso 3 — Narrativas dominantes

```
Identificar 3 narrativas macro dominantes a partir de:
  - Qué sector lidera QQQ/SPY en 30d (AI, semis, energy, etc.)
  - Qué categorías de DeFiLlama ganan TVL más rápido
  - Qué términos aparecen en CoinGecko trending

Output: lista de 3 narrativas con 1 línea cada una y qué verticales las
tocan. No recomendar tickers aquí — eso es trabajo del vertical.
```

## Output de este skill al orquestador

Un bloque estructurado que el skill vertical consume:

```
CONTEXTO MACRO:
  - RSI SPY: <valor> | RSI QQQ: <valor>
  - BTC dominance: <%> | TVL total DeFi: $<valor>
ASIMETRÍAS DETECTADAS: <lista de 0-5 patrones encontrados>
NARRATIVAS DOMINANTES: <3 narrativas, 1 línea cada una>
```

Este bloque NO va al usuario directamente. Lo consume el skill vertical
para priorizar candidatos dentro de su propio universo calibrado.
