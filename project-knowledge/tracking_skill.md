# Skill: Seguimiento y monitoreo de inversiones

## Cuándo se activa
Automáticamente cuando:
- El usuario dice "revisa mis inversiones", "cómo va mi portafolio", "cómo van mis posiciones"
- El usuario vuelve después de haber recibido un plan de inversión
- Han pasado los hitos del plan (mes 1, 3, 6, 12)
- El usuario reporta que compró, vendió o movió capital
- El usuario pregunta "debo vender?", "rebalanceo?", "qué hago ahora?"

## Fuentes de datos para seguimiento

### Datos en tiempo real (MCP servers)
| Vertical | Server | Qué consultar |
|----------|--------|--------------|
| Acciones/ETFs | Alpha Vantage | Precio actual, cambio %, RSI, MACD |
| Acciones/ETFs | Yahoo Finance | Dividendos pagados, próximo ex-dividend date |
| Cripto spot | CoinGecko | Precio actual, cambio 24h/7d/30d, market cap |
| Cripto spot | Binance | Precio exacto, volumen 24h |
| DeFi yields | DeFiLlama | APY actual del pool, TVL del protocolo |
| Forex | Alpha Vantage | Tipo de cambio actual, tendencia |
| Forex | MetaTrader 5 | Posiciones abiertas, P&L en tiempo real |
| Screener | TradingView | Verificar si algún activo cambió de señal técnica |

### Datos del usuario (preguntar si no los tiene)
El agente NO tiene memoria entre sesiones. Cada vez que el usuario vuelve para seguimiento, necesita saber:
1. Qué posiciones tiene (activo, cantidad, precio de entrada, fecha)
2. En qué plataforma está cada posición (Hapi, Binance, Aave, eToro, MT5)
3. Si hizo cambios desde la última revisión

### Pregunta de onboarding de seguimiento
```
"Para revisar tu portafolio necesito que me digas tus posiciones actuales.
Puedes decirme algo como:
- VOO: compré $150 a $520 el 15 de marzo en Hapi
- ETH: tengo 0.05 ETH en Binance, compré a $3,200
- Aave USDC: deposité $100 en el pool de Polygon
- eToro: copio al trader CryptoKing con $200

Si tienes MetaTrader 5 abierto, puedo consultar tus posiciones forex automáticamente."
```

## Lógica de seguimiento autónomo

### Al recibir las posiciones del usuario
```
POR CADA posición reportada:
  1. Consultar precio actual (MCP server correspondiente)
  2. Calcular:
     - Rendimiento absoluto ($): precio_actual - precio_entrada × cantidad
     - Rendimiento porcentual (%): (precio_actual / precio_entrada - 1) × 100
     - Días desde la compra
     - Rendimiento anualizado: rendimiento% × (365 / días)
  3. Consultar indicadores técnicos actuales (RSI, tendencia)
  4. Comparar rendimiento real vs escenario base del plan original
  5. Evaluar si alguna regla de riesgo se activa (risk_rules.md)

DESPUÉS de evaluar todas las posiciones:
  6. Calcular rendimiento total del portafolio ponderado por peso
  7. Comparar asignación actual vs asignación objetivo
  8. Ejecutar stress_test_portfolio con posiciones actuales
  9. Identificar desviaciones > 5% del peso objetivo
  10. Generar recomendaciones de acción
```

### Alertas automáticas (evaluar SIEMPRE)
```
ALERTA ROJA (acción inmediata recomendada):
  - Posición con pérdida > 15% → "Considerar stop loss"
  - APY de pool DeFi cayó > 50% vs cuando entró → "El rendimiento del pool bajó significativamente"
  - TVL del protocolo DeFi cayó > 30% → "Riesgo de liquidez en el protocolo"
  - RSI > 80 en posición con ganancia > 20% → "Posible toma de ganancias"
  - Trader copiado en eToro con drawdown > 20% → "Considerar dejar de copiar"

ALERTA AMARILLA (monitorear de cerca):
  - Posición con pérdida entre 5-15% → "Normal en corto plazo, pero monitorear"
  - Correlación entre posiciones > 0.7 → "Portafolio poco diversificado"
  - Una vertical tiene > 40% del portafolio → "Sobreexposición"
  - Dividendo ex-date próximo (< 7 días) → "Próximo pago de dividendos"
  - APY del pool cambió > 20% → "Revisar si sigue siendo competitivo"

ALERTA VERDE (todo bien):
  - Rendimiento dentro del rango del escenario base → "En camino según el plan"
  - Asignación dentro de ±5% del objetivo → "Portafolio balanceado"
  - Todos los indicadores técnicos neutros → "Sin señales de alarma"
```

