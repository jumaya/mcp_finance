# social_skill.md — Copy Trading inteligente

Instrucciones para el agente cuando el usuario expresa interés en
**copy trading** o en **seguir popular investors** en eToro.

## Regla fundamental

**NUNCA recomendar traders por nombre sin validar sus métricas con datos
reales de la API.** Nombres como @JeppeKirkBonde o @jaynemesis son
referencias iniciales útiles, pero toda sugerencia final debe apoyarse
en los datos que devuelven las tools del MCP `etoro-server`.

## Cuándo activar este skill

Se activa cuando el usuario menciona:

- "Copy trading", "copiar traders", "popular investors", "PI", "eToro social".
- "¿A quién debería copiar?", "recomiéndame un trader".
- Pregunta por retornos históricos de un usuario específico de eToro.
- Diseño de cartera donde una porción va a "seguir a otros".

## Flujo recomendado

### Paso 1 — Entender el perfil del usuario

Antes de buscar traders, el agente debe tener claro:

- **Horizonte temporal** (corto/medio/largo).
- **Tolerancia al riesgo** (conservador = risk score 1-4; moderado = 4-6;
  agresivo = 6-8; nunca sugerir 9-10 sin advertencia fuerte).
- **Monto a destinar** a copy trading dentro del portfolio total.
- **Mercados preferidos** (acciones, cripto, forex, diversificado).

Si algo no está claro, el agente **pregunta una sola cosa por mensaje**
antes de buscar.

### Paso 2 — Ver el portfolio actual del usuario (si hay contexto)

Si el usuario ya tiene cuenta eToro conectada al MCP, llamar
`get_portfolio` primero para saber:

- Cuánto `credit` (cash libre) tiene disponible para asignar.
- Si ya tiene `mirrors` (copias activas) — no sugerir duplicar un trader
  que ya está copiando.
- Qué `positions` manuales tiene — evitar sugerir traders cuyo
  `topTradedInstrumentId` solape mucho con lo que el usuario ya opera
  directamente (redundancia de exposición).

### Paso 3 — Descubrir candidatos con `discover_popular_investors`

Llamar con filtros coherentes al perfil del usuario. **No pasar todos
los filtros de golpe**; la API puede fallar con combinaciones. Patrón
probado que funciona:

**Conservador (risk 1-4):**
```
discover_popular_investors(
  period="OneYearAgo",
  page_size=10,
  popular_investor=True,
  max_monthly_risk_score_max=4,
  min_weeks_since_registration=104   # 2+ años
)
```

**Moderado (risk 4-6):**
```
discover_popular_investors(
  period="OneYearAgo",
  page_size=10,
  popular_investor=True,
  max_monthly_risk_score_max=6,
  min_weeks_since_registration=52    # 1+ año
)
```

**Agresivo:** igual al moderado pero subiendo `max_monthly_risk_score_max`
a 7 como tope absoluto, nunca más.

