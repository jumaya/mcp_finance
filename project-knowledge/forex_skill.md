# Skill: Agente de Forex y CFDs — v2

## Cuándo se activa
Este skill se activa cuando:
- El allocate_portfolio asigna capital a "forex"
- El usuario menciona forex, divisas, trading, pares, EUR/USD, apalancamiento
- NUNCA se activa como primera recomendación para principiantes

## 🚪 Gate de disponibilidad eToro (para pares/CFDs operados en eToro)

**Cuándo aplica:** solo si el plan propone operar en eToro (no aplica a
Capital.com, XTB, Pepperstone, MetaTrader con otro broker).

Algunos pares y CFDs sobre commodities (p.ej. XAU/USD) pueden no estar
disponibles para cuentas retail desde Colombia, o estar deshabilitados
temporalmente por condiciones de mercado.

### Protocolo
```
POR CADA par/CFD que se vaya a operar EN eToro:

  etoro-server.search_instruments(
    query="<SYMBOL>",         # ej. "EURUSD", "GBPUSD", "XAUUSD"
    search_by="internalSymbolFull",
    page_size=5
  )

Validar en el primer resultado cuyo symbol coincida:

  ✅ instrumentType ∈ {"Currencies", "Commodities"}
  ✅ isCurrentlyTradable == true
  ✅ isBuyEnabled == true   (o validar según dirección de la operación)

Si falla:
  → par NO operable en eToro para esta cuenta
  → opción 1: sugerir otro broker de la tabla (Capital.com es la mejor
    alternativa desde Colombia por depósito PSE)
  → opción 2: reemplazar por un par líquido equivalente que sí pase
  → informar al usuario antes de continuar
```

Si el usuario ya eligió broker **distinto de eToro**, este gate no
aplica — usar los datos del broker correspondiente.

## Lógica de decisión autónoma

### Barrera de entrada (evaluar ANTES de recomendar)
```
SI experience_level = "none":
  → NO incluir forex en el plan inicial
  → Mencionar como opción futura: "En el mes 3-4 podemos explorar forex con cuenta demo"
  → DETENER este skill

SI experience_level = "beginner":
  → SOLO con cuenta demo obligatoria (1 mes mínimo)
  → Capital real máximo: $100 o 10% del capital total (lo menor)
  → Universo restringido: solo pares donde ambas patas ∈ {USD, EUR, GBP, JPY}
    (descubrimiento dinámico aplica SOLO sobre este subconjunto)
  → Apalancamiento máximo: 2x
  → Excluir XAU/USD y commodity currencies (AUD, NZD, CAD, NOK, SEK)

SI experience_level = "intermediate" o "advanced":
  → Incluir con capital real
  → Apalancamiento máximo: 5x
  → Universo completo disponible para descubrimiento dinámico
    (majors + crosses + commodity currencies + XAU/USD como CFD)
```

### Descubrimiento dinámico de pares

**Principio:** no hay ranking fijo de pares. El universo se escanea cada
iteración y la selección la determina la **tendencia** y el **ATR relativo**,
no una tabla preestablecida.

#### Universo de escaneo (monedas, no pares)
```
MAJORS:              USD, EUR, GBP, JPY, CHF
COMMODITY CURRENCIES: AUD, NZD, CAD, NOK, SEK
(opcional si intermediate+): XAU (oro como CFD commodity)
```

De este universo se construyen pares contra **USD** (majors vs USD) y los
**crosses** más líquidos (EUR/GBP, EUR/JPY, EUR/CHF, GBP/JPY, AUD/JPY,
EUR/AUD, AUD/NZD, EUR/NOK, EUR/SEK, USD/NOK, USD/SEK). Evitar exóticos.

El filtro de barrera de entrada (ver § anterior) puede **restringir** este
universo (p.ej. beginner → solo pares que incluyan USD y donde una pata
sea EUR/GBP/JPY), pero nunca lo sustituye por una lista fija.

