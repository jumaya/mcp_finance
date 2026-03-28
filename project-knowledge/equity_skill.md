# Skill: Agente de acciones y ETFs

## Cuándo se activa
Este skill se activa automáticamente cuando:
- El perfil del usuario incluye tolerancia moderada o agresiva
- El usuario menciona acciones, ETFs, bolsa, S&P 500, dividendos
- El allocate_portfolio asigna capital a la vertical "equity"

## Lógica de decisión autónoma

### Selección de activos
```
SI capital asignado a equity < $50:
  → Solo 1 ETF diversificado (VOO o VT)
  → Explicar: "Con menos de $50 es mejor concentrar en un solo fondo diversificado"

SI capital entre $50 y $200:
  → 2 ETFs: uno de base (VOO) + uno de ingreso (SCHD o VYM)
  → Proporción: 70% base + 30% ingreso

SI capital entre $200 y $500:
  → 3-4 posiciones: base (VOO) + crecimiento (QQQ) + ingreso (SCHD) + bono (BND si moderado)
  → Proporción según tolerancia

SI capital > $500:
  → 4-5 posiciones incluyendo acciones individuales (MSFT, AMD, o del sector que le interese)
  → ETFs como base (60%) + individuales como satélite (40%)
```

### Validación de correlación (ejecutar SIEMPRE)
```
SI el plan incluye VOO y QQQ:
  → Obtener precios históricos 30 días de ambos con Alpha Vantage
  → Ejecutar calculate_correlation
  → SI correlación > 0.7:
    → REEMPLAZAR parte de QQQ con BND (bonos, corr ~0.15) o VWO (emergentes, corr ~0.62)
    → Explicar al usuario: "VOO y QQQ se mueven casi igual. Reemplacé parte de QQQ con [X] para que si uno baja, el otro no necesariamente baje también"
```

### Evaluación técnica (ejecutar para cada activo candidato)
```
→ Consultar Alpha Vantage: precio actual, RSI 14d, P/E ratio
→ SI RSI > 70: advertir "Este activo está sobrecomprado (muchos han comprado recientemente). Podría corregir a corto plazo. Considera esperar 1-2 semanas o entrar con la mitad ahora y la mitad después."
→ SI RSI < 30: señalar "Este activo está sobrevendido (ha caído mucho). Podría ser buen punto de entrada, pero verifica que no haya una razón fundamental para la caída."
→ SI P/E > 35 y perfil es moderado: advertir "Este activo está caro comparado con sus ganancias. El riesgo de corrección es mayor."
```

## Datos a obtener (Alpha Vantage)
Para cada activo candidato, consultar:
1. GLOBAL_QUOTE → precio actual, cambio diario
2. OVERVIEW → P/E, EPS, dividend yield, market cap, 52w high/low
3. RSI (function=RSI, interval=daily, time_period=14)

## Plataformas y decisión automática
```
SI usuario no tiene cuenta en ninguna plataforma:
  → Recomendar Hapi (más fácil, desde $5, PSE/Nequi)
  
SI usuario ya tiene eToro:
  → Usar eToro para acciones (ya tiene cuenta)
  → Agregar Hapi solo si eToro no tiene un activo específico

SI capital a invertir > $1000 y perfil avanzado:
  → Considerar Interactive Brokers (mejores comisiones para volumen)
```

| Plataforma | Mínimo | Comisión | Depósito CO | Regulación |
|-----------|--------|----------|-------------|------------|
| Hapi | $5 | $0 broker, ~$0.10 clearing | PSE, Nequi | SEC/FINRA/SIPC |
| eToro | $200 | $0 acciones reales | PayPal, tarjeta | CySEC/FCA |
| XTB | $0 | $0 hasta 100K EUR/mes | PSE | KNF/FCA |

## ETFs base (consultables)
| ETF | Qué es | Expense | Dividend yield | Para qué |
|-----|--------|---------|---------------|----------|
| VOO | S&P 500 | 0.03% | ~1.3% | Base de todo portafolio |
| QQQ | NASDAQ 100 | 0.20% | ~0.5% | Crecimiento tech |
| VT | Mercado global | 0.07% | ~1.5% | Máxima diversificación |
| SCHD | Dividendos selectos | 0.06% | ~3.5% | Ingreso pasivo cash |
| VYM | Alto dividendo | 0.06% | ~2.8% | Ingreso pasivo estable |
| BND | Bonos USA | 0.03% | ~3.5% | Reducir volatilidad |
| VWO | Mercados emergentes | 0.08% | ~3.0% | Descorrelacionar de USA |
| GLD | Oro | 0.40% | 0% | Cobertura crisis |

## Cálculos obligatorios por posición
Para CADA activo que entre en el plan:
1. `calculate_scenarios(amount, expected_apy, volatility, passive_income, months)`
   - Para VOO: apy=0.10, volatility=0.15, passive_income basado en dividend yield
   - Para QQQ: apy=0.12, volatility=0.20
   - Para BND: apy=0.04, volatility=0.05
2. `calculate_risk_score(volatility_30d, max_drawdown_12m, "instant", True, weight_pct)`
3. `calculate_tax_impact("us_etf_dividend", estimated_annual_dividend, has_w8ben)`

## Cronograma (auto-generar según plataforma elegida)
```
SI plataforma = Hapi:
  Día 1: Descargar app + registrar con cédula (15 min, verificación 24h)
  Día 2: Depositar via PSE ($0) + comprar con orden limit (~$0.10 clearing)
  Día 2: Llenar W-8BEN en Configuración > Información fiscal (5 min)
  Día 15: Verificar posición en portafolio
  Día 30: Segundo aporte DCA

SI plataforma = eToro:
  Día 1: Registrar en etoro.com (10 min, KYC 1-3 días)
  Día 3: Depositar $200 mínimo via PayPal o tarjeta
  Día 3: Comprar activos. Llenar W-8BEN si aplica
  Día 30: Segundo aporte
```

## W-8BEN (decisión automática)
```
SI el plan incluye cualquier acción o ETF de USA:
  → SIEMPRE incluir en el cronograma: "Llenar W-8BEN"
  → SIEMPRE calcular impacto con y sin W-8BEN para mostrar la diferencia
  → SIEMPRE marcar como URGENTE si no lo tiene
```

## Explicación adaptativa
```
SI principiante:
  "Un ETF es como una canasta con pedacitos de muchas empresas. En lugar de comprar una acción de Apple por $230, compras un pedacito de un fondo que INCLUYE Apple junto con otras 499 empresas."

SI intermedio:
  "VOO replica el S&P 500 con expense ratio de 0.03%. Históricamente ~10% anual."

SI avanzado:
  "VOO (SPY si prefieres mayor liquidez), ER 0.03%, tracking error mínimo. P/E actual del índice en [consultar]."
```
