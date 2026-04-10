# Template del plan de inversión — v6

## Rendimiento mínimo por perfil (escenario BASE, 6 meses)
```
Bajo: +4-8% | Moderado: +10-20% | Alto: +30-60% | Extremo: +40-200%
```

## Límite defensivo (stablecoins + reserva + ETFs broad)
```
Bajo: ≤60% | Moderado: ≤30% | Alto: ≤10% | Extremo: ≤5%
```

## ESTRUCTURA JSX OBLIGATORIA — exactamente 4 tabs
```
El plan JSX DEBE tener EXACTAMENTE estos 4 tabs, en este orden, con estos nombres:

  Tab 1: "📊 Plan"
  Tab 2: "📅 Cronograma"
  Tab 3: "📈 Escenarios"
  Tab 4: "⚠️ Riesgo"

PROHIBIDO:
  - Agregar tabs adicionales (NO crear tab "Intel", "Fiscal", "Detalles", etc.)
  - Cambiar los nombres de los tabs
  - Reorganizar el orden

Si hay información extra (earnings history, DEX volumes, trending cripto):
  → Incluirla DENTRO del Tab 1 "Plan" como parte del contexto de mercado
  → O NO incluirla si no es esencial para la decisión de inversión
```

## Contenido de cada tab

### Tab 1: "📊 Plan" — Todo el análisis y las posiciones
```
Orden de secciones dentro del tab:
  1. Paso 1: Contexto de mercado (datos MCP con fuente)
  2. Paso 2: Asimetrías detectadas (2-3 máximo)
  3. Paso 3: Popular investors / Copy trading
  4. Paso 4: Las 3 posiciones con detalle completo
  5. Distribución del capital (barra visual)
  6. Resumen por plataforma (eToro / Binance)
```

### Tab 2: "📅 Cronograma" — Plan semanal del Mes 1
```
  Semana 1: Setup + primeras compras (día a día)
  Semana 2: Revisión y ajustes
  Semana 3: Refuerzo o nuevas entradas
  Semana 4: Evaluación y rebalanceo
  
  INCLUIR: earnings dates de acciones en el portafolio como hitos
```

### Tab 3: "📈 Escenarios" — Tablas a 3M y 6M + honestidad sobre rendimiento
```
  1. Nota de honestidad sobre rendimiento mensual objetivo vs realista
  2. Tabla escenarios a 3 meses (optimista/base/pesimista con razones)
  3. Tabla escenarios a 6 meses (optimista/base/pesimista con razones)
  4. Impacto fiscal Colombia (resumen por tipo de activo)
```

### Tab 4: "⚠️ Riesgo" — Stress test + validación + disclaimers
```
  1. Stress test: crash moderado (-20%) y severo (-40%) con montos
  2. Correlación entre posiciones
  3. Checks de validación (concentración, defensivo, tolerancia)
  4. Reglas de protección y triggers de salida
  5. Disclaimers obligatorios
```

## REGLAS DE FORMATO NUMÉRICO
```
Risk scores — SIEMPRE mostrar como texto visible:
  CORRECTO: "8.0/10 — ALTO" (número + barra visual al lado)
  INCORRECTO: solo barra gráfica sin número

Escenarios — SIEMPRE mostrar porcentaje Y monto:
  CORRECTO: "🟢 Optimista (25%): +80.0% → $315.00"
  INCORRECTO: solo barra de color sin números

Stress test — SIEMPRE diferenciar escenarios:
  CORRECTO: Moderado $385 (-22.9%) vs Severo $270 (-46.0%)
  INCORRECTO: mismo resultado para todos los escenarios

Overnight fees — SIEMPRE incluir en posiciones CFD:
  CORRECTO: "Overnight: ~$1.58/mes ($9.48 en 6M)"
  
Fuentes — SIEMPRE indicar:
  CORRECTO: "$72,182 (via CoinGecko)"
  INCORRECTO: "$72,182" sin fuente
```

## Checklist de calidad (verificar ANTES de generar JSX)
```
□ ¿Exactamente 4 tabs con los nombres correctos?
□ ¿NO hay tabs adicionales?
□ ¿Precios reales via MCP con fuente indicada?
□ ¿Tesis específica por posición (no genérica)?
□ ¿Catalizador con fecha por posición?
□ ¿SL y TP por posición?
□ ¿Risk score como NÚMERO visible X.X/10?
□ ¿Escenarios con % y $ en texto visible?
□ ¿Overnight fees en posiciones CFD?
□ ¿Stress test con escenarios diferenciados?
□ ¿Copy trading incluido como posición (si eToro)?
□ ¿Correlación calculada?
□ ¿Rendimiento base ≥ mínimo del perfil?
□ ¿% defensivo ≤ límite del perfil?
□ ¿Checkpoints ✅ visibles?
□ ¿Disclaimers al final?
```