#### Protocolo de escaneo
```
PARA CADA par candidato del universo (filtrado por experience_level):

  1. alphavantage.TOOL_CALL(
        name="CURRENCY_EXCHANGE_RATE",
        from_currency="<BASE>",
        to_currency="<QUOTE>"
     )
     → obtener precio spot y validar que el par cotiza.

  2. alphavantage.TOOL_CALL(
        name="FX_DAILY",
        from_symbol="<BASE>",
        to_symbol="<QUOTE>",
        outputsize="compact"   # últimos ~100 días D1
     )
     → calcular sobre la serie:
       - SMA50 y SMA20
       - % de las últimas 20 velas cerradas arriba (o abajo) de SMA50
       - ATR(14) en valor absoluto
       - ATR% = ATR(14) / precio_spot   ← normalización para comparar pares

  3. Clasificar el par:

     TENDENCIA CLARA:
       ≥ 70% de las últimas 20 velas D1 del mismo lado de SMA50
       Y SMA20 en la misma dirección que SMA50
       → candidato válido; registrar dirección (long/short).

     TENDENCIA AMBIGUA:
       entre 45% y 70% del mismo lado
       → descartar esta iteración (no operar lo dudoso).

     RANGO / SIN DIRECCIÓN:
       < 45% (oscila alrededor de SMA50)
       → descartar para swing direccional.

  4. ATR RELATIVO (ranking entre candidatos válidos):
     ordenar los pares que pasaron (3) por ATR%:
       - ATR% muy bajo (< 0.3%) → movimiento insuficiente, descartar
         (el stop técnico queda tan apretado que el R:R no compensa el
         spread + comisión).
       - ATR% normal (0.3% – 1.2%) → preferidos.
       - ATR% alto (> 1.2%) → aceptable SOLO si experience_level ≥
         intermediate y se reduce el tamaño de posición proporcionalmente
         vía calculate_position_size.
```

#### Selección final
```
SI ≥ 1 par pasa los filtros 3 y 4:
  → elegir hasta 2 pares (máximo 3 trades simultáneos, ver "Reglas duras").
  → preferir diversificación de divisa base/cotización
    (no abrir 3 trades todos con USD del mismo lado = misma apuesta).
  → pasar los candidatos a technical_skill para derivar entry/SL/TP.

SI ningún par pasa:
  → NO recomendar forex activo en esta iteración.
  → Explicar: "Escaneé el universo forex (majors + crosses + commodity
    currencies) y ninguno tiene tendencia clara con ATR operable.
    Mejor esperar a la próxima revisión."
  → Esto es comportamiento inteligente: saber cuándo NO actuar.
```

#### Explicación al usuario (patrón)
```
"Del universo escaneado (USD, EUR, GBP, JPY, CHF, AUD, NZD, CAD, NOK,
SEK), los pares con tendencia D1 sostenida y ATR relativo operable esta
semana son: <par A> (<dirección>, ATR% <x.xx>%) y <par B>
(<dirección>, ATR% <x.xx>%). El resto está en rango o con volatilidad
insuficiente para el R:R objetivo."
```

### Dimensionamiento automático
```
SIEMPRE ejecutar calculate_position_size:
→ risk = 1% para beginners, 2% para intermediate+
→ stop_loss = soporte/resistencia más cercano o ATR×1.5
→ leverage = 1x beginners, hasta 5x avanzados

SI el tool retorna warnings:
  → Ajustar automáticamente (reducir leverage o posición)
  → Explicar el ajuste
```

### Reglas duras
```
NUNCA: apalancamiento > 5x | más de 3 trades simultáneos | riesgo > 2% por trade | trade sin stop loss
SIEMPRE: stop loss + TP1 (1:2 R:R) + TP2 (1:3 R:R) | verificar calendario económico | mostrar pérdida máxima en USD
```

## Plataformas y selección automática
```
SI no tiene cuenta forex → Capital.com (PSE directo, más fácil en CO)
SI ya tiene eToro → usar eToro (pero pasar gate de disponibilidad)
SI quiere MetaTrader → Pepperstone o XTB
```

| Plataforma | Depósito CO | Spread EUR/USD | Demo | Regulación |
|-----------|-------------|---------------|------|------------|
| Capital.com | PSE directo | ~0.6 pips | Sí, $100K | FCA/CySEC |
| XTB | PSE, oficina CO | ~0.9 pips | Sí, $100K | KNF/FCA |
| eToro | PayPal, tarjeta | ~1.0 pips | Sí, $100K | CySEC/FCA/ASIC |
| Pepperstone | Transferencia | ~0.1 pips raw | Sí | ASIC/FCA/BaFIN |

## Referencia secundaria: sesiones y spreads típicos

> ⚠️ **Esta tabla NO es un ranking de selección.** La selección del par
> la hace la sección "Descubrimiento dinámico de pares" (tendencia + ATR
> relativo). Esta tabla solo ayuda a elegir **horario de ejecución** y a
> tener una referencia de spread/volatilidad esperada una vez que el
> escaneo dinámico ya eligió el par.

