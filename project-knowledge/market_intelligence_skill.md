# Skill: Inteligencia de mercado — v3

## Activación
Pasos 1 y 2 del orquestador. SIEMPRE.

## Paso 1: Tool calls de contexto
```
EJECUTAR (no inventar):
  Alpha Vantage → RSI de SPY, RSI de QQQ
  CoinGecko → BTC precio + dominancia + cambios
  CoinGecko → ETH, SOL precios + cambios
  DeFiLlama → TVL total + top protocolos
  TradingView → screener acciones RSI < 30
```

## Paso 2: Framework de asimetrías
```
Buscar con los datos obtenidos:
  1. SOBREVENTA: RSI < 30 + fundamentales OK
  2. DIVERGENCIA TVL/PRECIO: TVL sube, precio flat → catch-up pendiente
  3. EARNINGS PRÓXIMOS: Yahoo Finance → historial de beats
  4. MOMENTUM IGNORADO: >10% 7d sin cobertura masiva
  5. SPREAD APY: diferencia yields entre plataformas (DeFiLlama)
```

## Calibración por riesgo
```
ALTO: NVDA, TSLA, COIN, MSTR, SOL, RENDER, SUI + copy trading + apalancamiento 2x
  PROHIBIDO: VOO, VT, SCHD, QQQ | MÁXIMO 10% defensivo
MODERADO: QQQ, AAPL, BTC, ETH, staking | MÁXIMO 30% defensivo
BAJO: VOO, VT, SCHD, stablecoins | MÁXIMO 60% defensivo
```

## Señales entrada/salida
```
COMPRAR: RSI < 35 en soporte | MACD cruce alcista | Breakout con volumen
VENDER: RSI > 75 | Take profit parcial al +30% | Fundamentales deteriorados
```

## Narrativas (actualizar cada consulta)
```
Identificar 3 narrativas dominantes.
Para riesgo alto: incluir al menos 1 posición en la narrativa dominante.
```
