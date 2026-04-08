# Skill: Agente de acciones y ETFs — v2

## Cuándo se activa
Automáticamente cuando el allocate_portfolio asigna capital a "equity" o el usuario menciona acciones, ETFs, bolsa, S&P 500, Nasdaq, o nombres de acciones.

## Selección de activos por nivel de riesgo

### Riesgo BAJO
```
SOLO ETFs diversificados:
  - VOO (S&P 500): el estándar de oro, 8-12% anual histórico
  - VT (mercado global): diversificación internacional
  - SCHD (dividendos): ingreso pasivo vía dividendos

NO acciones individuales para riesgo bajo.
```

### Riesgo MODERADO
```
ETFs sectoriales + blue-chips selectas:
  - QQQ (Nasdaq 100): exposición a tech, ~15% anual histórico
  - XLK (Technology Select): similar a QQQ con menos concentración
  - AAPL, MSFT, GOOGL: blue-chips de mega cap
  - AMZN: e-commerce + cloud (AWS)

Máximo 3-4 acciones individuales. Peso máximo 20% por acción.
```

### Riesgo ALTO (OBLIGATORIO usar esta lista)
```
Acciones de alto crecimiento / alta volatilidad:
  - NVDA: líder GPUs/IA, beta ~1.8, movimientos de 5-10% en un día
  - TSLA: polarizante, beta ~2.0, puede subir 50% o caer 40% en un trimestre
  - AMD: competidor directo de NVDA en IA, beta ~1.7
  - COIN: proxy de cripto en bolsa, beta ~3.0, se mueve con BTC
  - MSTR: apalancamiento implícito a BTC (~2x), beta ~3.5
  - PLTR: IA empresarial + gobierno, beta ~1.6
  - SOFI: fintech de alto crecimiento
  - RIOT/MARA: mineros de Bitcoin, beta ~3.0+

ETFs apalancados (solo para riesgo alto):
  - TQQQ: Nasdaq 3x (NO para hold > 3 meses por decay)
  - SOXL: Semiconductores 3x
  - ADVERTENCIA: ETFs apalancados pierden valor en mercados laterales

PROHIBIDO para riesgo alto:
  - VOO, VT, SCHD → demasiado conservadores
  - QQQ → solo si es TQQQ (3x)
```

## Datos a consultar ANTES de recomendar (MCP servers)
```
POR CADA acción candidata:
  1. Alpha Vantage → precio actual, P/E, EPS, dividendo, market cap
  2. Alpha Vantage → RSI, MACD, SMA50, SMA200
  3. Yahoo Finance → próximo earnings date, analyst consensus
  4. TradingView → screener para verificar señal técnica

EVALUAR:
  - RSI < 30: sobreventa → posible oportunidad de compra
  - RSI > 70: sobrecompra → esperar corrección
  - Precio < SMA200: tendencia bajista → precaución
  - Precio > SMA50 cruzando SMA200: golden cross → señal alcista
  - MACD cruzando al alza: momentum positivo
```

## Apalancamiento en eToro
```
eToro permite apalancamiento en acciones:
  - Sin apalancamiento (1x): compras la acción real
  - Con apalancamiento (2x, 5x): compras un CFD

PARA RIESGO ALTO:
  → Sugerir 2x en acciones de convicción fuerte (NVDA, TSLA)
  → NUNCA 5x (riesgo de liquidación muy alto con $100)
  → Con 2x en $25: tu exposición real es $50
  → Ganancia de +20% con 2x = +40% real
  → Pérdida de -20% con 2x = -40% real

SIEMPRE advertir:
  "El apalancamiento multiplica tanto ganancias como pérdidas. Con 2x, una caída del 50% en el activo liquida tu posición completamente."
```

## Formato de recomendación por acción
```
NOMBRE: NVDA (NVIDIA Corporation)
PLATAFORMA: eToro
MONTO: $25 (25% del portafolio)
APALANCAMIENTO: 2x (exposición real: $50)
PRECIO ACTUAL: $177.64 (via Alpha Vantage)
RSI: 49.4 (neutral — buen punto de entrada)
TENDENCIA: Lateral con soporte en SMA200 ($180)

TESIS: Semiconductores en superciclo por demanda de chips IA. NVDA está en zona neutral
tras corrección del -16% desde máximos. MACD cruzando al alza — señal de reversión.

CATALIZADOR: Earnings Q2 2026 (fecha: mayo 2026). Los últimos 4 earnings fueron beats > 10%.
Si el patrón se repite, movimiento esperado de +8-15% post-earnings.

RIESGO: Si el gasto en IA se desacelera o regulación antimonopolio afecta, soporte en $150.
P/E de 36x es alto pero justificado por crecimiento ~60% YoY.

ENTRADA: Limit order a $175 (confluencia con SMA200)
STOP LOSS: $155 (-11%)
TAKE PROFIT 1: $200 (+14%) → vender 25% de la posición
TAKE PROFIT 2: $230 (+31%) → vender otro 25%

ESCENARIOS (sobre $25 invertidos con 2x):
  Optimista (25%): +75% → $43.75 (+$18.75)
  Base (50%): +20% → $30.00 (+$5.00)
  Pesimista (25%): -40% → $15.00 (-$10.00)
```

## Cálculos obligatorios
```
1. calculate_risk_score(volatilidad_30d, max_drawdown, "high", apalancamiento > 1, peso%)
2. calculate_scenarios(monto, rendimiento_estimado, volatilidad, passive=0, months)
3. calculate_tax_impact("equity_dividend" o "equity_capital_gain", ganancia_estimada)
4. SI hay 2+ acciones en portafolio: calculate_correlation entre ellas
```

## Encadenamiento
```
→ Si recomienda NVDA + AMD → calculate_correlation (probablemente > 0.7 → advertir)
→ Si recomienda COIN o MSTR → verificar precio de BTC (CoinGecko) porque están correlacionados
→ Antes de presentar → validar contra risk_rules.md
→ Después del plan → agregar calendario de earnings en el cronograma
```
