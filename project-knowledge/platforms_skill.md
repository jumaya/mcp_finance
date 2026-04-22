# platforms_skill.md — Plataformas de inversión (eToro + Binance) desde Colombia — v1

Conocimiento operativo de las dos plataformas que usa el inversor colombiano
en este agente. Objetivo: que el agente no proponga posiciones **imposibles
de ejecutar** (USD $5 en eToro, pares inexistentes en Binance CO, depósitos
vía métodos no soportados desde COP, etc.) ni ignore fricciones reales
de entrada/salida en pesos.

> **Vigencia:** datos verificados a abril 2026. Mínimos, spreads, métodos
> P2P y pares disponibles cambian con frecuencia. Si el usuario reporta
> una discrepancia con lo que ve en la plataforma, **prevalece lo que ve
> el usuario** y el agente actualiza la suposición para el resto de la
> sesión.

## Cuándo se activa

Este skill se carga **junto con** el skill vertical correspondiente
(`equity_skill`, `defi_skill`, `forex_skill`, `social_skill`), no lo
reemplaza. Aplica cuando el plan proponga ejecutar cualquier operación
en eToro o Binance, o el usuario pregunte:

- "¿Cuánto necesito como mínimo para abrir esta posición?"
- "¿Cómo deposito en pesos?" / "¿Cómo retiro a Bancolombia/Nequi/Daviplata?"
- "¿Está disponible <ticker/par/token> desde Colombia?"
- "¿Cuánto me cuesta el spread en <activo>?"
- "¿Binance tiene par COP?"
- Cualquier fricción de onboarding entre el usuario y la plataforma.

## Relación con otros skills (no duplicar lógica)

| Dueño | Qué resuelve | Lo que este skill aporta |
|---|---|---|
| `equity_skill` gate | ¿El ticker X está tradable en eToro? | Mínimo USD por posición en equity/ETF spot |
| `defi_skill` gate | ¿Token Y está tradable en eToro? | Mínimo USD cripto en eToro + universo Binance CO |
| `forex_skill` gate | ¿Par Z está tradable en eToro? | Tamaño mínimo CFD forex + spread por par |
| `social_skill` | Cómo elegir a quién copiar | Mínimo USD absoluto de CopyTrader ($200) y cómo se reparte |
| `risk_rules` | Concentración, reserva | Comisiones/spreads que erosionan el rendimiento base |

**Regla dura:** si hay conflicto entre este skill y el gate de un vertical,
gana el **gate** (la API de la plataforma es la verdad en tiempo real).
Este skill es la referencia **cuando no se ha corrido gate todavía**
(dimensionamiento inicial, preguntas del usuario, validación de mínimos
antes de gastar tool calls en datos fundamentales).

---

## 1. eToro — Reglas operativas desde Colombia

### 1.1 Depósito

```
Primer depósito mínimo:
  Colombia / LATAM (tarjeta/PayPal/Skrill): USD $50
  Wire transfer (cualquier país):           USD $500
  Cuenta Islamic:                           USD $1,000
  Cuenta corporativa:                       USD $10,000

Depósitos siguientes:
  Tarjeta/PayPal/otros online:              USD $50
  Wire transfer:                            USD $500

Límite cuenta sin KYC completo:             USD $2,250 acumulado
  → Completar "Complete Verification" antes de pasar este tope
```

Métodos que funcionan desde Colombia (orden de preferencia por fricción):

| Método | Fee eToro | Tiempo | Nota |
|---|---|---|---|
| Tarjeta débito/crédito (Visa/Master) | 0% | Instantáneo | Más usado en CO |
| PayPal | 0% | Instantáneo | Si el usuario ya tiene PayPal en USD |
| Wire transfer (USD) | 0% | 4-7 días hábiles | Solo para montos > $500; costo del banco CO aparte |
| Skrill / Neteller | 0% | Instantáneo | Nicho |

**PSE directo NO existe para eToro.** Si el usuario pregunta "¿puedo
depositar con PSE?", la respuesta es no — tiene que pasar por tarjeta
(que internamente hace la conversión COP→USD al TRM del emisor).

### 1.2 Plataforma solo en USD

