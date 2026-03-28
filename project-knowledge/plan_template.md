# Skill: Agente de generación de plan — Template autónomo

## Cuándo se activa
AUTOMÁTICAMENTE después de que:
- Se completaron los cálculos de todas las posiciones (escenarios, riesgo, impuestos)
- El risk_rules.md validó y ajustó la asignación
- El stress test se ejecutó

## Lógica de generación autónoma

### Decisión de profundidad
```
SI principiante:
  → Plan COMPLETO con todas las secciones
  → Explicaciones largas con analogías
  → Cronograma día por día con tiempos en minutos
  → Incluir sección "qué NO hacer" (no vender por pánico, no revisar cada hora)

SI intermedio:
  → Plan completo pero explicaciones más concisas
  → Cronograma por semana, no por día
  → Incluir opciones de estrategias avanzadas como "siguiente paso"

SI avanzado:
  → Plan técnico con métricas detalladas
  → Incluir tablas de correlación, Sharpe ratio estimado
  → Opciones de composición y apalancamiento
```

### Auto-ajuste de moneda
```
SI el usuario dio su capital en COP:
  → Convertir a USD para los cálculos
  → Mostrar AMBAS monedas en el plan: "$150 USD (~$630,000 COP)"
  → Usar tasa de cambio actual (consultar o usar default 4200)

SI el usuario dio en USD:
  → Calcular en USD
  → Agregar equivalente COP en la primera mención para contexto
```

## Estructura obligatoria del plan

### 1. RESUMEN EJECUTIVO
```
Generar automáticamente 3-4 oraciones que incluyan:
- Cuánto invierte total
- En cuántas posiciones
- Rango de ingreso pasivo mensual estimado (del resultado de calculate_scenarios)
- Nivel de riesgo en lenguaje simple

Ejemplo para principiante:
"Con tus $500 distribuidos en 4 posiciones — fondos americanos, dólares digitales generando intereses, y una reserva líquida — podrías generar entre $2 y $5 al mes en ingresos pasivos. El riesgo es moderado (4.5/10): en el peor escenario realista perderías ~$60, pero tus dólares digitales no se ven afectados."

Ejemplo para avanzado:
"Portafolio de $500 en 5 posiciones cross-vertical: equity 40% (VOO+SCHD), DeFi 25% (USDC lending + ETH staking), social 15% (copy moderate), reserva 10%. Expected monthly yield: $2.80-$5.20. Portfolio risk score: 4.5/10. Max drawdown escenario moderado: -12.3%."
```

### 2. PLATAFORMAS A CONFIGURAR
```
PARA cada plataforma en el plan:
  → Auto-generar ficha con:
    - Nombre y URL
    - Para qué la necesita (contextual a SUS posiciones)
    - Pasos numerados de registro (máximo 5 pasos)
    - Depósito desde Colombia: método + costo
    - Configuraciones importantes (W-8BEN si aplica)
    - Tiempo estimado total

Orden de prioridad:
  1ro: la plataforma con más posiciones (generalmente Hapi o Binance)
  2do: las demás por orden cronológico
```

### 3. POSICIONES DEL PORTAFOLIO
```
PARA CADA posición, incluir esta ficha completa:

[NOMBRE DEL ACTIVO] — [riesgo X/10]
├── Qué es: [1-2 oraciones, adaptado al nivel del usuario]
├── Por qué está en tu plan: [justificación personalizada]
├── Cuánto invertir: $X USD (Y% del portafolio)
├── Rendimiento esperado:
│   ├── Optimista (25% prob): +$A (+B%)
│   ├── Base (50% prob): +$C (+D%)
│   └── Pesimista (25% prob): -$E (-F%)
├── Ingreso pasivo: $G/mes neto (después de impuestos)
├── Riesgo: score H/10 — [warnings si hay]
├── Impuestos: retención X%, tasa efectiva Y%, neto $Z por cada $1 ganado
├── Plataforma: [nombre]
└── Alerta de salida: "Te avisaré si cae más de X%"

SI risk_score > 6: agregar recuadro de advertencia
SI tiene W-8BEN applicable: agregar nota URGENTE
SI tiene impermanent loss risk: explicar específicamente
```

### 4. PLAN SEMANAL (primer mes)
```
Auto-generar cronograma según las plataformas del plan:

SEMANA 1: "Setup y primera inversión"
  → Listar cada acción día por día
  → Incluir tiempo estimado y costo
  → SI principiante: agregar capturas de pantalla mentales ("verás un botón que dice...")
  → Total capital desplegado esta semana: $X

SEMANA 2: "Verificación y configuración"
  → Verificar posiciones activas
  → Configurar alertas de precio
  → Llenar W-8BEN si aplica
  → Total tiempo: ~30 minutos

SEMANA 3-4: "No hacer nada"
  → ENFATIZAR: "La tentación de revisar cada hora es normal. Resiste."
  → "Tu plan está diseñado para funcionar automáticamente"
  → "Si algo importante pasa, el sistema te avisará con las alertas"
  → "Tu único trabajo: depositar los $[monthly_savings] del próximo mes"
```

