# Reglas de riesgo — Validación autónoma del portafolio v2

## Cuándo se ejecuta
Este skill se ejecuta AUTOMÁTICAMENTE en el Paso 5 del orquestador:
- Después de seleccionar las posiciones del plan (antes de presentar)
- Cuando se agrega o modifica cualquier posición
- Cuando el usuario reporta rendimiento real
- En cada rebalanceo trimestral sugerido

## Reglas por perfil de riesgo

### R1: Concentración individual
```
RIESGO BAJO (1-3):    ninguna posición > 25% del capital
RIESGO MODERADO (4-6): ninguna posición > 30% del capital
RIESGO ALTO (7-8):    ninguna posición > 35% del capital
RIESGO EXTREMO (9-10): ninguna posición > 40% del capital

SI viola → reducir al máximo permitido y redistribuir excedente.
```

### R2: Concentración por vertical
```
Threshold escalado por perfil de riesgo (mismo patrón que R1):

  RIESGO BAJO (1-3):     ninguna vertical > 40% del capital
  RIESGO MODERADO (4-6): ninguna vertical > 50% del capital
  RIESGO ALTO (7-8):     ninguna vertical > 70% del capital
  RIESGO EXTREMO (9-10): ninguna vertical > 90% del capital

Excepción "horizonte corto" (solo perfil ALTO o EXTREMO):
  Si horizonte declarado ≤ 3 meses Y perfil ∈ {alto, extremo}:
    - Perfil ALTO permite hasta 80% (en lugar de 70%).
    - Perfil EXTREMO sin techo extra (sigue 90%).
  La excepción se invoca SOLO si:
    (a) el usuario declaró horizonte ≤ 3 meses en la entrada del plan, Y
    (b) la vertical sobre-ponderada tiene liquidez alta (equity líquido,
        cripto major, NO DeFi con lockup ni copy trading).
  La excepción se DOCUMENTA en `data.validaciones[]` del artifact con
  una entrada explícita: "R2 con excepción horizonte corto: equity
  75% sobre threshold base 70%, dentro del techo 80% por horizonte
  declarado de 3 meses". Sin esa entrada, B-checks asumen el threshold
  base y B5 falla.

Cómo se calcula la "vertical" para R2:
  vertical(posicion) ∈ {equity, cripto_spot, cripto_lending, defi_pool,
                        forex_cfd, copy_trading, smart_portfolio,
                        cash_reserva}
  Para mezcla equity + ETF broad → ambos cuentan como "equity".
  Para BTC/ETH spot + stablecoin lending → SE SEPARAN: spot va a
  "cripto_spot", lending a "cripto_lending" (drivers distintos).
  Cash en USD/USDC sin yield → "cash_reserva", NO "cripto_lending".

SI viola el threshold del perfil (sin invocar excepción válida):
  → reducir la vertical sobre-ponderada al threshold y redistribuir el
    excedente entre las otras verticales del plan respetando R1
    (concentración individual ≤ threshold del perfil).
  → Si no hay otra vertical en el plan, mover el excedente a
    cash_reserva o sugerir al usuario añadir un vertical diversificador.

Caso retroactivo — sesión 2 (C/CVS perfil agresivo, horizonte 3M):
  Equity = 75.4% del total ($275.59 / $365.59).
  Threshold base perfil ALTO: 70% → FAIL.
  Excepción horizonte corto (3M, equity líquido NYSE): techo 80% → PASA.
  Documentación requerida en validaciones: "R2 con excepción horizonte
  corto: equity 75.4% > base 70%, dentro de techo 80% por horizonte 3M".
  Sin esa documentación, R2 se evalúa con threshold base y el plan
  se reescribe redistribuyendo $20 a otra vertical.
```

### R3: Reserva mínima
```
RIESGO BAJO:     reserva líquida ≥ 15%
RIESGO MODERADO: reserva líquida ≥ 10%
RIESGO ALTO:     reserva líquida ≥ 0% (no obligatoria)
RIESGO EXTREMO:  reserva líquida ≥ 0% (no obligatoria)

Para riesgo alto y extremo, la reserva es OPCIONAL.
El usuario acepta no tener colchón de seguridad.
```

### R4: Capital ilíquido
```
TODOS LOS PERFILES: activos con lock > 30 días ≤ 20% del total
SI viola → reemplazar por alternativas flexibles.
```