**Si un filtro hace que la API devuelva 404** (error "An error has
occurred."), quitar ese filtro y reintentar. Los filtros opcionales son
frágiles en combinación — es preferible traer más resultados y filtrar
en post-proceso.

### Paso 4 — Rankear por métricas objetivas, no por ganancia pura

La API ordena por `copiers` por defecto. El agente debe **rerankear**
los candidatos aplicando este criterio compuesto:

**Métricas que importan (del response de `discover_popular_investors` o
`get_user_performance`):**

| Métrica | Lectura | Peso sugerido |
|---|---|---|
| `gain` | Ganancia del período. Más alto mejor, pero no es lo único. | 30% |
| `profitableMonthsPct` | % de meses en verde. >70% es excelente. | 20% |
| `peakToValley` | Máximo drawdown. Menor (más cercano a 0) mejor. | 20% |
| `winRatio` | % de trades ganadores. >60% es bueno. | 10% |
| `weeksSinceRegistration` | Experiencia. >104 semanas (2 años) preferible. | 10% |
| `copiers` | Validación social. >1000 ya es señal. | 10% |

**Señales de descarte inmediato:**

- `maxMonthlyRiskScore > 7` si el usuario es conservador o moderado.
- `highLeveragePct > 20` (usa apalancamiento agresivo con frecuencia).
- `peakToValley < -30` (drawdown histórico mayor a 30%).
- `weeksSinceRegistration < 26` (menos de 6 meses, track record insuficiente).

### Paso 5 — Profundizar en los 2-3 finalistas con `get_user_performance`

Para cada candidato corto, llamar `get_user_performance` con múltiples
periodos para verificar **consistencia**, no solo buen rendimiento
reciente:

```
get_user_performance(username="Xxx", period="OneYearAgo")
get_user_performance(username="Xxx", period="LastTwoYears")
get_user_performance(username="Xxx", period="CurrYear")
```

Un trader con +80% en 1 año pero -10% promedio en 2 años **no es
confiable** — solo tuvo suerte. Preferir consistencia (+20% anual
sostenido) sobre picos recientes.

### Paso 6 — Presentar con datos, no con adjetivos

Al usuario se le muestra una tabla comparativa con las métricas clave,
**no una recomendación única**. Ejemplo:

> Basado en tu perfil moderado, estos son los 3 candidatos con mejores
> métricas de los últimos 12 meses:
>
> | Trader | Ganancia | Risk | Drawdown máx | Meses verdes | Copiers | Años |
> |---|---|---|---|---|---|---|
> | @X | +45% | 5 | -12% | 84% | 25K | 12 |
> | @Y | +38% | 4 | -9% | 78% | 15K | 9 |
> | @Z | +52% | 6 | -18% | 69% | 33K | 6 |
>
> @X destaca en consistencia (84% de meses en verde, drawdown bajo).
> @Y es la opción más conservadora (risk 4, drawdown menor).
> @Z tiene el mayor retorno pero también el mayor riesgo.
>
> ¿Con cuál quieres profundizar? Puedo traer su portfolio actual y
> las últimas operaciones.

### Paso 7 — Advertencias obligatorias antes de cualquier acción

Antes de que el usuario decida copiar a alguien, el agente **siempre**
recuerda:

1. Rendimiento pasado no garantiza futuro.
2. Mínimo recomendado de copy en eToro suele ser $200 USD.
3. Se puede configurar `stopLossPercentage` al abrir el copy (el agente
   sugiere 15-25% según risk score del trader).
4. El MCP actual es **solo lectura** — el usuario ejecuta la copia él
   mismo desde la plataforma eToro.
5. Si la clave es `real` Read-only, Claude puede ver el portfolio pero
   no puede abrir copies automáticamente (por diseño, es una decisión
   de seguridad del setup).

## Qué NO hacer

- ❌ Sugerir traders sin haber llamado `get_user_performance` para ver
  sus métricas reales.
- ❌ Usar nombres hardcodeados como referencias definitivas. Son solo
  punto de partida para que el usuario sepa de qué estamos hablando.
- ❌ Basar la recomendación solo en `gain` anual. Alto retorno con alto
  drawdown es peor que retorno moderado estable.
- ❌ Pasar todos los filtros de `discover_popular_investors` juntos —
  algunos combinan mal y rompen el endpoint.
- ❌ Asumir que el usuario puede copiar un trader desde Claude. El MCP
  no ejecuta escritura. Darle instrucciones para hacerlo manualmente
  en eToro.
- ❌ Dar consejo financiero categórico. Presentar datos y dejar la
  decisión al usuario.

## Contexto técnico para el agente

- **Tools disponibles del MCP `etoro-server`:**
  - `get_portfolio` — cartera personal + cash libre + mirrors actuales.
  - `discover_popular_investors` — descubrir candidatos (frágil con
    filtros compuestos; empezar simple).
  - `get_user_performance` — métricas detalladas de un trader específico.
  - `search_instruments`, `get_rates`, `get_candles` — para analizar
    los activos que los traders están operando (cruce con
    `topTradedInstrumentId`).

- **`aumTierDesc`** indica el tamaño del capital que maneja el trader:
  `<$10K`, `$10K-$100K`, `$100K-$1M`, `$1M-$5M`, `$5M+`. Preferir
  `$1M+` para señal de confianza institucional.

- **`topTradedAssetId`**: 5 = acciones, 6 = ETFs, 10 = cripto, 11 = forex.
  Útil para matchear con preferencia del usuario.

- **`isFund: true`** marca Smart Portfolios / fondos gestionados, que
  tienen dinámica distinta al copy de un trader individual. Mencionarlo
  explícitamente si aparece.

## Ejemplo de conversación ideal

> **Usuario:** Tengo $1000 y quiero copy trading conservador.
>
> **Agente:** [llama get_portfolio para ver si ya tiene algo]
> [llama discover_popular_investors con risk ≤ 4]
> [selecciona 3 finalistas, llama get_user_performance a cada uno con
>  OneYearAgo y LastTwoYears para ver consistencia]
> [presenta tabla comparativa con las 6 métricas, pregunta con cuál
>  profundizar]
>
> **Usuario:** Cuéntame más de @X.
>
> **Agente:** [llama get_user_performance(@X, "LastTwoYears")]
> [muestra que su `topTradedInstrumentId` es el 1971, llama
>  search_instruments para identificarlo, llama get_rates para
>  ver precio actual]
> [resume, recuerda advertencias, explica que para copiarlo debe
>  ir a eToro.com/people/X directamente]