### 5. RESUMEN FINANCIERO
```
Auto-generar tabla con:

| Concepto | Monto |
|----------|-------|
| Capital invertido | $X |
| Costos de setup | -$Y (comisiones, spreads, gas) |
| Capital efectivo | $Z |
| Ingreso pasivo mensual est. | $A - $B |

Escenarios a 6 meses (usar calculate_scenarios a nivel portafolio):
| Escenario | Prob. | Valor portafolio | Ganancia |
|-----------|-------|-----------------|----------|
| Optimista | 25% | $X | +$Y |
| Base | 50% | $X | +$Y |
| Pesimista | 25% | $X | -$Y |

Comparaciones (auto-calcular):
  → "En un CDT al 10% habrías ganado $[capital × 0.10 / 12 × meses]"
  → "En cuenta de ahorros al 1% habrías ganado $[capital × 0.01 / 12 × meses]"
  → "Tu plan proyecta $[expected] — [X]x más que el CDT"
```

### 6. STRESS TEST
```
→ Resultado de stress_test_portfolio("moderate_crash")
→ Presentar en lenguaje simple:

"¿Qué pasa si los mercados caen?"
"En una caída moderada (similar a correcciones históricas), tu portafolio de $X bajaría a $Y (-Z%)."
"PERO: tus $[stablecoin_amount] en stablecoins ($[surviving_income]/mes) NO se ven afectados porque los dólares digitales mantienen su valor."
"Históricamente, estas caídas se recuperan en 12-24 meses si mantienes la inversión."
```

### 7. HITOS PROGRAMADOS
```
Auto-generar basado en el plan:

Mes 1: "Primer review"
  → Revisar rendimiento real vs proyectado
  → Preguntar: "¿Cómo te sientes con los movimientos que viste?"
  → SI el usuario se estresó: considerar reducir riesgo en la siguiente iteración

Mes 2: "Evaluación de expansión"
  → SI tiene capital acumulado: evaluar agregar nueva vertical
  → SI copy trading estaba pendiente (eToro min $200): evaluar si ya puede

Mes 3: "Primer rebalanceo"
  → Comparar pesos actuales vs objetivo
  → SI desviación > 5%: sugerir vender lo sobrante, comprar lo faltante
  → Ejecutar stress_test con portafolio actualizado

Mes 6: "Revisión mayor"
  → Comparar real vs proyectado completo
  → Generar plan v2 con nuevos datos de mercado
  → Evaluar estrategias avanzadas si el usuario progresó
```

### 8. ACCIONES FISCALES
```
Auto-generar de los resultados de calculate_tax_impact:

Lista concreta:
□ [URGENTE si aplica] Llenar W-8BEN en [plataforma] — 5 minutos
□ Crear archivo/spreadsheet para registro de compras y ventas
□ Guardar estados de cuenta mensuales de cada plataforma
□ [Si supera umbral] Agendar cita con contador en enero
□ [Siempre] Reportar activos en el exterior en declaración de renta
```

### 9. DISCLAIMERS
```
Incluir SIEMPRE al final:
- "Este plan no constituye asesoría financiera profesional."
- "Todas las inversiones conllevan riesgo de pérdida de capital."
- "Los rendimientos pasados no garantizan rendimientos futuros."
- "Consulta con un asesor financiero y un contador antes de invertir."
- "Los datos de mercado son del momento de generación y pueden cambiar."
```

### 10. PRÓXIMO PASO CONCRETO
```
Terminar SIEMPRE con UNA acción específica:

SI no tiene ninguna plataforma:
  "Tu primer paso: descarga Hapi en tu celular y regístrate con tu cédula. Toma 5 minutos. Cuando lo tengas, dime y seguimos."

SI ya tiene plataforma pero no ha invertido:
  "Tu primer paso: deposita $[amount] en [plataforma] via [método]. Cuando esté acreditado, me dices y hacemos la primera compra juntos."

SI ya invirtió y vuelve:
  "Cuéntame: ¿seguiste el plan? ¿Cómo van tus posiciones? Con esos datos puedo actualizar tu plan."
```

## Regla de calidad final
```
ANTES de presentar el plan, verificar:
□ ¿Cada posición tiene 3 escenarios? Si no → ejecutar calculate_scenarios
□ ¿Cada posición tiene risk score? Si no → ejecutar calculate_risk_score
□ ¿Cada posición tiene impacto fiscal? Si no → ejecutar calculate_tax_impact
□ ¿Se ejecutó stress_test? Si no → ejecutar
□ ¿El risk score ponderado es < 7? Si no → ajustar según risk_rules.md
□ ¿Hay cronograma semanal? Si no → generar
□ ¿Hay disclaimers? Si no → agregar
□ ¿Termina con próximo paso concreto? Si no → agregar

Si falta cualquiera → completar ANTES de presentar. No presentar planes incompletos.
```
