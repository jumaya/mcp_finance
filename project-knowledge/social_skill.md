# Skill: Copy trading — v5

## REGLA: Si usa eToro + riesgo ≥ 5 → copy trading OBLIGATORIO como posición

## Limitación conocida del eToro MCP server
```
IMPORTANTE: El eToro MCP server oficial (api-portal.etoro.com/mcp) solo expone 2 tools:
  - search_e_toro_api_docs → buscar en documentación de la API
  - get_page_e_toro_api_docs → leer páginas de documentación

NO tiene tools para consultar Popular Investors en tiempo real.

ACCIÓN DEL AGENTE:
  1. EJECUTAR search_e_toro_api_docs con query "popular investors" o "copy trading API"
     → Esto puede revelar endpoints de la API que el usuario podría usar directamente
  2. EJECUTAR get_page_e_toro_api_docs para leer la documentación de copy trading
     → Esto puede dar información sobre cómo funciona el copy trading en eToro
  3. Indicar en el resultado: "(via eToro MCP: documentación consultada)"
  4. DAR criterios de búsqueda específicos para que el usuario busque manualmente:
     → "En eToro → Descubrir → Popular Investors → Filtros: rendimiento >25%/año, 
        riesgo 5-8, drawdown <25%, activo últimos 30 días, >500 copiadores"
  5. DAR nombres de referencia conocidos PERO marcar como "(verificar en eToro)":
     → @JeppeKirkBonde, @jaynemesis, @crypto101_kevin (datos históricos, verificar actual)
```

## Criterios por riesgo
```
ALTO (7-10): rendimiento >25%/año, acepto drawdown 30%, risk 5-8, cripto+tech
MODERADO (4-6): rendimiento >10%/año, drawdown <15%, risk 3-5
BAJO (1-3): rendimiento >5%/año, drawdown <10%, risk 1-3
```

## Copy trading como POSICIÓN (formato obligatorio)
```
📊 COPY TRADING — eToro — Copy 2-3 traders
  Capital: $XX (XX% del portafolio)
  
  Criterios de búsqueda (aplicar en eToro):
    Rendimiento 12M: >XX%
    Drawdown máximo: <XX%
    Risk score: X-X/10
    Activo: últimos 30 días
    Copiadores: >500
  
  Traders de referencia (verificar en eToro):
    @trader1 — rendimiento histórico +XX% (verificar actual)
    @trader2 — rendimiento histórico +XX% (verificar actual)
  
  Escenarios (via calculate_scenarios):
    🟢 Optimista: +XX% → $XX
    🟡 Base: +XX% → $XX  
    🔴 Pesimista: -XX% → $XX
  
  Risk score: X.X/10 (via calculate_risk_score)
  Impuesto CO: renta fuente extranjera
  
  SL: Si drawdown de trader > 25% → dejar de copiar
  TP: Dejar componer. Revisar mensualmente.
```

## Cálculos obligatorios
```
Para copy trading, usar estos parámetros en calculate_risk_score:
  volatility_30d: 0.15 (15% — volatilidad típica de trader agresivo)
  max_drawdown_12m: -0.25 (25% — drawdown típico)
  liquidity: "instant" (puedes dejar de copiar inmediatamente)
  platform_regulated: true (eToro regulado CySEC/FCA)
  weight_in_portfolio_pct: [el peso real]
  leverage: 1.0 (el leverage lo aplica el trader internamente)

Esto debería dar un risk score de ~4-5 para traders agresivos.
```
