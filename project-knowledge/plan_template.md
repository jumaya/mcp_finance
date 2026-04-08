# Template del plan de inversión — v3

## Regla de rendimiento mínimo por perfil
```
El plan DEBE proyectar al menos este rendimiento en escenario BASE a 6 meses:
  Riesgo bajo: +4% a +8%
  Riesgo moderado: +10% a +20%
  Riesgo alto: +30% a +60%
  Riesgo extremo: +40% a +200%

SI el rendimiento proyectado está DEBAJO del mínimo:
  → Aumentar activos volátiles
  → Agregar apalancamiento 2x
  → Reducir stablecoins/reserva
  → Incluir copy trading agresivo
```

## Límite de posiciones defensivas por perfil
```
Defensivo = USDC lending + reserva + stablecoins + ETFs broad (VOO/VT)

  Riesgo bajo: hasta 60% defensivo
  Riesgo moderado: hasta 30%
  Riesgo alto: MÁXIMO 10%
  Riesgo extremo: MÁXIMO 5%
```

## Secciones obligatorias (10)

### 1. Contexto de mercado
Datos reales de MCP. RSI S&P 500, BTC precio/dominancia, narrativas, conclusión.

### 2. Asimetrías detectadas
Del Paso 2 del orquestador. Oportunidades que el mercado no ha corregido.

### 3. Popular investors (si usa eToro)
Del Paso 3. Nombres reales, rendimiento, risk score.

### 4. Posiciones con tesis completa
Por cada posición: ticker, plataforma, monto, tipo, precio actual, RSI, tesis (no genérica), catalizador con fecha, riesgo específico, entrada, SL, TP1, TP2, escenarios, risk score, impuesto CO.

### 5. Distribución por vertical
Tabla con % por categoría. Verificar que defensivo no exceda el límite.

### 6. Escenarios a 3 y 6 meses
Tablas separadas con: escenario, rendimiento mensual, capital final, probabilidad, razón específica.

### 7. Cronograma semanal Mes 1
Semana 1: setup + primeras compras (día por día)
Semana 2: revisión y ajustes
Semana 3: refuerzo o nuevas entradas
Semana 4: evaluación y rebalanceo

### 8. Stress test
Crash moderado (-20%) y severo (-40%) con valores en dólares por posición.

### 9. Impacto fiscal Colombia
calculate_tax_impact por tipo de activo. Montos estimados.

### 10. Seguimiento + Disclaimers
Calendario de revisión (tracking_skill.md). Disclaimers obligatorios.

## Checklist de calidad (verificar ANTES de presentar)
```
□ ¿Todos los precios son reales (via MCP)?
□ ¿Cada posición tiene tesis específica (no genérica)?
□ ¿Cada posición tiene catalizador con fecha?
□ ¿Cada posición tiene SL y TP?
□ ¿Los escenarios tienen razones específicas?
□ ¿El % defensivo no excede el límite del perfil?
□ ¿El rendimiento base cumple el mínimo del perfil?
□ ¿Se ejecutó stress_test?
□ ¿Se calculó tax_impact?
□ ¿Se incluyó copy trading (si eToro)?
□ ¿Se consultaron popular investors reales?
□ ¿El contexto de mercado está al inicio?
□ ¿NO hay activos conservadores para perfil agresivo?
□ ¿Hay checkpoints ✅ visibles después de cada paso?
```
