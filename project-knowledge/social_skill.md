# Skill: Copy trading — v7

## REGLA: Si usa eToro + riesgo ≥ 5 → copy trading OBLIGATORIO como posición

## Cómo obtener Popular Investors reales de eToro

### Opción 1: Usar eToro MCP (search_e_toro_api_docs)
```
El eToro MCP oficial solo expone tools de documentación.
EJECUTAR search_e_toro_api_docs para obtener info de endpoints.
PERO NO puede consultar datos reales de traders.
```

### Opción 2: API REST directa de eToro (PREFERIDA)
```
La API de eToro tiene un endpoint REAL para buscar Popular Investors:

ENDPOINT: GET https://public-api.etoro.com/api/v1/user-info/people/search

PARÁMETROS CLAVE:
  period: "LastYear" (rendimiento último año)
  popularInvestor: true (solo Popular Investors)
  sort: "-gain" (ordenar por mayor rendimiento)
  maxDailyRiskScoreMin: 1
  maxDailyRiskScoreMax: 7 (filtrar por riesgo)
  page: 1
  pageSize: 5
  isTestAccount: false
  blocked: false

HEADERS REQUERIDOS:
  x-api-key: [la API key del usuario]
  x-user-key: [la user key del usuario]
  x-request-id: [UUID único]

EL AGENTE DEBE:
  1. Indicar al usuario que puede consultar este endpoint directamente
  2. Dar el comando curl exacto para que el usuario lo ejecute
  3. Explicar los campos de respuesta relevantes

COMANDO CURL PARA EL USUARIO:
  curl -s "https://public-api.etoro.com/api/v1/user-info/people/search?period=LastYear&popularInvestor=true&sort=-gain&maxDailyRiskScoreMax=7&page=1&pageSize=5&isTestAccount=false" \
    -H "x-api-key: TU_API_KEY" \
    -H "x-user-key: TU_USER_KEY" \
    -H "x-request-id: $(uuidgen)"

CAMPOS DE RESPUESTA RELEVANTES:
  userName: nombre del trader
  gain: rendimiento en el período (ej: 0.45 = +45%)
  riskScore: score de riesgo eToro (1-10)
  copiers: número de copiadores
  peakToValley: máximo drawdown (ej: -0.18 = -18%)
  winRatio: porcentaje de trades ganadores
  trades: número total de trades
  profitableMonthsPct: % de meses rentables
  topTradedAssetClassId: tipo de activo principal
```

### Endpoint de rendimiento por trader específico
```
Para verificar un trader conocido:
  GET https://public-api.etoro.com/api/v1/user-info/people/{username}/gain
  Devuelve rendimiento mensual y anual histórico detallado.
```

### Endpoint de portafolio en vivo
```
Para ver las posiciones abiertas de un trader:
  GET https://public-api.etoro.com/api/v1/user-info/people/{username}/portfolio/live
```

## Presentación en el plan

### Si el usuario tiene API key y user key:
```
DAR el comando curl exacto adaptado a sus keys.
Explicar: "Ejecuta este comando en tu terminal para ver los 5 mejores 
Popular Investors del último año. Luego dime los resultados y te ayudo a seleccionar."
```

### Si el usuario NO tiene user key:
```
1. Indicar: "Para consultar via API necesitas tu User Key.
   Ve a https://api-portal.etoro.com/ → Gestión de claves API → Crear clave API"
2. Dar criterios de búsqueda manual:
   "En eToro → Descubrir → Popular Investors → Filtros: rendimiento >25%, riesgo 5-7"
3. Nombres de referencia como fallback:
   @JeppeKirkBonde, @jaynemesis, @crypto101_kevin (verificar rendimiento actual)
```

## Parámetros para calculate_risk_score por tipo de trader
```
| Tipo de trader      | volatility_30d | max_drawdown_12m | Resultado esperado |
|---------------------|---------------|------------------|--------------------|
| Agresivo cripto     | 0.30          | -0.35            | ~4.5-5.5 moderate  |
| Agresivo tech       | 0.25          | -0.30            | ~4.0-5.0 moderate  |
| Mixto cripto+tech   | 0.25          | -0.30            | ~4.0-5.0 moderate  |
| Conservador         | 0.10          | -0.15            | ~2.0-3.0 low       |

Parámetros fijos: liquidity="instant", platform_regulated=true, leverage=1.0
```

## Gestión post-inversión
```
SEMANAL: revisar rendimiento del trader
Si drawdown > 25%: evaluar salida
Si inactivo > 2 semanas: considerar cambio
Si rendimiento < 0% en 3 meses: dejar de copiar
```