```
eToro opera 100% en USD. El usuario deposita en COP (vía tarjeta)
y el emisor de la tarjeta hace la conversión al TRM del día + spread
del banco (típicamente 3-5% sobre el TRM oficial).

IMPLICACIÓN para el plan:
  Si el usuario va a depositar $200 USD en eToro desde una tarjeta CO:
    Costo real ≈ $200 × (1 + fee_tarjeta_CO)
    Donde fee_tarjeta_CO está típicamente en 3-5%
    → reservar el 3-5% extra en el plan o advertirlo
```

### 1.3 Mínimo por posición (CRÍTICO)

```
Stocks spot (activo real, sin leverage):        USD $10
ETFs spot:                                      USD $10
Cripto spot:                                    USD $10
CFDs (stocks/ETFs/crypto con apalancamiento):   USD $50 (margen)
CFDs forex:                                     unit size mínimo (varía por par)
CFDs commodities (XAU, WTI, ...):               USD $50 (margen)
CFDs índices:                                   USD $50 (margen)

Smart Portfolios (Thematic / Partner):          USD $500
Top Trader Portfolios:                          USD $5,000
CopyTrader (por trader):                        USD $200
  → mínimo por posición copiada dentro:         USD $1
  → posiciones copiadas < $1 NO se abren (se descartan silenciosamente)
```

**Consecuencia operativa para el allocate_portfolio:**

- Si la asignación a **un ticker** en eToro es < USD $10 → la
  asignación es **imposible de ejecutar**. Redimensionar: o subir peso,
  o consolidar en menos posiciones, o cambiar a otro venue.
- Si la asignación a **copiar un trader** es < USD $200 → idem. Es
  frecuente con capital < USD $1,000 + perfil diversificado.
- Si la asignación a **Smart Portfolio** es < USD $500 → idem.
- CFD con leverage 2x y peso $25: el margen es $25 (válido porque
  supera $50 de notional), pero la liquidación está mucho más cerca.
  Ver `equity_skill` y `forex_skill` para leverage rules.

### 1.4 Spreads y comisiones (para el plan)

```
Stocks / ETFs spot (activo real):
  Comisión US stocks:  $0 por trade (commission-free)
  Spread:              el del mercado, eToro NO añade markup sobre spot
  → muy competitivo para compra-venta de acciones US reales

CFDs sobre Stocks / ETFs:
  Spread opening/closing: 0.15% cada lado (sí se suma al trade)
  Stocks US con precio ≤ $3: spread fijo 2 cents por unidad
  → tener en cuenta en calculate_scenarios como fee implícito de entrada

Cripto spot:
  Spread:              1.0% por lado (1% al comprar + 1% al vender)
  CFD cripto:          1.0% opening + 1.0% closing
  Transfer a wallet externa: 2% fee (Club member discounts aplican)
  → 1% es ALTO comparado con Binance (0.075-0.1%). Si el usuario tiene
    Binance, el skill debe recomendar cripto spot en Binance, no eToro,
    salvo que la razón sea copy trading o "todo en una plataforma".

Forex CFD (spread base, competitivo pero no raw):
  EUR/USD:  desde 1.0 pip
  USD/JPY:  desde 1.0 pip
  GBP/USD:  desde 2.0 pips
  AUD/USD:  desde 1.5 pips
  EUR/GBP:  desde 1.5 pips
  → ver forex_skill para la tabla completa y comparación vs Capital.com

Commodities CFD:
  XAU/USD (oro):   spread ~45 pips (ALTO vs brokers dedicados ~15-20 pips)
  WTI:             spread 5 cents
  → eToro no es óptimo para commodities; advertir si el plan los incluye

Índices CFD:
  S&P 500 (SPX500): spread 0.75 puntos
  NASDAQ 100:       spread 1.0 puntos
  GER40 (DAX):      spread 2.0 puntos
```

### 1.5 Fees no-trading (erosionan rendimiento, incluirlos)

```
Retiro:              USD $5 flat por retiro (cualquier monto)
Mínimo retiro:       USD $30
Conversión FX:       50 pips al depositar/retirar en moneda ≠ USD
Inactividad:         USD $10/mes tras 12 meses sin login
Overnight CFD:       0.015%/día × apalancamiento × notional (aprox)
                     weekend: triple (viernes 22:00 UK cobra x3)
Dividendos:          se pagan netos de la retención del país emisor, según aplique.

```

