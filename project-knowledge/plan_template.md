# Template del plan de inversión — v2

## Cuándo se activa
SIEMPRE que el agente genera un plan de inversión completo. Este template define la estructura obligatoria y las reglas de calidad.

## Regla de oro: el plan debe ser PROPORCIONAL al riesgo declarado
```
SI el usuario dice "riesgo alto" y el plan proyecta < 20% de ganancia en escenario base a 6 meses:
  → EL PLAN ES DEMASIADO CONSERVADOR → RECALIBRAR

Rendimientos MÍNIMOS esperados por perfil (escenario base, 6 meses):
  - Riesgo bajo: +3% a +8% (conservar capital + algo de crecimiento)
  - Riesgo moderado: +8% a +20% (crecimiento con control)
  - Riesgo alto: +20% a +60% (crecimiento agresivo, acepta volatilidad)
  - Riesgo extremo: +40% a +200% (acepta pérdida total)

SI los rendimientos proyectados están DEBAJO del mínimo para el perfil:
  → Aumentar exposición a activos volátiles
  → Agregar apalancamiento (2x-5x según perfil)
  → Reducir posiciones defensivas (USDC, stablecoins)
  → Incluir copy trading agresivo
```

## Regla de asignación defensiva máxima por perfil
```
Posiciones defensivas = USDC lending + reserva líquida + stablecoins + ETFs broad index

  - Riesgo bajo: hasta 60% defensivo permitido
  - Riesgo moderado: hasta 30% defensivo permitido
  - Riesgo alto: MÁXIMO 10% defensivo
  - Riesgo extremo: MÁXIMO 5% defensivo

SI el plan tiene más % defensivo que el permitido:
  → REASIGNAR el exceso a posiciones de crecimiento
  → Ejemplo: perfil alto con 25% en USDC → reducir a 10% → mover 15% a altcoins o copy trading
```

## Secciones obligatorias del plan (10)

### 1. CONTEXTO DE MERCADO (nuevo en v2)
```
ANTES de las posiciones, presentar:
- Estado del mercado general (bull/bear/neutral) con datos reales
- RSI del S&P 500 y BTC
- Narrativas dominantes del momento
- Eventos próximos que pueden mover el mercado
- POR QUÉ es buen momento (o no) para invertir
- SI no es buen momento: decirlo honestamente y sugerir esperar
```

### 2. RESUMEN EJECUTIVO
- Capital total
- Perfil de riesgo
- Número de posiciones
- Rendimiento esperado en escenario base (debe cumplir el mínimo del perfil)
- Riesgo ponderado del portafolio (score 1-10)
- Plataformas utilizadas

### 3. DISTRIBUCIÓN POR VERTICAL
- Tabla con % por vertical (equity, cripto, DeFi, copy trading, forex)
- Verificar que % defensivo no exceda el máximo del perfil
- Para riesgo alto: mostrar que >90% está en activos de crecimiento

### 4. POSICIONES INDIVIDUALES (con tesis, NO genérico)
```
POR CADA posición:
  a) NOMBRE + PLATAFORMA
  b) MONTO EXACTO ($) y PESO (%)
  c) PRECIO ACTUAL (datos reales de MCP)
  d) TESIS DE INVERSIÓN (2-3 oraciones, POR QUÉ este activo)
  e) CATALIZADOR (qué evento puede mover el precio Y CUÁNDO)
  f) RIESGO ESPECÍFICO (no "puede bajar" — sino "si X pasa, cae a $Y")
  g) ENTRADA (precio exacto: market order o limit a $X)
  h) STOP LOSS (precio exacto)
  i) TAKE PROFIT 1 y 2 (precios exactos)
  j) INDICADORES TÉCNICOS (RSI, tendencia, soporte/resistencia)
  k) RISK SCORE (calculate_risk_score)

PARA RIESGO ALTO, incluir adicionalmente:
  l) APALANCAMIENTO sugerido (si aplica)
  m) BETA vs mercado (cuánto se mueve vs S&P 500)
  n) UPSIDE ASIMÉTRICO: relación ganancia/pérdida potencial
```

### 5. COPY TRADING (obligatorio si usa eToro y capital >= $200)
```
Para riesgo alto en eToro:
  - Buscar popular investors con rendimiento > 25% anual
  - Mostrar: nombre, rendimiento 12M, drawdown, # copiadores
  - Distribuir entre 2-3 traders diferentes
  - Explicar por qué cada trader fue seleccionado
  - Asignar mínimo 15-20% del capital a copy trading

SI el agente NO incluye copy trading para riesgo alto en eToro:
  → EL PLAN ESTÁ INCOMPLETO → agregar esta sección
```

### 6. ESCENARIOS (3 obligatorios con contexto)
```
NO usar escenarios genéricos. Cada escenario debe tener una RAZÓN:

  Optimista (25% prob): "Si [evento específico] ocurre → portafolio llega a $X (+Y%)"
  Base (50% prob): "Si el mercado se mantiene en [estado actual] → portafolio llega a $X (+Y%)"
  Pesimista (25% prob): "Si [riesgo específico] se materializa → portafolio cae a $X (-Y%)"

VERIFICAR que:
  - Escenario base cumple el rendimiento mínimo del perfil
  - Escenario pesimista no excede la tolerancia declarada del usuario
  - Escenario optimista refleja el upside real de los activos seleccionados
```

### 7. CRONOGRAMA DETALLADO
```
Semana 1: paso a paso día por día (con tiempos estimados)
Semana 2-4: revisiones semanales
Mes 2-3: hitos mensuales
Mes 4-6: revisión trimestral

INCLUIR:
  - Cuándo ejecutar DCA con ahorro mensual
  - Cuándo revisar posiciones (tracking_skill.md)
  - Cuándo evaluar rebalanceo
  - Fechas de earnings de acciones en el portafolio
```

### 8. STRESS TEST
```
Ejecutar stress_test_portfolio con:
  - Crash moderado (-20%)
  - Crash severo (-40%)
  - Crypto winter (-60% solo en cripto)

Mostrar:
  - Valor del portafolio en cada escenario
  - Qué posiciones pierden más
  - Qué posiciones protegen (si hay)
  - Plan de acción en caso de crash (comprar más? vender? mantener?)
```

### 9. IMPACTO FISCAL
```
calculate_tax_impact para cada tipo de ganancia:
  - Trading cripto: 15% ganancia ocasional
  - Dividendos USA: retención + renta fuente extranjera
  - DeFi yields: ganancia ocasional al realizar
  - Copy trading: renta fuente extranjera

Incluir montos estimados en pesos colombianos
```

### 10. DISCLAIMERS
- No es asesoría financiera profesional
- Rendimientos pasados no garantizan futuros
- Todas las inversiones conllevan riesgo
- Consultar asesor financiero
- Fecha de los datos de mercado

## Checklist de calidad (el agente verifica ANTES de presentar)
```
□ ¿Todos los precios son reales y actuales (via MCP)?
□ ¿Cada posición tiene tesis de inversión (no genérica)?
□ ¿Cada posición tiene catalizador con fecha?
□ ¿Cada posición tiene entrada, SL y TP específicos?
□ ¿Los escenarios tienen razones, no solo números?
□ ¿El % defensivo no excede el máximo del perfil?
□ ¿El rendimiento base cumple el mínimo del perfil?
□ ¿Se ejecutó stress_test_portfolio?
□ ¿Se calculó calculate_tax_impact?
□ ¿Se incluyó copy trading (si aplica)?
□ ¿El contexto de mercado está al inicio?
□ ¿Hay cronograma detallado?
□ ¿NO se recomiendan activos conservadores a perfil agresivo?
```
