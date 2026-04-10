# Skill: Acciones y ETFs — v6

## Activos por riesgo
```
ALTO: NVDA, TSLA, AMD, COIN, MSTR, PLTR, SOFI, RIOT, MARA, SNOW, NOW, INTU, CRM
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

## Tabla de volatilidades por ticker (usar en calculate_risk_score)
```
USAR ESTOS VALORES EXACTOS — no estimar ni usar rangos:

| Ticker | volatility_30d | max_drawdown_12m | Notas                    |
|--------|---------------|------------------|--------------------------|
| NVDA   | 0.35          | -0.45            | Semiconductores/IA       |
| TSLA   | 0.45          | -0.55            | Muy volátil, polarizante |
| AMD    | 0.30          | -0.40            | Semiconductores          |
| COIN   | 0.50          | -0.60            | Proxy cripto, beta ~3x   |
| MSTR   | 0.55          | -0.65            | Proxy BTC apalancado     |
| PLTR   | 0.35          | -0.40            | IA gobierno/empresa      |
| SNOW   | 0.35          | -0.45            | SaaS cloud data          |
| NOW    | 0.30          | -0.40            | SaaS enterprise          |
| RIOT   | 0.55          | -0.65            | Minero BTC               |
| MARA   | 0.55          | -0.65            | Minero BTC               |
| SOFI   | 0.40          | -0.50            | Fintech                  |
| INTU   | 0.25          | -0.35            | SaaS finanzas            |
| CRM    | 0.25          | -0.35            | SaaS enterprise          |
| AAPL   | 0.12          | -0.20            | Blue-chip                |
| MSFT   | 0.12          | -0.18            | Blue-chip                |
| GOOGL  | 0.15          | -0.22            | Blue-chip                |
| AMZN   | 0.18          | -0.25            | E-commerce + cloud       |
| QQQ    | 0.12          | -0.20            | ETF Nasdaq 100           |
| VOO    | 0.08          | -0.15            | ETF S&P 500              |

Si el ticker NO está en esta tabla:
  → Buscar volatilidad real en Alpha Vantage o TradingView
  → Usar como referencia el activo más similar de la tabla
```

## Cómo llamar calculate_risk_score (ejemplo)
```
Para NOW con CFD 2x, peso 35%:
  calculate_risk_score(
    volatility_30d=0.30,      ← de la tabla
    max_drawdown_12m=-0.40,   ← de la tabla
    liquidity="instant",
    platform_regulated=true,
    weight_in_portfolio_pct=35,
    leverage=2.0
  )
  Resultado esperado: ~7.5-8.5 "high" (por la tabla + leverage floor del server.py)

Para AAPL spot, peso 20%:
  calculate_risk_score(
    volatility_30d=0.12,
    max_drawdown_12m=-0.20,
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

## Tool calls obligatorios
```
POR CADA acción:
  1. Alpha Vantage → precio, RSI, MACD, SMA50, SMA200
  2. Yahoo Finance → earnings date
  3. TradingView → señal técnica
  4. calculate_risk_score(vol_tabla, dd_tabla, "instant", true, peso, leverage)
  5. calculate_scenarios(monto, apy, vol_tabla, 0, meses, leverage, monthly_cost)
  6. calculate_tax_impact("equity_capital_gain", ganancia_estimada)
  7. Si 2+ acciones: calculate_correlation
```