### R5: Correlación
```
PARA cada par (i, j) de activos del plan con i < j:
  → Obtener 30 días de precios de cierre reales (closes diarios).
  → Ejecutar calculate_correlation(prices_a, prices_b).
  → El valor devuelto es el ÚNICO número aceptable. Sin tool no hay
    correlación — punto.

Cadena de fuentes para los 30 closes (probar en orden, parar al primer
éxito; cada par puede usar fuentes distintas):

  1. alphavantage TIME_SERIES_DAILY (preferida para acciones US y forex):
     - Endpoint canónico, splits/dividends ajustados.
     - Si responde con 30+ closes válidos para AMBOS activos → usar.

  2. yahoo-finance.yfinance_get_price_history (fallback general):
     - Pedir period="2mo", interval="1d" y tomar últimos 30 closes.
     - Cobertura amplia: equity global, ETFs, cripto majors (BTC-USD,
       ETH-USD), índices.
     - Si responde con 30+ closes para AMBOS activos → usar.

  3. etoro-server.get_candles (fallback para activos eToro-only):
     - Útil cuando el activo solo se opera en eToro y otras fuentes no
       lo cubren. Pedir 30 candles diarios y extraer columna Close.

  Si NINGUNA de las tres fuentes devuelve 30 closes válidos para ambos
  activos del par → ese par queda como "no disponible vía tool" y se
  EXCLUYE de la correlation_matrix pasada a calculate_portfolio_risk_score
  (no se rellena con un valor inventado, no se promedia desde sectores,
  no se usa "estimada" como string). El plan se entrega con la nota
  explícita en Tab 4 de qué par quedó sin medir y por qué.

Umbrales (sobre el valor devuelto por la tool, no sobre supuestos):
  SI correlación > 0.7:
    → Riesgo BAJO / MODERADO: reemplazar uno de los dos por un activo
      descorrelacionado y recalcular.
    → Riesgo ALTO / EXTREMO: advertir, permitir si el usuario lo acepta
      explícitamente.
  SI 0.3 < correlación ≤ 0.7:
    → Aceptable. Reportar el valor en la presentación del plan.
  SI correlación ≤ 0.3:
    → Buena diversificación. Reportar el valor.

PROHIBIDO (cualquiera de estos invalida la sesión, B7 falla):
  ❌ Usar correlaciones precalculadas o pares "conocidos" que no
     provengan de calculate_correlation sobre datos reales del periodo.
  ❌ Escribir strings como "estimada", "cualitativa", "sectores
     diferentes", "media-alta (~0.5-0.7)", o cualquier rango/etiqueta
     que NO sea un número con 2 decimales devuelto por la tool en el
     campo `valor` de las correlaciones del artifact.
  ❌ Justificar la ausencia con "el skill alphavantage no fue invocado"
     sin haber probado el fallback yfinance ni etoro get_candles.
  ❌ Pasar a calculate_portfolio_risk_score una correlation_matrix con
     valores inventados o estimados — corrompe R6 downstream.

Si todas las fuentes fallan para un par y el par es central a la tesis
(p.ej. los dos únicos activos direccionales del plan), el plan NO se
entrega como está: se sustituye una de las dos posiciones por un activo
de la misma clase con cobertura de tools confirmada, o se pide al
usuario un ticker alternativo. Entregar un plan con el par central sin
correlación medida convierte R6 en ficción.
```

### R6: Risk score del portafolio (ajustado por correlación)
```
Ejecutar calculate_portfolio_risk_score(positions, correlation_matrix)

La tool calcula:
  score_ponderado = Σ(weight_i × risk_score_i)            ← base

Y luego ajusta por correlación promedio ponderada entre pares:
  corr_prom = Σ(w_i × w_j × corr_ij) / Σ(w_i × w_j)       para i < j

  SI corr_prom > 0.7:  score_final = score_ponderado + 1.0
  SI corr_prom < 0.3:  score_final = score_ponderado - 0.5
  EN OTRO CASO:        score_final = score_ponderado

score_final se satura a [1, 10].

Límites por perfil (evaluar sobre score_final, no sobre el ponderado base):
  RIESGO BAJO:     score_final ≤ 4.0
  RIESGO MODERADO: score_final ≤ 6.0
  RIESGO ALTO:     score_final ≤ 8.0
  RIESGO EXTREMO:  sin límite (acepta cualquier score)

Cómo armar la correlation_matrix:
  - Para cada par (i, j) con i < j, ejecutar calculate_correlation con 30d.
  - Construir matriz N×N simétrica con diagonal = 1.0.
  - Pasarla a calculate_portfolio_risk_score.
  - Si no hay precios para algún par, omitir la matriz: la tool devuelve
    solo el score ponderado base (compatible con R6 v1).

SI viola → reducir posición con mayor risk score y redistribuir.
  Si además corr_prom > 0.7, priorizar reemplazar una posición del par
  más correlacionado antes que solo reducir tamaño — eso ataca la causa
  (concentración en un mismo factor), no el síntoma.

Por qué el ajuste: dos posiciones de risk=8 correlacionadas al 0.9 son
mucho más riesgosas que las mismas dos correlacionadas al 0.2. En caída
caen juntas. La suma ponderada sola las trata idénticamente; el ajuste
por correlación promedio ponderada refleja la diversificación real.
```