| Par      | Spread típ. | Volatilidad | Sesión óptima             | Nota                              |
|----------|-------------|-------------|---------------------------|-----------------------------------|
| EUR/USD  | 0.6–1.0     | Baja-media  | Londres/NY 8am-12pm ET    | Más líquido                       |
| GBP/USD  | 1.0–1.5     | Media       | Londres 3am-12pm ET       | Más volátil                       |
| USD/JPY  | 0.7–1.2     | Baja-media  | Tokio/Londres             | Buenos movimientos tendenciales   |
| USD/CHF  | 1.0–1.5     | Baja        | Londres/NY                | Sensible a risk-off               |
| AUD/USD  | 0.8–1.3     | Media       | Sídney/Tokio + Londres    | Ligada a commodities y China      |
| NZD/USD  | 1.2–1.8     | Media       | Sídney/Tokio              | Menos líquido que AUD             |
| USD/CAD  | 1.0–1.5     | Media       | NY                        | Correlación inversa con crudo     |
| USD/NOK  | 8–20        | Media-alta  | Londres                   | Commodity currency, spread alto   |
| USD/SEK  | 8–20        | Media       | Londres                   | Commodity currency, spread alto   |
| EUR/JPY  | 1.0–1.6     | Media       | Londres/Tokio             | Cross clásico risk-on/risk-off    |
| GBP/JPY  | 1.8–3.0     | Alta        | Londres                   | "The Beast" – mover el stop       |
| EUR/GBP  | 1.0–1.8     | Baja        | Londres                   | Rango frecuente, ATR% bajo        |
| XAU/USD  | 2–4         | Media-alta  | NY 8am-5pm ET             | CFD commodity, no es par FX puro  |

Si un par aparece **seleccionado por el descubrimiento dinámico** pero
su spread típico aquí listado es > 3 veces el ATR% esperado del trade
→ revisar manualmente si el setup sigue teniendo sentido con los costos.

## Cálculos obligatorios
0. Si se opera en eToro → **Gate eToro** (arriba) antes de seguir
1. 🧭 technical_skill.md (OBLIGATORIO antes del paso 2):
     → Derivar entry, stop y TP técnicamente (Fibonacci sobre swing
       del par, confluencia con S/R, o fallback ATR × 1.5 si no hay
       swing claro).
     → technical_skill reemplaza al texto informal actual sobre
       "soporte/resistencia más cercano" de esta sección.
     → Validar R:R ≥ 1:2 (mínimo más alto que equity porque forex usa
       apalancamiento).

2. `calculate_position_size(capital, risk_pct, entry, stop, leverage)`
   — OBLIGATORIO, usando los valores de entry y stop provenientes de
   technical_skill.
3. `calculate_scenarios(amount, apy=0, volatility=0.15, passive=0, months)`
4. `calculate_risk_score(volatility, drawdown=-0.15, "instant", True, weight)`

## Cronograma autónomo
```
SI principiante:
  Semana 1: cuenta demo (10 min)
  Semana 1-4: SOLO demo, mínimo 20 trades
  Semana 4: revisar → SI rentable: cuenta real $50-$100 | SI no: extender o reasignar

SI intermedio+:
  Día 1: abrir cuenta
  Día 2: depositar + ejecutar descubrimiento dinámico sobre universo completo
  Día 3+: ejecutar setups cuando condiciones se cumplan (re-escanear al menos 1 vez por semana)
```

## Explicación adaptativa
```
SI principiante:
  "Trading de divisas es comprar una moneda esperando que suba contra otra. A diferencia del staking o ETFs, NO genera ingreso pasivo — necesitas dedicar tiempo. Por eso empezamos con cuenta demo."

SI intermedio:
  "Swing trading en pares principales con R:R mínimo 1:2. Entrada en retrocesos a soportes en tendencia."

SI avanzado:
  SI avanzado:
  "El setup viene de technical_skill: entrada en <nivel Fibonacci o S/R>,
   SL en <nivel>, TP escalonado a 1.272 y 1.618 del swing. Position
   sizing al 2% risk con leverage <X>x."
```

## Advertencias obligatorias
- "70-80% de cuentas minoristas pierden dinero"
- "Apalancamiento amplifica ganancias Y pérdidas"
- "Forex NO es ingreso pasivo"
- "SIEMPRE empieza con demo"
- "Nunca inviertas dinero que necesites para gastos esenciales"
