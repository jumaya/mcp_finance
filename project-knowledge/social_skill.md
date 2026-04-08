# Skill: Copy trading — v4

## REGLA CRÍTICA
```
SI el usuario tiene eToro como plataforma Y riesgo ≥ 5/10:
  → Copy trading es OBLIGATORIO como posición en el plan
  → NO solo mostrar traders — ASIGNAR capital a copiar como posición real
  → Mínimo 15% del capital en copy trading
  → Al menos 1 de las posiciones del plan DEBE ser copy trading
```

## Consultar eToro MCP (OBLIGATORIO)
```
EJECUTAR las tools del eToro MCP server:
  → Buscar popular investors
  → Obtener datos actualizados de rendimiento

SI eToro MCP responde:
  → Usar datos reales, indicar "(via eToro MCP)"
  → Mostrar rendimiento actual, no histórico

SI eToro MCP NO responde:
  → Indicar: "No pude consultar eToro MCP — datos de referencia"
  → Marcar como "(verificar en eToro)"
  → IGUAL incluir copy trading como posición con criterios de búsqueda
```

## Criterios por riesgo
```
ALTO (7-10): rendimiento >25%/año, acepto drawdown 30%, risk 5-8, cripto+tech
MODERADO (4-6): rendimiento >10%/año, drawdown <15%, risk 3-5
BAJO (1-3): rendimiento >5%/año, drawdown <10%, risk 1-3
```

## Copy trading como POSICIÓN en el plan
```
📊 COPY TRADING — eToro — Copy 2-3 traders
  Capital: $XX (XX% del portafolio)
  Traders seleccionados:
    @trader1: $XX → rendimiento esperado +XX%/año
    @trader2: $XX → rendimiento esperado +XX%/año
  
  Escenarios (via calculate_scenarios):
    🟢 Optimista: +XX%
    🟡 Base: +XX%
    🔴 Pesimista: -XX%
  
  Risk score: X.X/10 (via calculate_risk_score)
  Impuesto CO: renta fuente extranjera (via calculate_tax_impact)
  
  SL: Si drawdown de trader > 25% → dejar de copiar
  TP: Dejar componer. Revisar mensualmente.
```

## Tool calls obligatorios
```
1. eToro MCP → buscar popular investors actuales
2. calculate_scenarios(monto_copy, rendimiento_trader, drawdown, 0, meses)
3. calculate_risk_score basado en drawdown promedio de traders
4. calculate_tax_impact("copy_trading_gain", ganancia_estimada)
```

## Gestión post-inversión
```
SEMANAL: revisar rendimiento del trader
Si drawdown > 25%: evaluar salida
Si inactivo > 2 semanas: considerar cambio
Si rendimiento < 0% en 3 meses: dejar de copiar
```
