# Skill: Agente de cripto, staking y DeFi — v2

## Cuándo se activa

## Interacción con technical_skill.md

technical_skill SOLO aplica si el plan incluye compra direccional de
cripto spot (BTC, ETH, SOL) esperando subida de precio. En ese caso,
pasar los datos de CoinGecko (OHLC) a technical_skill y recibir
entrada, SL y TP técnicos.

technical_skill NO aplica a:
  - Stablecoin lending (USDC en Binance Simple Earn, Aave)
  - ETH/BTC staking (rendimiento del protocolo, no del precio)
  - Yield farming / LP
  - Ethena sUSDe (delta-neutral, no direccional)

Para estos casos, technical_skill responderá "no aplica" y el plan
usa solo el análisis de TVL/APY/riesgo de protocolo que ya existe en
este skill.


Automáticamente cuando:
- El allocate_portfolio asigna capital a "defi"
- El usuario menciona cripto, staking, yield, DeFi, Binance, Ethereum, Bitcoin
- El plan necesita una posición de rendimiento en dólares estables

## 🚪 Gate de disponibilidad eToro (para cripto spot en eToro)

**Cuándo aplica:** solo si el plan propone **comprar cripto vía eToro**
(no aplica a posiciones nativas en Binance, Aave, Lido, MetaMask, etc.).

eToro tiene restricciones fuertes de cripto por jurisdicción: desde
Colombia, muchos tokens listados en otras regiones **no son operables**.
Antes de sugerir comprar BTC/ETH/SOL/cualquier token en eToro, pasar
el gate.

### Protocolo
```
POR CADA token que se vaya a operar EN eToro:

  etoro-server.search_instruments(
    query="<SYMBOL>",        # ej. "BTC", "ETH", "SOL"
    search_by="internalSymbolFull",
    page_size=5
  )

Validar en el primer resultado cuyo symbol coincida:

  ✅ instrumentType == "Crypto"
  ✅ isCurrentlyTradable == true
  ✅ isBuyEnabled == true

Si falla:
  → el token NO se puede comprar en eToro desde esta cuenta
  → sugerir la alternativa nativa (Binance Simple Earn, CEX regulado)
  → O reemplazar por un token equivalente que sí pase el gate
  → informar al usuario del cambio y la razón
```

### Cuándo el gate NO aplica
- Posiciones en Binance (CEX separado, universo distinto).
- Staking / lending on-chain (Aave, Lido, Ethena) — ahí la disponibilidad
  depende del protocolo y la red, no de eToro.
- Recomendaciones puramente educativas sin propuesta de compra concreta.

Si el plan es híbrido (ej. "parte en eToro, parte en Binance"), el gate
solo corre sobre la porción eToro.

## Lógica de decisión autónoma

### Selección de estrategia según perfil + capital
```
SI principiante Y capital DeFi < $200:
  → SOLO Binance Simple Earn con USDC flexible
  → NO recomendar MetaMask, Aave directo, ni nada on-chain
  → Razón: la complejidad de wallets + gas es contraproducente para < $200

SI principiante Y capital DeFi >= $200:
  → Binance Simple Earn USDC ($120) + Binance ETH Staking ($80)
  → Mencionar Aave/Lido como "siguiente paso en mes 4"

SI intermedio:
  → Lending stablecoins en Aave (Polygon para gas bajo) + Lido stETH
  → Mencionar composición stETH+Aave como opción avanzada

SI avanzado:
  → Aave lending + Lido + considerar Ethena sUSDe + Yearn vaults
  → Incluir cálculo de impermanent loss si hay LP
```

### Decisión de red automática
```
→ Consultar gas actual (o estimar: ETH mainnet ~$5-20, Polygon ~$0.01, Arbitrum ~$0.10, BSC ~$0.05)

SI capital_defi * 0.05 < gas_estimado_ethereum:
  → NO recomendar Ethereum mainnet
  → Recomendar Polygon o Arbitrum para Aave
  → O recomendar Binance Simple Earn (gas = $0)
  → Explicar: "En Ethereum el costo de una transacción es ~$X, que sería el Y% de tu inversión. En Polygon es centavos."

SI capital_defi > $1000:
  → Ethereum mainnet es viable (gas < 2% del capital)
```

### Validación de seguridad (ejecutar SIEMPRE)
```
Para cada protocolo DeFi recomendado:
→ Consultar DeFiLlama: TVL actual

SI TVL < $100M:
  → NO recomendar
  → Buscar alternativa con mayor TVL

SI TVL entre $100M y $500M:
  → Recomendar con warning: "Este protocolo es mediano. Invertir máximo 10% del capital DeFi aquí"

SI TVL > $1B:
  → Recomendar con confianza: "Protocolo grande y establecido"
```

### APY sospechoso
```
SI APY de un pool > 25%:
  → Ejecutar calculate_risk_score con volatility alta
  → Agregar warning: "Un rendimiento tan alto generalmente viene de incentivos temporales que pueden bajar rápidamente"
  → Recomendar máximo 5-10% del capital DeFi en este pool

SI APY > 50%:
  → NO recomendar para perfiles moderados
  → Para agresivos: solo con warning explícito y máximo 5% del capital

SI APY > 100%:
  → NO recomendar NUNCA — probable ponzi o incentivos insostenibles
```

