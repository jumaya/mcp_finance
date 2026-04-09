# Skill: Acciones y ETFs — v5

## Activos por riesgo
```
ALTO: NVDA, TSLA, AMD, COIN, MSTR, PLTR, SOFI, RIOT, MARA, SNOW, NOW
  ETFs apalancados: TQQQ, SOXL (solo momentum, NO hold >3 meses)
  PROHIBIDO: VOO, VT, SCHD, QQQ sin apalancamiento

MODERADO: QQQ, XLK, AAPL, MSFT, GOOGL, AMZN
BAJO: VOO, VT, SCHD
```

## Apalancamiento eToro CFDs
```
Riesgo ALTO → CFD 2x en acciones de convicción
  NUNCA 5x con capital < $1000
  Ganancia +20% con 2x = +40% real
  Pérdida -50% con 2x = LIQUIDACIÓN TOTAL
```

## Parámetros CORRECTOS para calculate_risk_score
```
IMPORTANTE: El agente debe pasar parámetros REALISTAS, no conservadores.

ACCIONES TECH VOLÁTILES (NVDA, TSLA, COIN, SNOW):
  volatility_30d: 0.25-0.45 (25-45% — estas acciones son MUY volátiles)
  max_drawdown_12m: -0.30 a -0.55 (30-55% — caídas reales de estos activos)
  liquidity: "instant"
  platform_regulated: true (eToro)
  weight_in_portfolio_pct: [peso real]
  leverage: 2.0 (si es CFD 2x)

  Resultado esperado con estos parámetros: risk score 6.5-8.5 "high"

ACCIONES BLUE-CHIP (AAPL, MSFT):
  volatility_30d: 0.08-0.15
  max_drawdown_12m: -0.15 a -0.25
  leverage: 1.0

  Resultado esperado: risk score 2-4 "low"

SI EL RISK SCORE SALE < 5 PARA UNA ACCIÓN CON CFD 2x:
  → Los parámetros están MAL → revisar volatilidad y drawdown
  → Una acción apalancada 2x NUNCA es "low risk"
  → Ajustar volatility_30d y max_drawdown_12m al alza
```

## Overnight fees (SIEMPRE incluir en CFDs)
```
Fee diario ≈ monto × apalancamiento × 0.015%
Fee mensual = fee_diario × 30

Ejemplo: $175 con 2x = $350 exposición → ~$1.58/mes
Restar del rendimiento neto.
```

## Tool calls obligatorios
```
1. Alpha Vantage → precio, RSI, MACD, SMA50, SMA200, P/E
2. Yahoo Finance → earnings date
3. TradingView → señal técnica
4. calculate_scenarios(monto, apy, vol, 0, meses, leverage=2.0)
5. calculate_risk_score(vol_realista, dd_realista, "instant", true, peso, leverage=2.0)
6. calculate_tax_impact("equity_capital_gain", ganancia)
7. Si 2+ acciones: calculate_correlation
```

## Formato de presentación
```
OBLIGATORIO mostrar risk score como NÚMERO visible:
  "Risk score: 7.2/10 — ALTO ⚠️"
  NO solo barras gráficas — el número debe ser visible en texto.

OBLIGATORIO mostrar escenarios con NÚMEROS:
  "🟢 Optimista (25%): +90.0% → $332.50"
  "🟡 Base (50%): +35.0% → $236.25"
  "🔴 Pesimista (25%): -47.5% → $91.87"
```