### R7: Event Risk Overlay (overlay determinista al risk_score por posición)
```
Problema que resuelve:
  calculate_risk_score evalúa volatilidad histórica, drawdown 12m,
  liquidez y leverage. NO mira hacia adelante: no sabe que hay un
  earnings binario en 6 días, ni que el ticker es un small-cap cuyo
  volumen "normal" se evapora en momentos de estrés. Por eso planes
  como sesión 1 reportaban tool=2.4 vs real=7.0 con justificación
  vaga ("evento binario inminente y small/mid cap"). Ese gap quedaba
  a discreción del agente.

R7 reemplaza esa discreción con una fórmula determinista. El overlay
NO sustituye al score de la tool — lo COMPLEMENTA. Ambos valores
aparecen en el artifact:

  risk_score_tool  = salida directa de calculate_risk_score (decimal,
                     con componentes desglosados, B15 lo audita)
  risk_score_real  = risk_score_tool + event_overlay  (saturado a [1,10])

Cálculo del event_overlay (suma de los componentes que apliquen):

  COMPONENTE 1 — Earnings calendarizado:
    Solo aplica a equity individual. Fuente: yfinance_get_ticker_info,
    campos earningsTimestampStart e isEarningsDateEstimate (extraídos
    según equity_skill.md, validados por B17).

    Días hasta earnings desde la fecha del plan:
      < 7 días:    +2.0
      7-14 días:   +1.5
      14-30 días:  +1.0
      > 30 días:   +0.0

    Si isEarningsDateEstimate == true (Yahoo no confirmó la fecha):
      multiplicar el componente × 0.7
      (rationale: incertidumbre adicional sobre la fecha real;
       descontamos parte del overlay, no todo, porque la ventana
       sigue siendo ventana).

    Earnings de ETFs broad (SPY, QQQ, etc.): NO aplica overlay
    (no hay reporte de empresa, son cestas).

  COMPONENTE 2 — Catalizador regulatorio inminente:
    +1.0 si hay catalizador específico documentado en `data.posiciones[]
    .catalizador` distinto de earnings, con `catalizador_fecha` < 30
    días desde la fecha del plan. Tipos cubiertos:
      - FDA decision (PDUFA date, advisory committee)
      - Antitrust ruling (DOJ/FTC pending)
      - SEC enforcement deadline conocido públicamente
      - Merger close date / deal break risk window
      - Sanción/política comercial con fecha publicada
    Catalizadores genéricos como "earnings season", "macro outlook",
    "Fed meeting" NO califican — son ambientales, no específicos al
    ticker.

  COMPONENTE 3 — Small-cap (mcap < $2B):
    +0.5 fijo. Fuente: yfinance_get_ticker_info, campo `marketCap`.
    Rationale: la tool calcula liquidez con volumen reciente; en
    small-caps el "volumen normal" puede evaporarse en momentos de
    estrés (ask/bid spread se abre 5-10×). El overlay reconoce esa
    asimetría sin requerir backtesting.

  COMPONENTE 4 — Sector con drawdown reciente >30% en 90 días:
    +0.5 fijo. Fuente: opcional, requiere screener sector-level.
    Si no se mide, NO inventar — omitir el componente.

  COMPONENTE 5 — Posición ilíquida con lockup >30 días:
    +0.5 si la posición es DeFi staking/farming con lock o vesting
    activo. Aplica a través de defi_skill, no equity. Esta línea está
    aquí solo por completitud — el cálculo lo hace defi_skill al
    construir la posición.

Total event_overlay = suma de componentes que aplican, saturado a
[0, 4]. Saturar a 4 evita que un ticker pequeño con earnings y
sector castigado sume +3.5 y haga que el real supere 10 cuando
tool ya era 7+.

Saturación final del risk_score_real:
  risk_score_real = min(10, max(1, risk_score_tool + event_overlay))

Auditoría — el artifact debe mostrar el desglose:
  En `data.posiciones[].event_overlay` (objeto):
    {
      total: 2.0,
      componentes: [
        { tipo: "earnings_<7d", puntos: 2.0, evidencia: "earnings 06-may-2026, 6 días, confirmado" },
        // ...
      ]
    }
  Si event_overlay.total > 0 y `data.posiciones[].risk_score_real`
  no aparece en el artifact, B15 falla.

Validación retroactiva sobre sesión 1:
  NBIS:
    risk_score_tool = 2.4 (de la tool)
    Componentes:
      earnings 6-may a 6 días, confirmada → +2.0
      isEarningsDateEstimate=true (era estimada) → 2.0 × 0.7 = 1.4
      mcap $34.97B → no aplica small-cap
      Sin catalizador regulatorio → +0
    event_overlay = 1.4
    risk_score_real = 3.8
  Sesión 1 reportó 7.0 → inflación arbitraria de +3.2 puntos sobre
  lo que la fórmula justifica. Bajo R7, el agente o entrega 3.8 o
  documenta componentes adicionales con evidencia (no hay).

  RKLB:
    risk_score_tool = 3.0
    Componentes:
      earnings 7-may a 7 días, confirmado → +2.0 (cae justo en bin <7d
        si el plan era del 30-abr; si del 04-may → +1.5)
      mcap $47.69B → no aplica small-cap
    event_overlay = 1.5 a 2.0
    risk_score_real = 4.5 a 5.0
  Sesión 1 reportó 7.5. Mismo patrón — overlay arbitrario.

Cómo se aplica en Fase 4 del system.md:
  1. Llamar calculate_risk_score → guardar risk_score_tool y componentes.
  2. Calcular event_overlay con la fórmula de arriba.
  3. risk_score_real = saturar(risk_score_tool + event_overlay).
  4. Pasar AMBOS valores al esqueleto JSX:
       data.posiciones[i].risk_score          = risk_score_tool
       data.posiciones[i].event_overlay       = { total, componentes }
       data.posiciones[i].risk_score_real     = risk_score_real
  5. R6 (portfolio risk score) usa risk_score_tool, NO real
     (el overlay es información complementaria; el agregado del
     portafolio usa el score base + ajuste por correlación).
```

