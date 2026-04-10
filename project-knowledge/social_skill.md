# Skill: Copy trading — v6

## REGLA: Si usa eToro + riesgo ≥ 5 → copy trading OBLIGATORIO como posición

## Limitación conocida del eToro MCP server
```
El eToro MCP oficial (api-portal.etoro.com/mcp) solo expone 2 tools:
  - search_e_toro_api_docs → buscar en documentación
  - get_page_e_toro_api_docs → leer páginas de docs

NO tiene tools para consultar Popular Investors en tiempo real.

ACCIÓN DEL AGENTE:
  1. EJECUTAR search_e_toro_api_docs con query "popular investors" o "copy trading"
  2. Indicar: "(via eToro MCP: documentación consultada)"
  3. DAR criterios de búsqueda específicos para búsqueda manual:
     "En eToro → Descubrir → Popular Investors → Filtros: rendimiento >X%, riesgo X-X"
  4. DAR nombres de referencia marcados como "(verificar en eToro)":
     @JeppeKirkBonde, @jaynemesis, @crypto101_kevin
```

## Criterios de búsqueda por riesgo
```
ALTO (7-10): rendimiento >25%/año, drawdown <30%, risk eToro 5-8, cripto+tech
MODERADO (4-6): rendimiento >10%/año, drawdown <15%, risk eToro 3-5
BAJO (1-3): rendimiento >5%/año, drawdown <10%, risk eToro 1-3
```

## Parámetros para calculate_risk_score por tipo de trader
```
USAR ESTOS VALORES EXACTOS según el tipo de trader buscado:

| Tipo de trader      | volatility_30d | max_drawdown_12m | Resultado esperado |
|---------------------|---------------|------------------|--------------------|
| Agresivo cripto     | 0.30          | -0.35            | ~4.5-5.5 moderate  |
| Agresivo tech       | 0.25          | -0.30            | ~4.0-5.0 moderate  |
| Mixto cripto+tech   | 0.25          | -0.30            | ~4.0-5.0 moderate  |
| Conservador         | 0.10          | -0.15            | ~2.0-3.0 low       |
| Moderado            | 0.15          | -0.20            | ~3.0-4.0 low-mod   |

Parámetros fijos para TODOS los tipos:
  liquidity: "instant"
  platform_regulated: true
  leverage: 1.0 (el leverage lo aplica el trader internamente)
  weight_in_portfolio_pct: [peso real en el plan]
```

## Ejemplo de llamada (trader agresivo cripto+tech, peso 30%)
```
calculate_risk_score(
  volatility_30d=0.25,
  max_drawdown_12m=-0.30,
  liquidity="instant",
  platform_regulated=true,
  weight_in_portfolio_pct=30,
  leverage=1.0
)
→ Resultado esperado: ~4.5 "moderate"

calculate_scenarios(
  amount_usd=150,
  expected_apy=0.25,
  volatility_annual=0.30,
  passive_income_annual_usd=0,
  months=6,
  leverage=1.0,
  monthly_cost_usd=0
)
```

## Gestión post-inversión
```
SEMANAL: revisar rendimiento del trader
Si drawdown > 25%: evaluar salida
Si inactivo > 2 semanas: considerar cambio
Si rendimiento < 0% en 3 meses consecutivos: dejar de copiar
```
