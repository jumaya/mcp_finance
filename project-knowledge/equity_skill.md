# Skill: Acciones y ETFs — v3

## Cuándo se activa
Paso 4 del orquestador cuando hay acciones o ETFs en el plan.

## Activos por nivel de riesgo

### Riesgo ALTO (OBLIGATORIO usar esta lista)
```
Acciones de alto crecimiento:
  NVDA, TSLA, AMD, COIN, MSTR, PLTR, SOFI, RIOT, MARA

ETFs apalancados (solo para momentum, NO hold > 3 meses):
  TQQQ (Nasdaq 3x), SOXL (Semiconductores 3x)

PROHIBIDO: VOO, VT, SCHD, QQQ sin apalancamiento
```

### Riesgo MODERADO
```
ETFs sectoriales: QQQ, XLK, ARKK
Blue-chips: AAPL, MSFT, GOOGL, AMZN
```

### Riesgo BAJO
```
Solo ETFs diversificados: VOO, VT, SCHD
```

## Apalancamiento en eToro
```
Para riesgo ALTO, sugerir CFD 2x en acciones de convicción:
  - 2x en NVDA, TSLA, COIN → exposición real = doble del capital
  - NUNCA 5x (riesgo de liquidación con capital pequeño)
  - Ganancia +20% con 2x = +40% real
  - Pérdida -20% con 2x = -40% real
  - ADVERTIR siempre sobre el riesgo de liquidación
```

## Datos a consultar (MCP servers)
```
POR CADA acción:
  Alpha Vantage → precio, RSI, MACD, SMA50, SMA200, P/E, EPS
  Yahoo Finance → earnings date, analyst consensus
  TradingView → señal técnica, screener de sector
```

## Cálculos obligatorios
```
1. calculate_scenarios(monto, rendimiento, volatilidad, 0, meses)
2. calculate_risk_score(volatilidad, drawdown, liquidez, apalancado, peso)
3. calculate_tax_impact("equity_capital_gain", ganancia_estimada)
4. SI 2+ acciones: calculate_correlation entre ellas
```

## Formato de recomendación
```
TICKER | Plataforma | Tipo (Spot/CFD 2x)
Capital: $XX (XX%) | Precio: $XXX | RSI: XX
TESIS: [específica, no genérica]
CATALIZADOR: [evento + fecha]
RIESGO: [específico + precio]
Entrada: $XXX | SL: $XXX | TP1: $XXX | TP2: $XXX
Escenarios: 🟢+XX% 🟡+XX% 🔴-XX%
```
