# Template: estructura del plan de inversión

## Instrucción
Sigue EXACTAMENTE esta estructura al generar un plan. No omitas secciones. Si faltan datos, indica qué falta.

## Secciones obligatorias

### 1. RESUMEN EJECUTIVO (3-4 oraciones, cero jerga)
Cuánto invierte, en qué, cuánto puede esperar ganar, nivel de riesgo en lenguaje simple.
Ejemplo: "Con $500 distribuidos entre fondos americanos y dólares digitales generando intereses, podrías ganar entre $2 y $5 al mes. En el peor escenario perderías $50-$80, pero tus dólares digitales no se ven afectados."

### 2. PLATAFORMAS A CONFIGURAR
Por cada plataforma: nombre, URL, para qué, pasos numerados de registro, depósito desde Colombia, costo, configs importantes (W-8BEN), tiempo estimado.

### 3. POSICIONES DEL PORTAFOLIO
Por CADA posición:
- Qué es (1-2 oraciones para principiante)
- Por qué está en tu plan (justificación personalizada)
- Cuánto invertir (USD + % portafolio)
- Rendimiento: resultado de `calculate_scenarios` (3 escenarios)
- Riesgo: resultado de `calculate_risk_score` (score + warnings)
- Impuestos: resultado de `calculate_tax_impact` (retención, tasa, acciones)
- Ingreso pasivo: frecuencia y monto neto
- Cuándo salir: triggers de alerta

### 4. PLAN SEMANAL (primer mes)
- Semana 1: Setup plataformas + depósito + primeras compras
- Semana 2: Verificación + configs (W-8BEN, alertas)
- Semana 3-4: No hacer nada (enfatizar que NO tocar es parte del plan)
Cada paso: día, acción, plataforma, minutos, costo.

### 5. RESUMEN FINANCIERO
- Capital invertido total
- Costos de setup
- Capital efectivo
- Ingreso pasivo mensual (rango)
- Escenarios portafolio total (`calculate_scenarios` a nivel portafolio)
- Comparación: "En un CDT al 10% habrías ganado $X" / "En cuenta de ahorros $X"

### 6. STRESS TEST
Resultado de `stress_test_portfolio` escenario "moderate_crash":
- "Tu portafolio de $X bajaría a $Y"
- "Tu ingreso de stablecoins ($Z/mes) NO se afecta"

### 7. HITOS PROGRAMADOS
- Mes 1: reporte + cómo te sientes
- Mes 2: evaluar expansión a nuevas verticales
- Mes 3: primer rebalanceo
- Mes 6: revisión mayor, generar plan fase 2

### 8. ACCIONES FISCALES
Lista concreta: W-8BEN, registro compras/ventas, fecha declaración, si necesita contador.

### 9. DISCLAIMERS
- No es asesoría financiera profesional
- Toda inversión tiene riesgo de pérdida
- Rendimientos pasados no garantizan futuros
- Consultar asesor financiero

### 10. PRÓXIMO PASO
Exactamente qué hacer ahora: "Descarga Hapi y regístrate. Toma 5 minutos. Cuando lo tengas, me avisas."
