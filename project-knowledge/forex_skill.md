# Skill: Agente de Forex y CFDs — v2

## Cuándo se activa
Este skill se activa cuando:
- El allocate_portfolio asigna capital a "forex"
- El usuario menciona forex, divisas, trading, pares, EUR/USD, apalancamiento
- NUNCA se activa como primera recomendación para principiantes

## 🚪 Gate de disponibilidad eToro (para pares/CFDs operados en eToro)

**Cuándo aplica:** solo si el plan propone operar en eToro (no aplica a
Capital.com, XTB, Pepperstone, MetaTrader con otro broker).

Algunos pares y CFDs sobre commodities (p.ej. XAU/USD) pueden no estar
disponibles para cuentas retail desde Colombia, o estar deshabilitados
temporalmente por condiciones de mercado.

### Protocolo
```
POR CADA par/CFD que se vaya a operar EN eToro:

  etoro-server.search_instruments(
    query="<SYMBOL>",         # ej. "EURUSD", "GBPUSD", "XAUUSD"
    search_by="internalSymbolFull",
    page_size=5
  )

Validar en el primer resultado cuyo symbol coincida:

  ✅ instrumentType ∈ {"Currencies", "Commodities"}
  ✅ isCurrentlyTradable == true
  ✅ isBuyEnabled == true   (o validar según dirección de la operación)

Si falla:
  → par NO operable en eToro para esta cuenta
  → opción 1: sugerir otro broker de la tabla (Capital.com es la mejor
    alternativa desde Colombia por depósito PSE)
  → opción 2: reemplazar por un par líquido equivalente que sí pase
  → informar al usuario antes de continuar
```

Si el usuario ya eligió broker **distinto de eToro**, este gate no
aplica — usar los datos del broker correspondiente.

## Lógica de decisión autónoma

### Barrera de entrada (evaluar ANTES de recomendar)
```
SI experience_level = "none":
  → NO incluir forex en el plan inicial
  → Mencionar como opción futura: "En el mes 3-4 podemos explorar forex con cuenta demo"
  → DETENER este skill

SI experience_level = "beginner":
  → SOLO con cuenta demo obligatoria (1 mes mínimo)
  → Capital real máximo: $100 o 10% del capital total (lo menor)
  → Solo pares principales (EUR/USD, GBP/USD)
  → Apalancamiento máximo: 2x

SI experience_level = "intermediate" o "advanced":
  → Incluir con capital real
  → Apalancamiento máximo: 5x
  → Todos los pares principales + XAU/USD
```

### Selección de pares autónoma
```
→ Consultar Alpha Vantage: CURRENCY_EXCHANGE_RATE para pares principales
→ Consultar FX_DAILY últimos 30 días para tendencia

SI hay tendencia clara en D1 (precio arriba/abajo de media 50 consistentemente):
  → Recomendar ese par para swing en dirección de tendencia
  → Explicar: "El [par] tiene tendencia [alcista/bajista] las últimas semanas"

SI no hay tendencia clara en ningún par:
  → NO recomendar forex activo en esta iteración
  → "Los mercados de divisas están sin dirección clara. Mejor esperar."
  → Esto es comportamiento inteligente: saber cuándo NO actuar
```

### Dimensionamiento automático
```
SIEMPRE ejecutar calculate_position_size:
→ risk = 1% para beginners, 2% para intermediate+
→ stop_loss = soporte/resistencia más cercano o ATR×1.5
→ leverage = 1x beginners, hasta 5x avanzados

SI el tool retorna warnings:
  → Ajustar automáticamente (reducir leverage o posición)
  → Explicar el ajuste
```

### Reglas duras
```
NUNCA: apalancamiento > 5x | más de 3 trades simultáneos | riesgo > 2% por trade | trade sin stop loss
SIEMPRE: stop loss + TP1 (1:2 R:R) + TP2 (1:3 R:R) | verificar calendario económico | mostrar pérdida máxima en USD
```

## Plataformas y selección automática
```
SI no tiene cuenta forex → Capital.com (PSE directo, más fácil en CO)
SI ya tiene eToro → usar eToro (pero pasar gate de disponibilidad)
SI quiere MetaTrader → Pepperstone o XTB
```

| Plataforma | Depósito CO | Spread EUR/USD | Demo | Regulación |
|-----------|-------------|---------------|------|------------|
| Capital.com | PSE directo | ~0.6 pips | Sí, $100K | FCA/CySEC |
| XTB | PSE, oficina CO | ~0.9 pips | Sí, $100K | KNF/FCA |
| eToro | PayPal, tarjeta | ~1.0 pips | Sí, $100K | CySEC/FCA/ASIC |
| Pepperstone | Transferencia | ~0.1 pips raw | Sí | ASIC/FCA/BaFIN |

## Pares recomendados
| Par | Spread | Volatilidad | Sesión óptima | Nota |
|-----|--------|------------|---------------|------|
| EUR/USD | 0.6-1.0 | Baja-media | Londres/NY 8am-12pm ET | Más líquido |
| GBP/USD | 1.0-1.5 | Media | Londres 3am-12pm ET | Más volátil |
| USD/JPY | 0.7-1.2 | Baja-media | Tokio/Londres | Buenos movimientos tendenciales |
| XAU/USD | 2-4 | Media-alta | NY 8am-5pm ET | Cobertura, movimientos fuertes |

## Cálculos obligatorios
0. Si se opera en eToro → **Gate eToro** (arriba) antes de seguir
1. `calculate_position_size(capital, risk_pct, entry, stop, leverage)` — OBLIGATORIO
2. `calculate_scenarios(amount, apy=0, volatility=0.15, passive=0, months)`
3. `calculate_risk_score(volatility, drawdown=-0.15, "instant", True, weight)`
4. `calculate_tax_impact("forex_gain", estimated_annual_gain)`

## Cronograma autónomo
```
SI principiante:
  Semana 1: cuenta demo (10 min)
  Semana 1-4: SOLO demo, mínimo 20 trades
  Semana 4: revisar → SI rentable: cuenta real $50-$100 | SI no: extender o reasignar

SI intermedio+:
  Día 1: abrir cuenta
  Día 2: depositar + primer análisis de pares
  Día 3+: ejecutar setups cuando condiciones se cumplan
```

## Explicación adaptativa
```
SI principiante:
  "Trading de divisas es comprar una moneda esperando que suba contra otra. A diferencia del staking o ETFs, NO genera ingreso pasivo — necesitas dedicar tiempo. Por eso empezamos con cuenta demo."

SI intermedio:
  "Swing trading en pares principales con R:R mínimo 1:2. Entrada en retrocesos a soportes en tendencia."

SI avanzado:
  "Confluencia MA20/50 + S/R + RSI no extremo en D1/H4. Position sizing 2% risk. Monitorear correlación si operas GBP y EUR simultáneamente."
```

## Advertencias obligatorias
- "70-80% de cuentas minoristas pierden dinero"
- "Apalancamiento amplifica ganancias Y pérdidas"
- "Forex NO es ingreso pasivo"
- "SIEMPRE empieza con demo"
- "Nunca inviertas dinero que necesites para gastos esenciales"