**Regla de integración con `calculate_scenarios`:**

```
Para posiciones CFD en eToro:
  monthly_cost_usd = notional × leverage × 0.015% × 30 (ya usado por equity_skill)
  
```

### 1.6 Activos disponibles desde Colombia (universo nominal)

```
Stocks:        ~3,000 globales, 20 bolsas (principalmente US, UK, Alemania, HK)
ETFs:          ~264 (iShares, Vanguard, SPDR, ARK, etc.)
Crypto:        ~100 tokens (BTC, ETH, SOL, ADA, DOT, LINK, MATIC, ...)
               → verificar siempre con gate; la lista cambia por región
Forex:         ~55 pares (majors + minors + algunos exóticos)
Commodities:   32 (XAU, XAG, WTI, Brent, natgas, agrícolas)
Índices:       13 (SPX500, NAS100, GER40, UK100, ...)
```

**Regla:** este número es referencial. El **gate de search_instruments
es la única fuente de verdad** por ticker (ver skills verticales).

---

## 2. Binance — Reglas operativas desde Colombia

### 2.1 Depósito COP (orden de preferencia)

```
1. PSE (Banca en Línea) — recomendado por defecto
   Fee:      0% Binance, 0-$1 el banco CO según política
   Tiempo:   1-2 días hábiles (no es instantáneo, advertirlo al usuario)
   Mínimo:   ~50,000 COP (varía)
   Bancos:   Bancolombia, Davivienda, BBVA, Banco de Bogotá,
             Banco Popular, Av Villas, Colpatria y mayoría de PSE
   Cómo:     App Binance → [Depositar] → [Depositar COP] → [Online Banking (PSE)]

2. Tarjeta débito/crédito (Visa/Master)
   Fee:      ~1.8-2.0% Binance + spread del emisor CO
   Tiempo:   Instantáneo
   Bancos:   depende del banco; algunos bloquean compras en exchanges
   → solo recomendar si el usuario necesita cripto "hoy" y PSE no es
     viable por horario/banco

3. P2P (Compra a otro usuario, pago bancario o wallet digital)
   Fee:      0% Binance (el maker paga una comisión pequeña)
   Tiempo:   Minutos a ~1 hora (depende del vendedor)
   Spread:   ~0.5-2% sobre el mid-market, varía por vendedor y liquidez
   Métodos:  Bancolombia, Nequi, Daviplata, Banco de Bogotá,
             Efecty (efectivo), Transfiya, otros
   → usar P2P cuando el usuario quiere mejor tasa COP/USDT que la
     del spot o cuando PSE no sea viable
```

**Recomendación default del agente cuando el usuario dice "deposito por
primera vez en Binance desde Colombia":** PSE para la primera vez (más
simple, sin negociación con contraparte). P2P cuando el usuario ya está
cómodo con la plataforma y busca mejor tasa.

### 2.2 Retiro a peso colombiano

```
1. Transfiya (Banca en línea, retiro local)
   Fee:      pequeño fee de red + comisión de Binance (baja)
   Tiempo:   minutos a horas
   Bancos:   los que soportan Transfiya (Bancolombia, Davivienda,
             BBVA, Banco de Bogotá, Nequi, Daviplata, etc.)
   Requisito: el número de celular registrado en Binance debe
             coincidir con el asociado a Transfiya en el banco
   Cómo:     Wallet → Fiat and Spot → [Withdraw] → COP →
             método "Online Banking (Transfiya)"

2. P2P (Vender USDT a otro usuario, recibir en banco/wallet)
   Fee:      0% Binance; el spread negociado con el vendedor es el costo
   Tiempo:   minutos a ~1 hora
   Spread:   ~0.3-1.5% vs mid-market (mejor que Transfiya para montos
             grandes y usuarios con historial)
   → default para retiros > 2M COP

3. Binance Pay + servicio independiente
   → existe pero es un servicio de tercero con horario restringido
   → el agente NO lo recomienda por defecto; mencionar solo si pregunta
```

### 2.3 Pares COP directos (cambia con frecuencia — verificar)

