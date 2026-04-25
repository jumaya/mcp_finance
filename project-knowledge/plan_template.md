Template del plan de inversión — v7.0 (entrega como artifact JSX)

CAMBIO MAYOR vs v6.2: el plan ya NO se entrega como texto/markdown en chat. Se entrega
SIEMPRE como un **artifact JSX** (componente React con tabs interactivos), creado con
la herramienta de creación de artifacts de Claude. El chat solo lleva una línea breve
introduciendo el artifact ("Aquí está tu plan — abre las pestañas para revisar cada
sección"). Todo el contenido del plan (análisis, posiciones, cronograma, escenarios,
riesgo, BASELINE) vive dentro del artifact.

Esto NO cambia ningún chequeo de fondo (B1–B13 siguen aplicando, todos los datos
siguen viniendo de tools reales, nunca inventados). Solo cambia el medio de entrega.


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


═══════════════════════════════════════════════════════════════
ENTREGA OBLIGATORIA: ARTIFACT JSX (no texto en chat)
═══════════════════════════════════════════════════════════════

El plan se entrega SIEMPRE como un artifact de tipo `application/vnd.ant.react`
(extensión `.jsx`, archivo de salida) creado con la tool de artifacts. NUNCA como
texto plano, markdown, ni JSON en el chat.

Nombre sugerido del artifact: `investment_plan_<YYYYMMDD>.jsx`
Identifier sugerido: `investment-plan`