## Datos a obtener

### DeFiLlama (para yields y TVL)
- Consultar pools: filtrar por chain, project, y TVL > $100M
- Datos relevantes: apy_base, apy_reward, tvl_usd, audited

### CoinGecko (para precios de cripto)
- ETH: precio actual, cambio 24h/7d/30d
- SOL: precio actual
- USDC: verificar que mantiene paridad ($1 ± $0.01)

### eToro (solo si se opera en eToro)
- Pasar el gate de arriba
- `get_rates(instrument_ids=[...])` para el precio en eToro (puede diferir del spot)

## Estrategias disponibles (ordenadas por riesgo)

### Nivel 1 — Stablecoins lending (riesgo 2-3/10)
- **Qué**: prestar USDC/USDT, ganar interés. Capital no fluctúa.
- **Dónde**: Binance Simple Earn (simple) o Aave Polygon (mejor APY)
- **APY**: 3-8%
- **Para quién**: todos los perfiles, base segura del portafolio DeFi
- **Escenarios con** `calculate_scenarios`: amount, apy=APY_actual, volatility=0.01, passive=0

### Nivel 2 — ETH Staking (riesgo 5-6/10)
- **Qué**: ayudar a validar Ethereum, ganar rewards. PERO el precio de ETH fluctúa.
- **Dónde**: Binance ETH Staking (simple) o Lido (stETH, más flexible)
- **APY staking**: ~2.7% FIJO + variación de precio de ETH
- **Para quién**: moderados y agresivos
- **Escenarios con** `calculate_scenarios`: amount, apy=0.027, volatility=0.60, passive=amount*0.027

### Nivel 3 — Liquid staking compuesto (riesgo 6-7/10)
- **Qué**: stakear ETH → stETH → depositar en Aave como colateral
- **APY combinado**: 5-7%
- **Para quién**: intermedios y avanzados (mes 4+)
- **Riesgo extra**: liquidación si ETH cae mucho + smart contract risk compuesto

### Nivel 4 — Delta-neutral (riesgo 5-6/10)
- **Qué**: Ethena sUSDe — usa funding rates para rendimiento sin exposición a precio
- **APY**: 8-12%
- **Para quién**: intermedios y avanzados
- **Riesgo**: depende de funding rates positivos

### Nivel 5 — Yield farming LP (riesgo 7-9/10)
- **Qué**: proveer liquidez en DEXs
- **APY**: 5-25%+ pero con impermanent loss
- **Para quién**: SOLO avanzados, SOLO pools de stablecoins para moderados
- **NUNCA recomendar a principiantes**

## Cálculos obligatorios por posición
0. Si se opera en eToro → **Gate eToro** (arriba) antes de seguir
1. 🧭 Si la posición es cripto spot direccional (no stablecoin/staking):
     → technical_skill.md para entrada/SL/TP sobre el OHLC de CoinGecko.
     → Si la posición NO es direccional (USDC lending, ETH staking en
       Lido, LP), saltar este paso y documentarlo.
2. `calculate_scenarios` con APY y volatilidad del activo
3. `calculate_risk_score` — para stablecoins: vol=0.01, dd=-0.02. Para ETH: vol=0.15, dd=-0.35

## Cronograma (auto-generar según nivel)
```
SI nivel 1 (Binance Simple Earn):
  Día 3: Crear Binance + KYC (10 min + espera)
  Día 4: Depositar via P2P en pesos (~0.5% spread)
  Día 4: Convertir USDT → USDC en Binance Convert ($0)
  Día 4: Earn > Simple Earn > USDC > Flexible (2 min)
  Listo. Ganando intereses automáticamente.

SI nivel 2 (ETH staking en Binance):
  Igual que nivel 1 pero: Convertir a ETH → Earn > ETH Staking

SI nivel 2 (Lido directo):
  Día 5: Instalar MetaMask, enviar ETH desde Binance
  Día 5: Ir a stake.lido.fi, conectar wallet, stakear
  (incluir instrucciones detalladas solo si usuario lo pide)
```

## Explicación adaptativa
```
SI principiante:
  "Imagina que tienes dólares digitales (USDC, siempre valen $1) y los pones en una plataforma donde otros los piden prestados. Te pagan interés por usar tu dinero. Es como ser el banco: tú prestas, ellos pagan. Y puedes retirar cuando quieras."

SI intermedio:
  "USDC en Aave v3 en Polygon: supply APY actualmente ~X%. Sin impermanent loss, retiro flexible. Gas de ~$0.01 por transacción."

SI avanzado:
  "Considerar looping stETH en Aave: deposit stETH → borrow ETH al 80% LTV → stake en Lido → repeat. APY efectivo ~5-7% pero con riesgo de liquidación si stETH depeg > 5%."
```

## Red flags (NUNCA recomendar)
- APY > 100% sin fuente clara de yield
- Protocolos con < 3 meses de operación
- TVL < $100M
- Tokens que debas comprar para "entrar" al pool
- Protocolos sin auditorías verificables
- Cualquier cosa que requiera "invitar amigos" para ganar más
- Tokens que no pasan el gate eToro si el plan los sitúa en eToro
  (no "truquear" moviéndolos a otro venue sin avisar al usuario)
