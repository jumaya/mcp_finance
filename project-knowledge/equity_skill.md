# Skill: Acciones y ETFs — v4

## Cuándo se activa
Paso 4 del orquestador cuando hay acciones o ETFs.

## Activos por riesgo
```
ALTO: NVDA, TSLA, AMD, COIN, MSTR, PLTR, SOFI, RIOT, MARA | ETFs: TQQQ, SOXL
  PROHIBIDO: VOO, VT, SCHD, QQQ sin apalancamiento
MODERADO: QQQ, XLK, AAPL, MSFT, GOOGL, AMZN
BAJO: VOO, VT, SCHD
```

## Apalancamiento eToro CFDs
```
Riesgo ALTO → sugerir CFD 2x en acciones de convicción
  - 2x: ganancia/pérdida se duplica
  - NUNCA 5x con capital < $1000
  
COSTOS OVERNIGHT (incluir SIEMPRE en CFDs):
  Fee diario ≈ monto × apalancamiento × 0.015%
  Fee mensual ≈ fee_diario × 30
  
  Ejemplos:
    $200 con 2x = $400 exposición → ~$1.80/mes overnight
    $150 con 2x = $300 exposición → ~$1.35/mes overnight
  
  RESTAR del rendimiento neto:
    Si TP1 es +25% en 3 meses = +$50
    Overnight 3 meses = ~$5.40
    Rendimiento neto real = +$44.60 (+22.3%)
  
  MENCIONAR en cada posición CFD:
    "Costo overnight: ~$X.XX/mes. En 3 meses: ~$XX. Rendimiento neto ajustado: +XX%"
```

## Tool calls obligatorios POR CADA acción
```
1. Alpha Vantage → precio, RSI, MACD, SMA50, SMA200, P/E
2. Yahoo Finance → earnings date, analyst consensus
3. TradingView → señal técnica del sector
4. calculate_scenarios(monto, rendimiento, volatilidad, 0, meses)
5. calculate_risk_score(volatilidad, drawdown, liquidez, apalancado, peso)
6. calculate_tax_impact("equity_capital_gain", ganancia_estimada)
```

## Correlación (OBLIGATORIO si 2+ acciones)
```
EJECUTAR calculate_correlation entre acciones del portafolio.
Pares a verificar especialmente:
  COIN ↔ BTC/ETH: correlación ~0.8 (COIN es proxy de cripto)
  NVDA ↔ AMD: correlación ~0.7 (mismo sector)
  TSLA ↔ mercado general: beta 2.3 amplifica todo

SI correlación > 0.7:
  → ADVERTIR: "Estas posiciones se mueven juntas. En un crash, ambas caen simultáneamente"
  → SUGERIR: diversificar con un activo menos correlacionado
```

## Earnings como catalizador
```
SI hay earnings próximos (< 30 días) de una acción en el portafolio:
  → INCLUIR la fecha en el cronograma semanal
  → Ejemplo: "Semana 3: COIN earnings 7 mayo — evaluar posición antes"
  → Sugerir: reducir posición 25% antes del earnings si ya tiene ganancia
  → O: mantener si la tesis incluye el earnings como catalizador
```