### Decisiones de rebalanceo
```
SI desviación de peso > 5% en alguna vertical:
  → Calcular cuánto mover para volver al peso objetivo
  → Sugerir: "Tu vertical de cripto pasó de 25% a 35%. Considera mover $X de cripto a ETFs"
  → Ejecutar calculate_tax_impact sobre la ganancia realizada si vende

SI una posición subió > 50%:
  → Sugerir toma parcial de ganancias (vender 25-50% de la posición)
  → Reinvertir en la vertical más subponderada
  → "VOO subió 55% desde tu compra. Podrías vender la mitad y reinvertir en cripto que está subponderada"

SI una posición bajó > 20% Y los fundamentales no cambiaron:
  → Evaluar si es oportunidad de DCA (promediar precio)
  → "ETH bajó 22% pero los fundamentales siguen fuertes. Puedes promediar comprando $50 más"
  → Solo sugerir DCA si el usuario tiene capital disponible

SI el usuario tiene capital nuevo ($50/mes de ahorro):
  → Asignar según los pesos objetivo del plan
  → Priorizar la vertical más subponderada
  → "Con tus $50 de ahorro de este mes, te sugiero: $30 a VOO (subponderado) y $20 a staking ETH"
```

## Calendario de seguimiento

### Frecuencias por tipo de activo
```
DIARIO (solo revisar, no actuar):
  - Cripto spot: precio y cambio 24h (alta volatilidad)
  - Forex: posiciones abiertas en MT5 si tiene
  - NO revisar ETFs diariamente (genera ansiedad innecesaria)

SEMANAL (revisar y evaluar):
  - Copy trading: rendimiento del trader, drawdown semanal
  - DeFi yields: APY actual vs APY de entrada
  - Forex: P&L semanal, evaluar cerrar posiciones perdedoras

MENSUAL (revisar, evaluar y actuar):
  - ETFs/acciones: rendimiento mensual, comparar vs benchmark (S&P 500)
  - Ejecutar DCA con ahorro mensual ($50)
  - Rebalancear si desviación > 5%
  - Verificar dividendos recibidos
  - Actualizar el archivo de portafolio

TRIMESTRAL (revisión profunda):
  - Stress test completo del portafolio
  - Evaluar si la estrategia sigue siendo adecuada
  - Comparar rendimiento total vs inflación Colombia
  - Revisar impacto tributario acumulado (calculate_tax_impact)
  - Evaluar cambio de traders en copy trading si rendimiento < benchmark
  - Considerar nuevas oportunidades de inversión

ANUAL:
  - Preparar información para declaración de renta DIAN
  - Consolidar rendimientos por tipo de activo
  - Evaluar cambio de perfil de riesgo
  - Revisar si los objetivos financieros cambiaron
```

### Recordatorios automáticos
```
Cuando el agente genera un plan, SIEMPRE incluir al final:

"PRÓXIMAS REVISIONES:
- Semana que viene: revisa el rendimiento de tu copy trading
- En 30 días: vuelve para tu primera revisión mensual y para invertir tus $50 de ahorro
- En 90 días: haremos un stress test completo de tu portafolio

Escríbeme 'revisa mi portafolio' cuando quieras hacer seguimiento."
```

## Formato del reporte de seguimiento

