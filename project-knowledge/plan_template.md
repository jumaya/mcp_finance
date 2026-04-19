Template del plan de inversión — v6.2

Rendimiento mínimo por perfil Y capital (escenario BASE, 6 meses)

Los rendimientos mínimos dependen del capital invertido. Con capital bajo, las comisiones, spreads y overnight fees erosionan un porcentaje mayor del rendimiento bruto. Por eso el mínimo se escala por tramos de capital en los tres perfiles.

Todos los mínimos se expresan en rendimiento BASE neto a 6 MESES (no anualizado, después de comisiones, spreads y overnight fees).

RIESGO ALTO (7-10/10):
  Capital < $200:       mínimo +15% base 6M
  Capital $200-500:     mínimo +20% base 6M
  Capital $500-2000:    mínimo +30% base 6M
  Capital > $2000:      mínimo +40% base 6M

RIESGO MODERADO (4-6/10):
  Capital < $200:       mínimo +4%  base 6M
  Capital $200-500:     mínimo +6%  base 6M
  Capital $500-2000:    mínimo +8%  base 6M
  Capital > $2000:      mínimo +12% base 6M

RIESGO BAJO (1-3/10):
  Capital < $200:       mínimo +2% base 6M
  Capital $200-500:     mínimo +3% base 6M
  Capital $500-2000:    mínimo +4% base 6M
  Capital > $2000:      mínimo +5% base 6M

Justificación del escalado:
  - Depósito COP→USD (PSE/tarjeta): costo fijo 1.5-3% independiente del monto → pesa más sobre capital pequeño.
  - Retiro USD→COP: costo fijo ~$5-10 USD → sobre $200 es 2.5-5%, sobre $2000 es 0.25-0.5%.
  - Spreads de eToro/Binance: fijos en pips → consumen fracción mayor del retorno pequeño.
  - Overnight fees CFD: cargo diario en USD → desproporcionado en posiciones pequeñas.
  - Mínimos por posición (eToro $10 spot / $50 CFD / $200 copy): obligan a concentrar más el capital pequeño, subiendo risk score y bajando flexibilidad.

SI el rendimiento base proyectado NO alcanza el mínimo:
  → NO rechazar el plan
  → Incluir nota honesta: "El rendimiento base de +X% está ajustado al capital de $Y. Con mayor capital ($Z+) el rendimiento escala porque las comisiones pesan menos proporcionalmente."
  → NO decir "no alcanza el +30%" si el mínimo correcto es +20% para ese capital
  → NO forzar más riesgo ni más apalancamiento para llegar al mínimo del siguiente tramo: si el mínimo del tramo del usuario se cumple, el plan es válido aunque no llegue al tramo superior.

Límite defensivo (stablecoins + reserva + ETFs broad)
  Bajo: ≤60% | Moderado: ≤30% | Alto: ≤10% | Extremo: ≤5%


ESTRUCTURA JSX OBLIGATORIA — exactamente 4 tabs

El plan JSX DEBE tener EXACTAMENTE estos 4 tabs, en este orden, con estos nombres:
  Tab 1: "📊 Plan"
  Tab 2: "📅 Cronograma"
  Tab 3: "📈 Escenarios"
  Tab 4: "⚠️ Riesgo"

PROHIBIDO:
  - Agregar tabs adicionales (NO crear tab "Intel", "Fiscal", "Detalles", etc.)
  - Cambiar los nombres de los tabs
  - Reorganizar el orden


Contenido de cada tab

Tab 1: "📊 Plan" — Todo el análisis y las posiciones

1. Paso 1: Contexto de mercado (datos MCP con fuente)
2. Paso 2: Asimetrías detectadas (2-3 máximo)
3. Paso 3: Popular investors / Copy trading
4. Paso 4: Las 3 posiciones con detalle completo

Para CADA posición direccional, incluir bloque "Setup técnico" (proveniente de technical_skill.md):
  - Postura (BULLISH/NEUTRAL/BEARISH/sin señal clara)
  - Patrón identificado + divergencias
  - Entrada / SL / TP1 / TP2 con justificación de cada nivel
  - R:R calculado

Para posiciones NO direccionales (stablecoin lending, staking, copy trading), omitir el bloque. Documentar "no aplica análisis técnico".

5. Distribución del capital (barra visual)
6. Resumen por plataforma (eToro / Binance)
  - Capital asignado a cada una
  - Método de depósito recomendado (PSE para Binance, tarjeta para eToro)
  - Costo total de entrada estimado en USD
  - Costo total de salida estimado en USD