```
Binance Colombia ofrece pares con COP solo en P2P, no en spot trading.
El spot market de Binance NO tiene par USDT/COP ni BTC/COP como tal.

Flujo real desde COP:
  COP (tu banco) ──PSE──> COP (Binance fiat wallet) ──Buy Crypto──> USDT
    luego: USDT ──Convert / Spot Trading──> BTC / ETH / SOL / ...

Par USDT/COP aparece en P2P con cientos de ofertas.
Par BTC/COP aparece en P2P pero con liquidez mucho menor.

CONSECUENCIA PARA EL PLAN:
  El agente NO sugiere "compra el par X/COP en spot" para ningún crypto.
  La ruta canónica COP → crypto es:
    1. PSE → COP en fiat wallet  (o P2P → USDT directo)
    2. COP → USDT (si no llegó como USDT por P2P)
    3. USDT → crypto objetivo en spot
```

### 2.4 Activos y pares spot disponibles desde Colombia

```
Binance Colombia opera como Binance.com (NO como Binance US).
Universo aproximado desde CO:
  ~350 criptos listadas
  ~1,500 pares spot activos
  Stablecoins principales: USDT, USDC, FDUSD, DAI

Tokens confirmados disponibles desde CO (referencia, no exhaustivo):
  BTC, ETH, SOL, BNB, XRP, ADA, DOGE, TRX, AVAX, LINK, DOT,
  MATIC/POL, LTC, BCH, ATOM, NEAR, ARB, OP, APT, SUI, TON,
  HBAR, FIL, ICP, AAVE, MKR, UNI, LDO, RUNE, INJ, PEPE

Productos derivados:
  Futures USDⓈ-M: sí disponible desde CO
  Futures COIN-M: sí disponible desde CO
  Options:        disponible (liquidez limitada salvo BTC/ETH)
  Margin trading: disponible
  Copy Trading (Binance):    disponible
  Simple Earn flexible:      disponible para USDT, USDC, BNB, ETH, ...
  Simple Earn locked:        disponible (APY más alto, locks 15/30/60/90d)
  ETH Staking (Binance Earn): disponible
  Launchpool / Megadrop:     disponible

Tokens NO disponibles o con restricciones variables (verificar antes
de cualquier recomendación concreta):
  → Algunos tokens se desactivan por monitoreo (Binance "Seed Tag" o
    "Monitoring Tag") en determinadas jurisdicciones.
  → Si el plan propone un token fuera de los "confirmados" de arriba,
    el agente debe validarlo antes (ver 2.5).
```

### 2.5 Validación de disponibilidad Binance (sin MCP dedicado)

Hoy **no hay MCP de Binance conectado** (a diferencia de eToro). Para
validar disponibilidad de un token:

```
Si el plan propone un token en Binance que NO está en la lista
"confirmados desde CO" (sección 2.4):
  1. Declararlo al usuario como "disponibilidad a verificar"
  2. Instrucción al usuario: "Antes de depositar, busca <TOKEN>/USDT
     en binance.com — si el par aparece y permite 'Spot Trade', está
     operable desde tu cuenta"
  3. NO calcular escenarios con supuestos de precio si el token no
     se pudo validar — pedir al usuario que confirme primero

Alternativa agéntica (si el stack ya tiene CoinGecko MCP):
  coingecko.get_id_coins(id="<coingecko_id>")
    → revisar campo tickers[], filtrar por market.name == "Binance"
    → si hay par <TOKEN>/USDT en Binance con trust_score = green,
      aceptar como disponible
```

### 2.6 Comisiones Binance (plan debe incluirlas)

