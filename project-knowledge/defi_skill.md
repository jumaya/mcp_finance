# Skill: Análisis de cripto, staking y DeFi

## Cuándo aplicar
Cuando el usuario quiere invertir en criptomonedas, staking, lending de stablecoins o yield farming.

## Estrategias por riesgo (menor a mayor)

### 1. Lending stablecoins (riesgo bajo-moderado)
- Prestar USDC/USDT en Aave, ganar interés. USDC siempre vale ~$1.
- APY: 3-8%. Protocolos: Aave, Compound. Simple: Binance Simple Earn.

### 2. Staking directo (riesgo moderado)
- ETH en Binance: ~2.5% APY. ETH via Lido (stETH): ~2.7%. SOL: ~6-7%.
- RIESGO: el token puede bajar. El reward es fijo, el precio no.

### 3. Liquid staking compuesto (riesgo moderado-alto)
- Stakear ETH en Lido → stETH → depositar en Aave como colateral. APY: 5-7%.
- Solo para usuarios que ya entienden DeFi (mes 4+).

### 4. Delta-neutral (riesgo moderado)
- Ethena (sUSDe): ~8-12% APY via funding rates. Baja correlación con mercado.

### 5. Auto-compound vaults (riesgo medio-alto)
- Yearn, Beefy: APY 10-25%. Riesgo de smart contract compuesto.

### 6. Yield farming LP (riesgo alto)
- Uniswap, Curve, PancakeSwap. APY 5-25%+ pero impermanent loss.
- Solo pools de stablecoins para perfil moderado.

## Proceso
1. Obtener yields: DeFiLlama para APY y TVL de pools
2. Seguridad: solo protocolos con TVL > $100M y auditorías
3. Regla de gas: si gas fee > 5% del capital, recomendar otra red o exchange
4. Escenarios: `calculate_scenarios`. Stablecoins: volatilidad ~0.01. ETH: ~0.60
5. Impuestos: `calculate_tax_impact` tipo "crypto_staking" o "defi_yield"

## Plataformas por nivel
| Nivel | Plataforma | Qué hace | Gas |
|-------|-----------|----------|-----|
| Principiante | Binance Simple Earn | Staking/lending 1 click | $0 |
| Intermedio | Lido | Liquid staking ETH | ~$5-15 |
| Intermedio | Aave (Polygon) | Lending/borrowing | ~$0.01 |
| Avanzado | Yearn | Auto-compound vaults | ~$10-30 |

## Cronograma tipo
- Día 3: Crear cuenta Binance + KYC (10 min + espera)
- Día 4: Depositar via P2P en pesos (~0.5% spread). Convertir a USDC ($0)
- Día 5 opción A: Binance Simple Earn flexible (APY ~3.5%, cero complejidad)
- Día 5 opción B: MetaMask + Aave en Polygon (APY ~4.2%, más control)

## Explicación para principiantes
"Imagina que tienes dólares digitales (USDC, siempre valen $1) y los pones en una plataforma donde otros los piden prestados. Te pagan interés por usar tu dinero, como un banco pero tú eres el banco. Puedes retirar cuando quieras y los intereses son mejores que en un banco colombiano."

## Red flags (NUNCA recomendar)
- APY > 100% sin explicación clara del origen del yield
- Protocolos con < 3 meses de operación
- Tokens que debas comprar para "entrar" (posible Ponzi)
- Protocolos sin auditorías
