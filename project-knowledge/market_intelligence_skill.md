# Skill: Inteligencia de mercado — v2

## Cuándo se activa
Pasos 1 y 2 del orquestador. SIEMPRE. Este skill es transversal.

## Paso 1: Contexto (qué consultar)
```
MERCADO USA:
  Alpha Vantage → RSI de SPY (S&P 500) y QQQ (Nasdaq)
  TradingView → screener: top gainers, losers, sectores en momentum
  → Determinar: bull/corrección/bear

CRIPTO:
  CoinGecko → BTC precio, dominancia, cambios 24h/7d/30d
  CoinGecko → ETH, SOL precios y tendencias
  DeFiLlama → TVL total, top protocolos, yields
  → Determinar: risk-on/risk-off, BTC season/altseason

MACRO:
  → Tasas Fed: si subiendo → desfavorable para riesgo
  → Si bajando → favorable para cripto y tech
  → Inflación alta → considerar oro y BTC como cobertura
```

## Paso 2: Asimetrías (qué buscar)
```
1. SOBREVENTA: RSI < 30 + fundamentales OK → oportunidad
2. DIVERGENCIA TVL/PRECIO: TVL sube, precio flat → catch-up pendiente
3. EARNINGS PRÓXIMOS: historial de beats → posible movimiento
4. MOMENTUM IGNORADO: +10% en 7d sin cobertura masiva
5. SPREAD PLATAFORMAS: diferencia APY entre Binance y Aave
```

## Calibración por riesgo
```
RIESGO ALTO:
  Activos válidos: NVDA, TSLA, AMD, COIN, MSTR, SOL, RENDER, SUI, AVAX
  ETFs apalancados: TQQQ, SOXL
  Copy trading agresivo
  
  PROHIBIDO: VOO, VT, SCHD, QQQ sin apalancamiento
  MÁXIMO defensivo: 10%

RIESGO MODERADO:
  Válidos: QQQ, AAPL, MSFT, BTC, ETH, staking, copy conservador
  MÁXIMO defensivo: 30%

RIESGO BAJO:
  Válidos: VOO, VT, SCHD, stablecoins lending
  MÁXIMO defensivo: 60%
```

## Señales de entrada/salida
```
COMPRAR:
  RSI < 35 + soporte → sobreventa
  MACD cruce alcista + volumen → confirmación
  Precio rompe resistencia con volumen → breakout

VENDER:
  RSI > 75 + volumen decreciente → agotamiento
  Take profit parcial al +30%: vender 25% posición
  Stop loss al -20%: evaluar fundamentales
  Si fundamentales deteriorados: vender sin importar precio
```

## Narrativas de mercado (actualizar con cada consulta)
```
Identificar las 3 narrativas dominantes del momento:
  Ejemplos: "IA/GPUs", "DePIN", "RWA", "Layer 2", "Memecoins", "Bitcoin ETFs"
  
Para riesgo alto: incluir al menos 1 posición en la narrativa dominante.
```