```
Spot trading (default, sin BNB):
  Maker:  0.1%
  Taker:  0.1%

Con pago de fees en BNB (holding + opt-in):
  Maker:  0.075%  (25% de descuento)
  Taker:  0.075%

Futures (sin BNB):
  USDⓈ-M Maker:  0.02%
  USDⓈ-M Taker:  0.05%
  COIN-M Maker:  0.02%
  COIN-M Taker:  0.05%

Con BNB (descuento 10% en futures):
  USDⓈ-M Maker:  0.018%
  USDⓈ-M Taker:  0.045%

P2P:
  Taker: 0%
  Maker: comisión pequeña variable (típicamente < 0.5%)

Convert (conversión directa sin orderbook):
  0% comisión explícita, costo embebido en el spread (~0.1-0.3%)
  → cómodo para cantidades pequeñas o primeros pasos

Simple Earn / Staking / Launchpool:
  0% comisión de suscripción y redención
  Rendimiento neto = APY publicado (es el neto al usuario)

Retiro crypto on-chain:
  depende del token y la red — BTC (Bitcoin) ~0.0002 BTC,
  USDT (BSC o Polygon) ~0.1-0.3 USDT, ETH (Ethereum L1) ~0.001-0.003 ETH
  → advertir al usuario de elegir bien la red antes de retirar
  → ERC20 es caro; BSC / Polygon / Arbitrum mucho más barato
```

**Regla de integración:**

```
En calculate_scenarios para posiciones en Binance (spot crypto):
  fee_entrada = monto × 0.001           (0.1% taker, worst case)
  fee_salida  = monto_final × 0.001
  → incluir como descuento al rendimiento base, no como monthly_cost_usd
    (a diferencia de CFDs de eToro, Binance spot no tiene overnight)

Para Binance Simple Earn:
  APY publicado es el neto al usuario → usar tal cual en calculate_scenarios

Para Binance Futures:
  fee por trade = notional × 0.0005 (taker USDT-M sin BNB)
  funding rate cada 8h — si vas a mantener > 24h, advertir que puede
  sumar/restar entre -0.3%/día y +0.3%/día según mercado
```

### 2.7 Custodia y seguridad

```
Binance es CEX custodial. El usuario no tiene las claves privadas
mientras los fondos estén en la plataforma.

Recomendaciones por monto (advertir siempre, no obligatorio):
  < $1,000 USD en crypto:   aceptable mantener todo en Binance
  $1,000 - $10,000:         considerar hardware wallet (Ledger Nano)
                            para el 50%+ del crypto no-stablecoin
  > $10,000:                hardware wallet obligatorio en el plan
                            mantener en Binance solo el trading + earn

Para DeFi (Aave, Lido, Ethena) hay que sacar de Binance a una wallet
EVM (MetaMask) — ver defi_skill.md para red y costos de gas.
```

---

## 3. Decisión de venue (eToro vs Binance) — árbol de decisión

Cuando el allocate_portfolio asigna capital a un vertical y el venue
no está forzado por el usuario, aplicar:

```
VERTICAL = "equity" o "etf":
  → eToro por defecto
    (Binance no lista acciones ni ETFs tradicionales)
    Excepción: tokenized stocks en Binance → NO recomendar,
    liquidez y régimen fiscal poco claros desde CO

VERTICAL = "defi" o "crypto":
  Si el token es BTC, ETH, u otros majors Y el plan es hold/earn:
    → Binance (spread 0.1% << eToro 1%)
  Si el plan incluye staking / Simple Earn:
    → Binance (eToro no ofrece staking nativo en todos los tokens)
  Si el plan es hold puro de cripto dentro de una estrategia
  multi-vertical en eToro ("todo en una sola plataforma"):
    → eToro, con nota explícita: "el spread de 1% en eToro vs
      0.1% en Binance representa una diferencia de X USD en la
      entrada + salida; aceptable si la prioridad es centralizar."
  Si el plan toca DeFi on-chain (Aave, Lido, Ethena):
    → Binance como onramp (COP → USDT), luego retirar a MetaMask

VERTICAL = "forex":
  Si el usuario tiene solo eToro:
    → eToro (con spreads de la tabla 1.4)
  Si el usuario aún no tiene cuenta forex:
    → Capital.com por defecto (PSE directo, spreads más bajos;
      ver forex_skill.md)
    → eToro solo si el usuario ya tenía la cuenta o quiere
      centralizar con copy trading

VERTICAL = "social" (copy trading):
  → eToro (Binance tiene copy pero el universo de traders y la
    interfaz de eToro siguen siendo superiores; además el
    MCP etoro-server soporta este flujo)

VERTICAL = "commodities":
  → NO eToro salvo que esté forzado. Spread XAU 45 pips vs 15-20
    en Capital.com. Advertir al usuario.
```

---