### Estructura obligatoria del reporte
```
1. RESUMEN EJECUTIVO
   - Rendimiento total del portafolio: +X% ($Y ganancia/pérdida)
   - Días desde inicio del plan
   - Comparación vs benchmark (S&P 500 en el mismo período)

2. POSICIONES INDIVIDUALES
   Por cada posición:
   - Activo | Plataforma | Precio entrada → Precio actual | Rendimiento % | Rendimiento $
   - Indicador técnico actual (RSI, tendencia)
   - Estado: ✅ En plan | ⚠️ Monitorear | 🔴 Acción requerida

3. ALERTAS ACTIVAS
   - Listar alertas rojas y amarillas con acción sugerida

4. ASIGNACIÓN ACTUAL vs OBJETIVO
   - Tabla comparativa de pesos por vertical
   - Desviaciones y acciones correctivas

5. ACCIONES RECOMENDADAS
   - Qué hacer ahora (ordenado por prioridad)
   - Qué monitorear esta semana
   - Cuándo volver para la siguiente revisión

6. IMPACTO FISCAL (si vendió algo)
   - Ganancia/pérdida realizada
   - Impuesto estimado (calculate_tax_impact)
```

## Encadenamiento con otros skills

```
→ Antes del reporte: consultar TODOS los MCP servers relevantes para precios actuales
→ Para cada posición: calculate_risk_score con datos actuales
→ Si sugiere venta: calculate_tax_impact sobre la ganancia
→ Si sugiere rebalanceo: allocate_portfolio con capital actual
→ Si detecta sobreexposición: calculate_correlation entre posiciones
→ Si el portafolio cambió mucho: stress_test_portfolio actualizado
→ Si el usuario pregunta por un activo nuevo: activar el skill de la vertical correspondiente
```

## Adaptación por nivel

### Principiante
```
"Tu portafolio va bien. VOO subió 3% este mes, que es normal para un ETF del S&P 500.
No necesitas hacer nada ahora. El próximo paso es invertir tus $50 de ahorro del mes
en VOO para seguir promediando tu precio de entrada. Vuelve en 30 días para tu
siguiente revisión."
```

### Intermedio
```
"Rendimiento total: +4.2% ($21 sobre $500). Tu ETF de S&P 500 rinde +5.1% y tu staking
de ETH rinde +2.8%. El APY de Aave bajó de 4.5% a 3.2% — todavía es competitivo pero
monitorea. Tu asignación está dentro del rango objetivo. DCA de $50 sugerido: $30 VOO +
$20 ETH staking."
```

### Avanzado
```
"P&L total: +$21.40 (+4.28%, anualizado 18.3%). Sharpe implícito del portafolio: 1.2.
Correlación VOO-QQQ: 0.89 (alta, considerar sustituir QQQ por SCHD para diversificar).
RSI de ETH en 72 — acercándose a sobrecompra, considerar toma parcial si cruza 80.
APY Aave USDC Polygon: 3.2% (era 4.5% al entrar, -28.9%). Stress test: drawdown
estimado en crash moderado: -12.4% ($62)."
```

## Manejo de emociones del usuario

```
SI el usuario dice "todo está cayendo" / "estoy perdiendo mucho":
  → Consultar datos reales inmediatamente (no asumir)
  → Contextualizar: "El mercado general cayó X% hoy. Tu portafolio cayó Y%."
  → Comparar con benchmark: "El S&P 500 también cayó Z% hoy"
  → Recordar horizonte: "Tu plan es a mediano plazo (6-12 meses). Las caídas de corto plazo son normales"
  → NO sugerir venta por pánico
  → SI la caída es > 20%: evaluar objetivamente si los fundamentales cambiaron

SI el usuario dice "quiero vender todo":
  → Preguntar por qué: "¿Necesitas el dinero para algo urgente, o es por la caída del mercado?"
  → Si es por pánico: mostrar datos históricos de recuperación
  → Si necesita liquidez: calcular cuánto vender para cubrir la necesidad, no todo
  → Calcular impacto fiscal de vender (calculate_tax_impact)
  → "Si vendes todo hoy, realizarías una pérdida de $X y pagarías $Y en impuestos"

SI el usuario dice "quiero invertir más" / "tengo más dinero":
  → Preguntar cuánto capital nuevo tiene
  → Evaluar si el portafolio actual está balanceado
  → Asignar capital nuevo a la vertical más subponderada
  → Ejecutar allocate_portfolio con el nuevo capital total
```

## Advertencias obligatorias en cada reporte
- "Este reporte es informativo. No constituye asesoría financiera profesional."
- "Los rendimientos pasados no garantizan rendimientos futuros."
- "Consulta con un asesor financiero certificado antes de tomar decisiones importantes."
