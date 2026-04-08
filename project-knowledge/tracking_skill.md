# Skill: Seguimiento de inversiones — v2

## Cuándo se activa
- Al final de cada plan (calendario de seguimiento)
- Cuando el usuario dice "revisa mis inversiones" o "cómo van mis posiciones"
- Cuando el usuario reporta compras/ventas

## Onboarding de seguimiento
```
El agente NO recuerda entre sesiones. Cada vez que el usuario vuelve:
  → Preguntar posiciones actuales (activo, cantidad, precio entrada, plataforma)
  → O consultar MetaTrader 5 / eToro MCP si están conectados
  → Consultar precios actuales via MCP servers
```

## Alertas automáticas
```
🔴 ROJA (acción recomendada):
  Pérdida > 15% | APY cayó > 50% | Trader drawdown > 20% | RSI > 80 con ganancia > 20%

🟡 AMARILLA (monitorear):
  Pérdida 5-15% | Correlación > 0.7 | Vertical > 40% | Dividendo próximo

🟢 VERDE (en plan):
  Rendimiento dentro del rango base | Asignación dentro de ±5% objetivo
```

## Calendario por tipo de activo
```
DIARIO: Cripto (precio, cambio 24h)
SEMANAL: Copy trading (rendimiento trader), DeFi yields (APY actual)
MENSUAL: ETFs/acciones (rendimiento, DCA con ahorro), rebalanceo si desviación > 5%
TRIMESTRAL: Stress test completo, evaluar estrategia, revisar impuesto acumulado
ANUAL: Preparar info para DIAN, consolidar rendimientos
```

## Rebalanceo
```
Si desviación > 5%: calcular cuánto mover
Si posición +50%: toma parcial ganancias (vender 25%)
Si posición -20% + fundamentales OK: oportunidad DCA
Si capital nuevo ($50/mes): asignar a vertical más subponderada
```

## Manejo de emociones
```
"Todo está cayendo": consultar datos reales, contextualizar vs benchmark, recordar horizonte
"Quiero vender todo": preguntar razón, calcular impacto fiscal, sugerir venta parcial
"Quiero invertir más": evaluar portafolio actual, asignar a subponderada
```

## Recordatorio al final de cada plan
```
"PRÓXIMAS REVISIONES:
- Semana 2: revisa rendimiento de copy trading
- Mes 1: primera revisión + DCA con ahorro mensual
- Mes 3: stress test completo
Escríbeme 'revisa mi portafolio' cuando quieras seguimiento."
```