## 4. Validación de mínimos en el plan — TOOL DETERMINÍSTICA

> **Cambio v2:** esta sección antes describía el algoritmo en prosa y
> dependía de que el agente lo recordara. Ahora es una **tool del MCP
> propio** que SIEMPRE se llama después de `allocate_portfolio` y
> ANTES del gate de `search_instruments`. No es opcional: el plan no
> avanza a generación de JSX si esta tool devuelve `is_valid: false`
> y no se aplicó `adjusted_allocation_usd` o una de las `suggestions`.

### 4.1 Cómo llamarla

```
Tool:    investment-calculators.validate_allocation_minimums
Entrada: 
  allocation_usd: dict  ← directamente el campo allocation_usd
                          que devolvió allocate_portfolio
  venue_map:      dict  ← plan de ejecución por vertical (abajo)

Salida:
  is_valid:                  bool   — True si todas las posiciones cumplen mínimo
  violations:                list   — posiciones inválidas con venue, producto, gap y motivo
  suggestions:               list   — acción concreta por cada violación
                                      (consolidate / switch_venue / drop_and_redistribute / verify_venue)
  adjusted_allocation_usd:   dict   — allocation_usd corregido (solo refleja los drops;
                                      consolidate y switch_venue no mueven capital entre verticales)
  allocation_changed:        bool
  normalization_warnings:    list   — pesos dentro del vertical que no sumaban 1.0 y fueron normalizados
  unknown_venues:            list   — venues fuera de la tabla de mínimos conocidos
  summary:                   str    — texto listo para mostrar al usuario
```

### 4.2 Cómo construir `venue_map`

Un vertical puede mapear a **uno o varios buckets** (p. ej. DeFi dividido
entre Binance spot y Aave supply). Cada bucket declara venue, tipo de
producto, número de posiciones y su peso dentro del vertical.

```python
venue_map = {
  "equity": [
    {"venue": "eToro",   "product_type": "stock_spot",   "num_positions": 3, "weight_within_vertical": 1.0}
  ],
  "defi": [
    {"venue": "Binance", "product_type": "spot_crypto",  "num_positions": 2, "weight_within_vertical": 0.7},
    {"venue": "Aave",    "product_type": "supply",       "num_positions": 1, "weight_within_vertical": 0.3}
  ],
  "forex": [
    {"venue": "Capital.com", "product_type": "cfd_forex","num_positions": 1, "weight_within_vertical": 1.0}
  ],
  "social": [
    {"venue": "eToro",   "product_type": "copy_trader",  "num_positions": 1, "weight_within_vertical": 1.0}
  ],
  "reserve": [
    {"venue": "Binance", "product_type": "simple_earn",  "num_positions": 1, "weight_within_vertical": 1.0}
  ],
}
```

`product_type` válidos (coincidir exactamente con la tabla `VENUE_MINIMUMS_USD` del server):

| Venue | product_type |
|---|---|
| eToro | `stock_spot`, `etf_spot`, `crypto_spot`, `cfd_stock`, `cfd_etf`, `cfd_crypto`, `cfd_forex`, `cfd_commodity`, `cfd_index`, `copy_trader`, `smart_portfolio`, `top_trader_portfolio` |
| Binance | `spot_crypto`, `simple_earn`, `futures`, `staking`, `copy_trading` |
| Capital.com | `cfd_forex`, `cfd_commodity`, `cfd_stock`, `cfd_index` |
| Aave | `supply`, `borrow` |
| Lido | `stake_eth` |
| Ethena | `susde` |

Los mínimos exactos viven en `mcp-server/server.py` → `VENUE_MINIMUMS_USD`.
**Si un mínimo cambia en la plataforma real, se actualiza AHÍ**, no en
prosa aquí; este skill solo explica la tabla y cómo llamar la tool.

### 4.3 Qué hacer con cada acción devuelta