Tab 2: "📅 Cronograma" — Plan semanal del Mes 1

  Semana 1: Setup + primeras compras (día a día)
  Semana 2: Revisión y ajustes
  Semana 3: Refuerzo o nuevas entradas
  Semana 4: Evaluación y rebalanceo

INCLUIR: earnings dates de acciones en el portafolio como hitos.


Tab 3: "📈 Escenarios" — Tablas a 3M y 6M + honestidad sobre rendimiento

1. Nota de honestidad sobre rendimiento objetivo vs realista
  - Indicar explícitamente el tramo de capital del usuario y el mínimo del tramo.
  - Si base < mínimo del tramo superior, explicar que mover al tramo superior requiere más capital, NO más riesgo.
2. Tabla escenarios a 3 meses (optimista/base/pesimista con razones)
3. Tabla escenarios a 6 meses (optimista/base/pesimista con razones)
4. Impacto fiscal Colombia (resumen por tipo de activo)


Tab 4: "⚠️ Riesgo" — Stress test + validación + disclaimers

1. Stress test: crash moderado (-20%) y severo (-40%) con montos
2. Correlación entre posiciones
3. Checks de validación (concentración, defensivo, tolerancia)
4. Reglas de protección y triggers de salida
5. Costos totales desglosados
6. Disclaimers obligatorios


REGLAS DE FORMATO NUMÉRICO

Risk scores — SIEMPRE mostrar como texto visible:
  CORRECTO: "8.0/10 — ALTO" (número + barra visual al lado)
  INCORRECTO: solo barra gráfica sin número

Escenarios — SIEMPRE mostrar porcentaje Y monto:
  CORRECTO: "🟢 Optimista (25%): +80.0% → $315.00"

Stress test — SIEMPRE diferenciar escenarios:
  CORRECTO: Moderado $163 (-18%) vs Severo $113 (-43%)

Overnight fees — SIEMPRE incluir en posiciones CFD:
  CORRECTO: "Overnight: ~$1.58/mes ($9.48 en 6M)"

Fuentes — SIEMPRE indicar:
  CORRECTO: "$72,182 (via CoinGecko)"

Rendimiento mínimo — SIEMPRE mostrar el tramo aplicado:
  CORRECTO: "Capital $350 (tramo $200-500, riesgo alto) → mínimo +20% base 6M. Plan proyecta +24% base ✅"
  INCORRECTO: "Plan proyecta +24% ✅" (sin mostrar el tramo)


Checklist de calidad (verificar ANTES de generar JSX)

□ ¿Exactamente 4 tabs con los nombres correctos?
□ ¿NO hay tabs adicionales?
□ ¿Precios reales via MCP con fuente indicada?
□ ¿Tesis específica por posición (no genérica)?
□ ¿Catalizador con fecha por posición?
□ ¿SL y TP por posición?
□ ¿Risk score como NÚMERO visible X.X/10?
□ ¿Escenarios con % y $ en texto visible?
□ ¿Overnight fees en posiciones CFD?
□ ¿Stress test con escenarios diferenciados (verticales correctos)?
□ ¿Copy trading incluido como posición (si eToro)?
□ ¿Correlación calculada?
□ ¿Tramo de capital y perfil de riesgo identificados explícitamente en Tab 3?
□ ¿Rendimiento base ≥ mínimo del tramo correcto (capital + riesgo)?
□ ¿Si base < mínimo del tramo superior, se aclara que es por el capital, NO por riesgo del plan?
□ ¿% defensivo ≤ límite del perfil?
□ ¿Cada posición cumple el mínimo de su venue (platforms_skill §4)?
□ ¿Costos de entrada/salida (depósito CO + spread + retiro) están descontados del rendimiento base presentado?
□ ¿Checkpoints ✅ visibles?
□ ¿Disclaimers al final?
□ ¿Cada posición direccional tiene bloque "Setup técnico" con SL/TP derivados de technical_skill.md?
□ ¿El R:R técnico por posición es ≥ 1:1.5 (equity/cripto) o ≥ 1:2 (forex)? Si alguna posición queda por debajo, ¿está marcada explícitamente?
□ ¿La modulación del cronograma (Tab 2) refleja la postura técnica? (Bullish → entrada Semana 1; Neutral → 50/50 S1-S2; Bearish → 33/resto condicionado)
□ ¿Los SL técnicos aparecen también en el Tab 4 como triggers de salida?
