# Skill: Copy trading — v3

## Cuándo se activa
Paso 3 del orquestador. OBLIGATORIO si el usuario tiene eToro.

## REGLA: Si usa eToro + riesgo alto → copy trading OBLIGATORIO
```
Asignar mínimo 15-25% del capital a copy trading.
Si el plan no incluye copy trading con eToro → INCOMPLETO.
```

## Consultar eToro MCP server (OBLIGATORIO)
```
1. Buscar popular investors con rendimiento > 12% anual
2. Filtrar: drawdown < 30%, activo últimos 30 días
3. Priorizar traders que operen cripto + tech (para riesgo alto)
4. Seleccionar 2-3 candidatos

SI eToro MCP no responde:
  → Mencionar que no se pudo consultar en tiempo real
  → Dar criterios de búsqueda manual
  → Sugerir buscar en eToro web: Descubrir → Popular Investors → filtrar por rendimiento
```

## Criterios por riesgo
```
ALTO: rendimiento > 25%/año, acepto drawdown 30%, risk 5-8, cripto+tech
MODERADO: rendimiento > 10%/año, drawdown < 15%, risk 3-5
BAJO: rendimiento > 5%/año, drawdown < 10%, risk 1-3
```

## Formato de salida
```
👥 @username | +XX% 12M | Drawdown -XX% | Risk X/10 | Copiadores: X,XXX
   Estilo: [cripto/acciones/mixto]
   POR QUÉ: [razón de selección]
   ASIGNACIÓN: $XX
```

## Gestión
```
→ Si drawdown > 25%: evaluar
→ Si inactivo > 2 semanas: considerar cambiar
→ Si rendimiento < 0% en 3 meses: dejar de copiar
```