```
action = "consolidate"
  → Reducir num_positions para ese bucket al valor `to_positions`
    antes de presentar el plan. El capital del vertical no cambia,
    solo cuántas posiciones se abren.
  → Ej: 5 tickers US de $6 c/u → 3 tickers US de $10 c/u.

action = "switch_venue"
  → Cambiar el venue (y opcionalmente product_type) del bucket a los
    valores `to_venue` / `to_product_type`. El capital del vertical
    no cambia. Requiere avisar al usuario: "movimos forex a
    Capital.com porque en eToro el mínimo de margen ($50) no cabe
    con tu asignación ($25)".

action = "drop_and_redistribute"
  → Eliminar el bucket. `adjusted_allocation_usd` ya lo hizo: restó
    ese capital del vertical y lo sumó a reserve. Avisar al usuario
    del cambio y por qué.

action = "verify_venue"
  → El agente propuso un venue que no está en la tabla. Opciones:
    (1) corregir a un venue canónico del stack (eToro/Binance/
    Capital.com/Aave/Lido/Ethena), o (2) pedir al mantenedor
    añadirlo a `VENUE_MINIMUMS_USD`. No presentar plan con venues
    no validables.

action = "fix_product_type"
  → El agente escribió un product_type no existente para ese venue.
    Corregir antes de reintentar.
```

### 4.4 Flujo integrado (obligatorio)

```
1. allocate_portfolio(...)            → allocation_usd por vertical
2. construir venue_map según §3       (árbol de decisión eToro/Binance/Capital.com)
3. validate_allocation_minimums(
     allocation_usd=...,
     venue_map=...
   )                                  → is_valid + violations + suggestions
4. Si is_valid == False:
     Aplicar suggestions (consolidate / switch / drop) o usar
     adjusted_allocation_usd.
     REVALIDAR llamando la tool otra vez con el plan corregido.
5. Solo cuando is_valid == True:
     → pasar al gate de search_instruments de los skills verticales
     → luego a calculate_scenarios, stress_test_portfolio, etc.
     → finalmente a plan_template.md para generar JSX.
```

### 4.5 Por qué una tool y no prosa

- **Determinístico:** el plan se bloquea si falla, no depende de que
  el agente recuerde revisar.
- **Single source of truth:** los mínimos viven en el server, no
  duplicados en prosa de varios skills.
- **Trazable:** el usuario puede ver violations/suggestions tal como
  vinieron de la tool; no es "opinión" del agente.
- **Actualizable:** si eToro cambia copy_trader de $200 a $250, se
  cambia UN valor en `VENUE_MINIMUMS_USD` y se propaga a todo el
  sistema.

---

## 5. Costos de entrada/salida a agregar al `plan_template.md`

