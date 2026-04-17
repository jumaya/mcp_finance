# Skill: Copy trading — v7

## REGLA: Si usa eToro + riesgo ≥ 5 → copy trading OBLIGATORIO como posición

## eToro MCP — Tools reales disponibles
```
El eToro MCP server (orkblutt) expone tools reales para consultar Popular Investors.
USAR ESTAS TOOLS — no inventar datos ni dar solo nombres de referencia.

TOOLS DISPONIBLES:
  discover_users        → buscar Popular Investors con filtros de rendimiento y riesgo
  get_user_profile      → perfil completo de un trader
  get_user_performance  → rendimiento histórico detallado
  get_user_portfolio    → portafolio en vivo (qué tiene abierto)
  search_instruments    → verificar si un activo está disponible en eToro
```

## Paso 3 del orquestador: Cómo ejecutar

### 1. Buscar Popular Investors (EJECUTAR discover_users)
```
EJECUTAR:
  discover_users(
    period="LastYear",
    popularInvestor=true,
    maxDailyRiskScoreMax=7,    ← ajustar según perfil de riesgo
    pageSize=5
  )

PARA RIESGO ALTO:
  discover_users(period="LastYear", popularInvestor=true, maxDailyRiskScoreMax=8, pageSize=5)

PARA RIESGO MODERADO:
  discover_users(period="LastYear", popularInvestor=true, maxDailyRiskScoreMax=5, pageSize=5)

De la respuesta, extraer para cada trader:
  userName → nombre del trader
  gain → rendimiento (0.45 = +45%)
  riskScore → score eToro 1-10
  copiers → número de copiadores
  peakToValley → drawdown máximo (-0.18 = -18%)
  winRatio → % trades ganadores
  profitableMonthsPct → % meses rentables
  trades → total de trades
```

### 2. Verificar rendimiento detallado (EJECUTAR get_user_performance)
```
Para los top 2-3 traders del paso anterior:
  get_user_performance(username="nombre_del_trader")

Esto da rendimiento mensual y anual histórico detallado.
Buscar consistencia: ¿gana la mayoría de meses o tiene picos y caídas?
```

### 3. Ver portafolio actual (EJECUTAR get_user_portfolio)
```
Para confirmar que el trader está activo y qué opera:
  get_user_portfolio(username="nombre_del_trader")

Verificar:
  → ¿Tiene posiciones abiertas? (si no, está inactivo)
  → ¿Qué tipo de activos opera? (cripto, acciones, mixto)
  → ¿Tiene posiciones apalancadas?
```

### 4. Verificar disponibilidad de activos (EJECUTAR search_instruments)
```
Antes de recomendar un activo en eToro, verificar que existe:
  search_instruments(query="CRM", exactSymbol=true)
  search_instruments(query="Bitcoin")

Si el instrumento no aparece → NO recomendar en eToro
```

## Formato de presentación (con datos reales del MCP)
```
👥 PASO 3 — POPULAR INVESTORS eTORO (via eToro MCP)

Fuente: discover_users + get_user_performance (datos en tiempo real)

1. @username1 | +XX% último año | Drawdown -XX% | Risk X/10 | Copiadores: X,XXX
   Win ratio: XX% | Meses rentables: XX% | Trades: XXX
   Portafolio: [cripto/tech/mixto] (via get_user_portfolio)
   → Seleccionado porque: [razón basada en datos reales]

2. @username2 | ...

POSICIÓN RECOMENDADA:
  Copiar @username1 con $XX y @username2 con $XX
  Capital total copy trading: $XX (XX% del portafolio)
```

## SI el eToro MCP da error 401 (Unauthorized)
```
Esto significa que las API keys no están configuradas correctamente.
El usuario debe verificar en claude_desktop_config.json:

  "etoro-mcp": {
    "command": "node",
    "args": ["C:\\Proyectos\\eToro-MCP\\dist\\index.js"],
    "env": {
      "ETORO_API_KEY": "su_api_key_publica",
      "ETORO_USER_KEY": "su_user_key_privada",
      "ETORO_TRADING_MODE": "demo"
    }
  }

SI el error persiste después de configurar:
  → Indicar: "El eToro MCP devolvió error 401. Verifica tus API keys en Settings → Trading"
  → Dar criterios de búsqueda manual como fallback:
    "En eToro → Descubrir → Popular Investors → Filtros: rendimiento >25%, riesgo 5-7"
  → Nombres de referencia: @JeppeKirkBonde, @jaynemesis (verificar rendimiento actual)
```

## Parámetros para calculate_risk_score por tipo de trader
```
DESPUÉS de obtener datos reales del trader via discover_users, usar:
  volatility_30d: usar el riskScore del trader / 20 (ej: riskScore 6 → vol 0.30)
  max_drawdown_12m: usar peakToValley del trader (ej: -0.25)
  liquidity: "instant"
  platform_regulated: true
  leverage: 1.0
  weight_in_portfolio_pct: [peso real]

SI no hay datos reales (fallback), usar tabla:
  | Tipo de trader      | volatility_30d | max_drawdown_12m |
  |---------------------|---------------|------------------|
  | Agresivo cripto     | 0.30          | -0.35            |
  | Mixto cripto+tech   | 0.25          | -0.30            |
  | Conservador         | 0.10          | -0.15            |
```

## Gestión post-inversión
```
SEMANAL: get_user_performance para revisar rendimiento del trader
Si drawdown > 25%: evaluar salida
Si inactivo (get_user_portfolio vacío): considerar cambio
Si rendimiento < 0% en 3 meses: dejar de copiar
```
