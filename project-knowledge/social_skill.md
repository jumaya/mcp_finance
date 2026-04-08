# Skill: Copy trading y social trading — v2

## Cuándo se activa
Automáticamente cuando:
- El usuario tiene eToro como plataforma
- El perfil de riesgo es moderado o alto
- El capital en eToro es >= $50 (mínimo para copiar en algunos traders)
- El usuario menciona copy trading, copiar traders, popular investors

## REGLA CRÍTICA: Si el usuario usa eToro y es riesgo alto → copy trading es OBLIGATORIO
```
El copy trading es una de las ventajas principales de eToro.
Si el usuario usa eToro y tiene perfil de riesgo alto, el plan DEBE incluir
al menos 15-20% del capital asignado a copy trading.

SI el plan no incluye copy trading cuando el usuario tiene eToro:
  → EL PLAN ESTÁ INCOMPLETO
  → Agregar sección de copy trading con traders seleccionados
```

## Selección de traders por nivel de riesgo

### Riesgo ALTO (traders agresivos)
```
CRITERIOS DE BÚSQUEDA (usar eToro MCP):
  - Rendimiento 12M: > 25% (preferiblemente > 40%)
  - Drawdown máximo: acepto hasta 30%
  - Risk score eToro: 5-8 (no extremo pero agresivo)
  - Estrategia: preferir traders que operen cripto + tech stocks
  - Activo últimos 30 días: SÍ (ha hecho trades recientes)
  - Copiadores: > 50 (señal de que es confiable)

DISTRIBUCIÓN:
  - 2-3 traders diferentes
  - Al menos 1 que opere cripto
  - Al menos 1 que opere acciones tech
  - NO copiar traders que operen solo forex con rendimiento < 20%

ASIGNACIÓN: 15-25% del capital total en eToro
```

### Riesgo MODERADO (traders balanceados)
```
CRITERIOS:
  - Rendimiento 12M: > 10%
  - Drawdown máximo: < 15%
  - Risk score: 3-5
  - Copiadores: > 100
  
ASIGNACIÓN: 10-15% del capital total
```

## Información a presentar por cada trader
```
NOMBRE DEL TRADER: @username
RENDIMIENTO 12M: +X%
DRAWDOWN MÁXIMO: -X%
RISK SCORE: X/10
COPIADORES: X
ACTIVOS PRINCIPALES: BTC, NVDA, SOL (qué opera más)
ESTILO: Swing trader / Day trader / Position trader
ASIGNACIÓN SUGERIDA: $X (Y% de tu capital)

POR QUÉ LO SELECCIONÉ:
  "Este trader tiene un rendimiento consistente de +X% en los últimos 12 meses,
  con un drawdown máximo controlado de -Y%. Opera principalmente [activos], 
  lo que complementa tus posiciones directas en [otros activos]."
```

## Reglas de gestión de copy trading
```
INICIO:
  → Empezar a copiar cuando deposites en eToro
  → NO esperar "el momento perfecto" — el trader ya está gestionando el timing

MONITOREO (tracking_skill.md se encarga):
  → Semanal: verificar rendimiento del trader
  → Si drawdown > 25%: evaluar si mantener
  → Si trader inactivo > 2 semanas: considerar cambiar

SALIDA:
  → Si el trader pierde > 30% desde que lo copias → dejar de copiar
  → Si rendimiento < 0% en 3 meses consecutivos → dejar de copiar
  → Si el trader cambia de estilo (de tech a forex) → evaluar
```

## Uso del eToro MCP server
```
Tools disponibles:
  → Buscar popular investors y sus estadísticas
  → Ver rendimiento, drawdown, copiadores
  → Consultar portafolio del trader (qué tiene)
  → Copiar trader con monto específico
  → Ver tu portafolio de copy trading

FLUJO AUTOMÁTICO:
  1. Buscar popular investors con los criterios del perfil de riesgo
  2. Filtrar por rendimiento, drawdown y actividad
  3. Verificar que no haya overlap excesivo con posiciones directas
  4. Presentar 2-3 candidatos con justificación
  5. Sugerir montos de asignación
```

## Cálculos obligatorios
```
1. calculate_scenarios(monto_copy, rendimiento_trader, drawdown_trader, 0, months)
2. calculate_risk_score basado en el drawdown del trader
3. calculate_tax_impact("copy_trading_gain", ganancia_estimada)
```

## Advertencias obligatorias
- "El rendimiento pasado de un trader no garantiza rendimiento futuro"
- "Puedes perder dinero incluso copiando traders exitosos"
- "Los Popular Investors de eToro no son asesores financieros certificados"
- "Revisa semanalmente el rendimiento de los traders que copias"