Para que el checklist final ("% rendimiento base ≥ mínimo ajustado por
capital") refleje la realidad, incluir como descuento al rendimiento
bruto:

```
Depósito:
  eToro vía tarjeta CO:      -3% a -5% (FX markup del emisor)
  Binance vía PSE:           -0% (PSE transparente)
  Binance vía tarjeta:       -1.8% a -2% + FX del emisor
  Binance vía P2P:           -0.5% a -2% (spread sobre mid)

Trade (ida y vuelta):
  eToro acciones US spot:    0% comisión; spread de mercado
  eToro CFD stock:           -0.30% (0.15% open + 0.15% close)
  eToro crypto spot:         -2.0% (1% open + 1% close) ← ALTO
  eToro forex CFD:           ~1-2 pips × 2 (spread base)
  Binance spot:              -0.20% (0.1% taker × 2)
  Binance spot con BNB:      -0.15% (0.075% × 2)
  Binance futures USDT-M:    -0.10% (0.05% × 2, sin funding)

Retiro:
  eToro:                     -$5 flat + FX de salida (50 pips)
  Binance via Transfiya:     ~0.1-0.5%
  Binance via P2P:           0.3-1.5% spread
```

**Regla:** el escenario BASE en `plan_template.md` debe presentarse
**neto de todos los costos anteriores**, no bruto. Si el rendimiento
base proyectado bruto es +25% pero los costos totales suman -3%, el
número a mostrar en la tabla es +22% (con una fila adicional "costos
de entrada/salida: -3%").

---

## 6. Preguntas frecuentes del usuario (respuestas plantilla)

### "¿Puedo depositar con PSE en eToro?"

> No. eToro no tiene integración PSE desde Colombia. Las opciones
> son tarjeta débito/crédito (que hace la conversión COP→USD a la
> tasa de tu banco), PayPal o transferencia bancaria internacional
> (desde USD $500 y toma 4-7 días). Si necesitas PSE directo, Binance
> sí lo tiene y Capital.com también (este último para forex).

### "¿Cuánto es lo mínimo para empezar en eToro desde Colombia?"

> USD $50 para el primer depósito (vía tarjeta, PayPal o Skrill).
> A partir de ahí puedes abrir posiciones desde USD $10 en acciones,
> ETFs o cripto. Copy Trading requiere USD $200 por cada trader que
> copies. Smart Portfolios USD $500.

### "¿Por qué Binance no muestra el par BTC/COP en spot?"

> Binance tiene pares COP solo en el mercado P2P, no en el orderbook
> spot. Para comprar BTC con pesos, la ruta es: depositas COP vía
> PSE → compras USDT con esos pesos (o recibes USDT directamente vía
> P2P) → intercambias USDT por BTC en spot. Suena a más pasos, pero
> cada uno toma segundos salvo el PSE inicial que puede tomar 1-2
> días hábiles.

### "¿Cuál es más barato para comprar crypto, eToro o Binance?"

> Binance — de lejos. eToro cobra 1% al comprar y 1% al vender crypto
> (total 2% round trip). Binance cobra 0.1% al comprar y 0.1% al
> vender (0.2% round trip), y con BNB baja a 0.15%. Sobre USD $500 de
> crypto, son ~USD $10 en eToro vs ~USD $1 en Binance. eToro tiene
> sentido si quieres todo centralizado o usar copy trading; Binance
> si solo quieres hold/trade crypto puro.

### "¿Retiro mis pesos a Bancolombia/Nequi/Daviplata de Binance?"

> Sí. Ruta rápida: Wallet → Fiat and Spot → Withdraw → selecciona
> COP → método "Online Banking (Transfiya)" → confirma que tu celular
> registrado en Binance es el mismo que tienes en Transfiya en el
> banco. Llega en minutos. Para montos grandes (> 2M COP) suele
> convenir P2P: vendes USDT en P2P eligiendo "Bancolombia" o "Nequi"
> como método, el comprador te transfiere, tú liberas el USDT. Mejor
> tasa pero requiere 15-45 min activos en la pantalla.

---

## 7. Lo que NO hace este skill

- ❌ Sustituir el gate de `search_instruments` de eToro. Los skills
  verticales siguen corriendo gate porque disponibilidad y tradability
  cambian en tiempo real.
- ❌ Validar pares en Binance en tiempo real (no hay MCP conectado hoy).
  Se apoya en la lista 2.4 + validación manual del usuario.
- ❌ Negociar ofertas P2P por el usuario. Solo explica el flujo.
- ❌ Sugerir "ganar dinero con arbitraje entre exchanges CO" — fuera
  de scope; riesgos operacionales altos.
- ❌ Recomendar evadir restricciones jurisdiccionales (usar VPN,
  cuentas de terceros, etc.). Si un activo no está disponible desde
  CO, se sustituye o se quita del plan.

---

## 8. Auto-chequeo antes de presentar un plan que toca estas plataformas

Antes de la salida JSX del `plan_template`, confirmar:

1. ¿Se llamó `validate_allocation_minimums` con el `allocation_usd`
   de `allocate_portfolio` y un `venue_map` completo, y devolvió
   `is_valid: true`? (ver §4 — esta checkpoint NO es opcional)
2. ¿Cada posición en Binance tiene un par viable y el token está
   en la lista confirmada o fue validado con el usuario?
3. ¿El flujo de entrada está claro (PSE, tarjeta o P2P) y sus costos
   están incluidos en el escenario base?
4. ¿El flujo de salida está claro (Transfiya, P2P, wire) con sus fees?
5. ¿El spread del vertical correcto está aplicado (1% crypto eToro,
   0.1% crypto Binance, etc.)?
6. ¿Los overnight fees de CFDs están en `monthly_cost_usd`?
7. ¿Si hay capital < $1,000, el número de posiciones es ≤ 3-4 para
   no violar mínimos? (la tool del §4 lo valida, pero mantener
   el instinto de diseño simple en capital bajo)

Si alguna es "no", el plan se ajusta antes de generar JSX.