## Stress test obligatorio
```
ANTES de presentar cualquier plan:
  → Ejecutar stress_test_portfolio con "moderate_crash" Y "severe_crash"
  → Incluir AMBOS en la presentación con montos en dólares
  → Verificar que la pérdida máxima NO exceda la tolerancia declarada:
    - Riesgo bajo: pérdida max ≤ 20%
    - Riesgo moderado: pérdida max ≤ 40%
    - Riesgo alto: pérdida max ≤ tolerancia declarada (típicamente 70-80%)
    - Riesgo extremo: acepta pérdida total
```

## Exit triggers (auto-generar por posición)
```
SI vertical = equity:
  → Alerta si cae > 15% desde precio de compra (riesgo bajo/moderado)
  → Alerta si cae > 25% desde precio de compra (riesgo alto)

SI vertical = defi Y no es stablecoin:
  → Alerta si cae > 20%
  → Alerta si APY baja del 2%
  → Alerta si TVL del protocolo cae > 30% en una semana

SI vertical = forex:
  → Stop loss definido en el plan (calculate_position_size)

SI vertical = social (copy trading):
  → Alerta si drawdown del trader > 25% en el mes
  → Alerta si deja de operar > 2 semanas
```

## Orden de ejecución
1. Ejecutar `calculate_risk_score` para cada posición
   → Guardar `risk_score_tool` y los `componentes` devueltos por la tool.
2. Calcular `event_overlay` para cada posición según R7 (suma determinista
   de componentes con evidencia documentada). Calcular `risk_score_real
   = saturar(risk_score_tool + event_overlay)`. Ambos van al artifact.
3. Verificar R1 a R5 según el perfil de riesgo del usuario:
   → R1 (concentración individual) — threshold escala por perfil.
   → R2 (concentración por vertical) — threshold escala por perfil; si
     se invoca excepción "horizonte corto", documentarla en validaciones[].
   → R3, R4 según corresponda.
   → R5 (correlación) — cadena alphavantage → yfinance → etoro get_candles.
4. Ejecutar `calculate_correlation` para cada par principal de activos
   → Armar la `correlation_matrix` del portafolio con los resultados.
5. Ejecutar `calculate_portfolio_risk_score(positions, correlation_matrix)`
   → R6 usa `risk_score_tool` de cada posición (NO `risk_score_real`),
     el overlay es información complementaria por posición.
   → Aplica R6 (score ponderado + ajuste por correlación).
   → Verificar límite según perfil del usuario (BAJO/MODERADO/ALTO/EXTREMO).
6. Ejecutar `stress_test_portfolio` con moderate Y severe.
7. Generar exit triggers por posición.
8. Si algún ajuste se hizo: explicar al usuario qué cambió y por qué.