En el chat, antes/después del artifact, máximo 2-3 líneas:
  - Antes: "Aquí está tu plan de inversión. Abre las pestañas para revisar cada sección.
    Al final del tab ⚠️ Riesgo encontrarás el BASELINE para hacer seguimiento."
  - Después (opcional): cualquier nota crítica que el usuario deba leer ANTES de abrir
    el artifact (ej. "Tu capital alcanzó solo para 2 verticales en lugar de 3 — el plan
    lo refleja"). Sin esto, no añadir relleno.

Si por alguna razón Claude no puede crear artifacts en este entorno (cliente que no
los soporta), entregar el código JSX completo en un bloque ```jsx en chat con la nota
"Copia este componente en un archivo .jsx" y avisar que el modo gráfico requiere un
cliente con soporte de artifacts React.


ESTRUCTURA JSX OBLIGATORIA — exactamente 4 tabs

El componente React DEBE tener EXACTAMENTE estos 4 tabs, en este orden, con estos nombres:
  Tab 1: "📊 Plan"
  Tab 2: "📅 Cronograma"
  Tab 3: "📈 Escenarios"
  Tab 4: "⚠️ Riesgo"

PROHIBIDO:
  - Agregar tabs adicionales (NO crear tab "Intel", "Fiscal", "Detalles", etc.)
  - Cambiar los nombres de los tabs
  - Reorganizar el orden


═══════════════════════════════════════════════════════════════
ESQUELETO JSX DEL COMPONENTE (copia y rellena con datos REALES)
═══════════════════════════════════════════════════════════════

Reglas de rendering:

1. Componente funcional, default export, sin props requeridas.
2. Tabs con `useState` (state local). NO usar `localStorage` ni `sessionStorage` —
   no están soportados en artifacts y romperá el componente.
3. Estilo: clases utilitarias estilo Tailwind (las del runtime de artifacts soportan
   solo el set core de Tailwind — no inventar clases custom como `bg-brand-500`).
4. Diseño moderno, oscuro por defecto, con acentos de color por categoría:
   - Plan / posiciones: slate-900 fondo, accent emerald-400
   - Cronograma: accent sky-400
   - Escenarios: accent amber-400 (optimista emerald, base sky, pesimista rose)
   - Riesgo: accent rose-400
5. Tipografía: stack de sistema (`font-sans` + `font-mono` para números). NO importar
   fuentes externas de Google: el runtime de artifacts no las descarga. NO usar Inter
   ni similares por consistencia con la guía de frontend-design.
6. Mostrar TODOS los datos crudos en texto visible. Si hay barra de progreso,
   acompañarla del número (ej. "8.0/10 — ALTO" + barra al lado, no solo barra).
7. El BASELINE JSON va en un `<pre>` con un botón "Copiar" implementado con
   `navigator.clipboard.writeText(JSON.stringify(baseline, null, 2))`. Si la API no
   está disponible, dejar el `<pre>` seleccionable para copia manual.
8. NO imports que no estén disponibles en el runtime: solo `react`, y opcionalmente
   `lucide-react` para iconos y `recharts` para charts.

Esqueleto base (rellenar `data` con los valores REALES calculados por las tools):

```jsx
import { useState } from "react";

const data = {
  meta: {
    fecha: "DD-MM-AAAA",          // del momento de generación
    capital_total_usd: 0,          // del input del usuario
    perfil_riesgo: "moderado",     // declarado por el usuario
    horizonte_meses: 6,
    tramo_capital: "$200-500",     // calculado en Fase 4
    minimo_aplicable_pct: 6,       // tabla plan_template, del tramo + perfil
    rendimiento_base_proyectado_pct: 0, // de calculate_scenarios
  },
  // Tab 1
  contexto_mercado: [
    // { titulo: "...", valor: "...", fuente: "yfinance" }
  ],
  asimetrias: [
    // { titulo: "...", descripcion: "...", evidencia: "..." }
  ],
  copy_trading: [
    // { username: "...", roi_12m_pct: 0, risk_score: 0, dd_max_pct: 0, copiers: 0, asignacion_usd: 0 }
  ],
  posiciones: [
    // {
    //   ticker: "...", nombre: "...", venue: "eToro",
    //   tipo: "spot|cfd|copy|stake|lending",
    //   asignacion_usd: 0, asignacion_pct: 0,
    //   precio_entrada: 0, fuente_precio: "yfinance",
    //   tesis: "...", catalizador: "...", catalizador_fecha: "DD-MM-AAAA",
    //   risk_score: 0, // 1-10
    //   setup_tecnico: { // null si no aplica (lending/staking/copy)
    //     postura: "BULLISH|NEUTRAL|BEARISH|NO_CLARO",
    //     patron: "...",
    //     entrada: 0, sl: 0, tp1: 0, tp2: 0,
    //     rr: "1:2.1",
    //     justificacion: "..."
    //   },
    //   overnight_fee_mensual_usd: 0, // solo CFD, 0 si no aplica
    // }
  ],
  resumen_plataforma: [
    // { plataforma: "eToro", capital_usd: 0, deposito_metodo: "...", costo_entrada_usd: 0, costo_salida_usd: 0 }
  ],
  // Tab 2
  cronograma: {
    semana_1: [], // ["Lun: depositar X via PSE", ...]
    semana_2: [],
    semana_3: [],
    semana_4: [],
    earnings_dates: [], // [{ ticker: "...", fecha: "DD-MM-AAAA" }]
  },
  // Tab 3
  honestidad_rendimiento: "Capital $X (tramo Y, perfil Z) → mínimo +N% base 6M. Plan proyecta +M% base.",
  escenarios_3m: { optimista: { pct: 0, monto: 0, razon: "" }, base: { pct: 0, monto: 0, razon: "" }, pesimista: { pct: 0, monto: 0, razon: "" } },
  escenarios_6m: { optimista: { pct: 0, monto: 0, razon: "" }, base: { pct: 0, monto: 0, razon: "" }, pesimista: { pct: 0, monto: 0, razon: "" } },
  // Tab 4
  stress_test: { moderado: { drop_pct: -20, monto_resultante_usd: 0 }, severo: { drop_pct: -40, monto_resultante_usd: 0 } },
  correlaciones: [
    // { par: "VOO/QQQ", valor: 0.85, lectura: "alta correlación, considerar diversificar" }
  ],
  validaciones: [
    // { check: "concentración ≤ 50%", resultado: true, detalle: "..." }
  ],
  triggers_salida: [
    // { posicion: "VOO", trigger: "cierre diario < 415", accion: "cerrar 100%" }
  ],
  costos_totales: { entrada_usd: 0, salida_usd: 0, overnight_6m_usd: 0 },
  disclaimers: [
    "Rendimiento pasado no garantiza futuro.",
    "Todo instrumento tiene riesgo de pérdida de capital.",
    "Este agente no ejecuta órdenes.",
    "Consulta con un contador para la fiscalidad local de tus inversiones.",
  ],
  baseline_seguimiento: {
    // schema completo de tracking_skill.md §Schema del BASELINE DE SEGUIMIENTO
    // todos los campos llenos con cálculos reales — nunca null si la tool entregó dato
  },
};

const TABS = [
  { id: "plan",       label: "📊 Plan",       accent: "emerald" },
  { id: "cronograma", label: "📅 Cronograma", accent: "sky" },
  { id: "escenarios", label: "📈 Escenarios", accent: "amber" },
  { id: "riesgo",     label: "⚠️ Riesgo",     accent: "rose" },
];

// IMPORTANTE: las clases con interpolación tipo `border-${accent}-400` NO funcionan
// con Tailwind JIT. Map literal con strings completos:
const ACCENT_CLASSES = {
  emerald: { text: "text-emerald-400", border: "border-emerald-400", bg: "bg-emerald-500/10" },
  sky:     { text: "text-sky-400",     border: "border-sky-400",     bg: "bg-sky-500/10" },
  amber:   { text: "text-amber-400",   border: "border-amber-400",   bg: "bg-amber-500/10" },
  rose:    { text: "text-rose-400",    border: "border-rose-400",    bg: "bg-rose-500/10" },
};

function RiskBar({ score }) {
  const pct = Math.max(0, Math.min(100, (score / 10) * 100));
  const color =
    score <= 3 ? "bg-emerald-400" :
    score <= 6 ? "bg-amber-400" : "bg-rose-400";
  const label =
    score <= 3 ? "BAJO" :
    score <= 6 ? "MODERADO" : "ALTO";
  return (
    <div className="flex items-center gap-3">
      <span className="font-mono text-sm tabular-nums">{score.toFixed(1)}/10 — {label}</span>
      <div className="h-2 w-32 rounded-full bg-slate-700 overflow-hidden">
        <div className={`h-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}

function CopyBaselineButton({ baseline }) {
  const [copied, setCopied] = useState(false);
  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(JSON.stringify(baseline, null, 2));
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (e) {
      // fallback: el <pre> sigue seleccionable para copia manual
    }
  };
  return (
    <button
      onClick={handleCopy}
      className="px-3 py-1.5 text-xs font-medium rounded-md bg-emerald-500 hover:bg-emerald-400 text-slate-900 transition"
    >
      {copied ? "✓ Copiado" : "Copiar BASELINE"}
    </button>
  );
}

function TabPlan({ d }) {
  // Render: contexto_mercado (cards), asimetrias (callouts), copy_trading (tabla),
  // posiciones (cards expandibles con setup técnico), distribución del capital
  // (barras horizontales con % visible), resumen_plataforma (tabla)
}

function TabCronograma({ d }) {
  // Render: 4 cards de semana (S1-S4) con bullets dia-a-dia,
  // sección "Earnings dates" como timeline horizontal con fecha visible
}

function TabEscenarios({ d }) {
  // Render: nota de honestidad arriba (callout amber con tramo y mínimo aplicado),
  // 2 tablas (3M / 6M) con filas optimista/base/pesimista, columnas: %, monto, razón
  // Colorear filas: emerald optimista, sky base, rose pesimista
}

function TabRiesgo({ d }) {
  // Render: stress test (2 cards moderado/severo con monto en grande),
  // tabla de correlaciones (con lectura por par), lista de validaciones (✓/✗),
  // triggers de salida (tabla), costos_totales (3 cards), disclaimers (lista numerada),
  // BLOQUE BASELINE: <pre> + botón copiar (componente CopyBaselineButton)
}

export default function InvestmentPlan() {
  const [active, setActive] = useState("plan");
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 font-sans p-6">
      {/* Header */}
      <header className="mb-6 border-b border-slate-800 pb-4">
        <h1 className="text-2xl font-semibold tracking-tight">Plan de inversión</h1>
        <p className="text-sm text-slate-400 mt-1">
          {data.meta.fecha} · Capital ${data.meta.capital_total_usd.toLocaleString()} ·
          Perfil {data.meta.perfil_riesgo} · Horizonte {data.meta.horizonte_meses}M
        </p>
      </header>

      {/* Tabs nav */}
      <nav className="flex gap-1 mb-6 border-b border-slate-800" role="tablist">
        {TABS.map((t) => {
          const a = ACCENT_CLASSES[t.accent];
          const isActive = active === t.id;
          return (
            <button
              key={t.id}
              role="tab"
              aria-selected={isActive}
              onClick={() => setActive(t.id)}
              className={`px-4 py-2 text-sm font-medium rounded-t-md transition ${
                isActive
                  ? `bg-slate-900 ${a.text} border-b-2 ${a.border}`
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              {t.label}
            </button>
          );
        })}
      </nav>

      {/* Tab panels */}
      <main role="tabpanel" className="bg-slate-900 rounded-lg p-6 shadow-xl">
        {active === "plan"       && <TabPlan       d={data} />}
        {active === "cronograma" && <TabCronograma d={data} />}
        {active === "escenarios" && <TabEscenarios d={data} />}
        {active === "riesgo"     && <TabRiesgo     d={data} />}
      </main>

      <footer className="mt-6 text-xs text-slate-500 text-center">
        Generado por agente de inversión — datos vía MCP servers, números calculados, no inventados.
      </footer>
    </div>
  );
}
```


Contenido de cada tab (idéntico a v6.2 — qué va en cada uno)

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

5. Distribución del capital (barra visual + número visible)
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

Tab 4: "⚠️ Riesgo" — Stress test + validación + disclaimers

1. Stress test: crash moderado (-20%) y severo (-40%) con montos
2. Correlación entre posiciones
3. Checks de validación (concentración, defensivo, tolerancia)
4. Reglas de protección y triggers de salida
5. Costos totales desglosados
6. Disclaimers obligatorios
7. BASELINE DE SEGUIMIENTO (bloque JSON para la próxima revisión)
   - Schema completo en tracking_skill.md §Schema del BASELINE DE SEGUIMIENTO.
   - Todos los campos rellenos desde cálculos reales, NUNCA inventados.
   - Renderizado dentro de un `<pre className="...">` legible, con botón "Copiar".
   - Precedido por una nota al usuario: "Guarda este bloque. Cuando quieras
     que revise cómo va tu portafolio, escríbeme 'revisa mi portafolio' y
     pégame este JSON."


REGLAS DE FORMATO NUMÉRICO (siguen aplicando dentro del JSX)

Risk scores — SIEMPRE mostrar como texto visible:
  CORRECTO: "8.0/10 — ALTO" (número + barra visual al lado, ver componente RiskBar)
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


Checklist de calidad (verificar ANTES de generar el artifact JSX)

□ ¿El entregable es un artifact JSX (no texto en chat)?
□ ¿El componente exporta default un componente funcional sin props requeridas?
□ ¿Exactamente 4 tabs con los nombres correctos?
□ ¿NO hay tabs adicionales?
□ ¿Las clases Tailwind con accent vienen de un map literal (no interpoladas)?
□ ¿NO se usa localStorage / sessionStorage?
□ ¿NO se importan fuentes externas (Google Fonts, etc.)?
□ ¿Precios reales via MCP con fuente indicada en cada posición?
□ ¿Tesis específica por posición (no genérica)?
□ ¿Catalizador con fecha por posición?
□ ¿SL y TP por posición direccional?
□ ¿Risk score como NÚMERO visible X.X/10 (no solo barra)?
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
□ ¿Disclaimers al final del Tab 4?
□ ¿Cada posición direccional tiene bloque "Setup técnico" con SL/TP derivados de technical_skill.md?
□ ¿El R:R técnico por posición es ≥ 1:1.5 (equity/cripto) o ≥ 1:2 (forex)? Si alguna posición queda por debajo, ¿está marcada explícitamente?
□ ¿La modulación del cronograma (Tab 2) refleja la postura técnica? (Bullish → entrada Semana 1; Neutral → 50/50 S1-S2; Bearish → 33/resto condicionado)
□ ¿Los SL técnicos aparecen también en el Tab 4 como triggers de salida?
□ ¿El Tab 4 incluye el bloque BASELINE DE SEGUIMIENTO en JSON con todos los campos del schema de tracking_skill.md?
□ ¿El BASELINE tiene botón "Copiar" funcional con navigator.clipboard?
□ ¿Todos los campos del BASELINE vienen de cálculos reales de las tools (pesos de allocate_portfolio, SL/TP de technical_skill, risk scores calculados, fechas de catalizadores de yfinance)?
□ ¿Hay un recordatorio al usuario indicando que guarde el bloque y lo pegue con "revisa mi portafolio" en la próxima sesión?
□ ¿El mensaje de chat alrededor del artifact es ≤3 líneas (solo introducción, no resumen del plan)?
