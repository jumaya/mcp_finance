# Skill: Inteligencia de mercado y contexto geopolítico

## Cuándo se activa
Automáticamente SIEMPRE que el agente genera un plan de inversión o analiza un activo. Este skill es transversal — enriquece las recomendaciones de TODOS los otros skills con contexto del mundo real.

## Por qué existe este skill
Sin contexto geopolítico y macroeconómico, el agente recomienda activos "genéricos" como QQQ o VOO para cualquier perfil. Un inversor de riesgo alto NO quiere ETFs diversificados — quiere oportunidades asimétricas donde puede ganar mucho (o perder mucho). Este skill enseña al agente a pensar como un analista de inversiones real.

## Lógica de decisión por nivel de riesgo

### Riesgo BAJO → Preservar capital
```
ACTIVOS PERMITIDOS:
  - ETFs indexados amplios: VOO, VT, SCHD
  - Stablecoins lending (Aave, Binance Earn): USDC, USDT, DAI
  - ETH staking líquido (Lido): stETH
  - Copy trading de traders conservadores (drawdown < 10%)

NO INCLUIR:
  - Acciones individuales
  - Altcoins
  - Apalancamiento
  - Forex
```

### Riesgo MODERADO → Crecer con volatilidad controlada
```
ACTIVOS PERMITIDOS (todo lo de bajo +):
  - ETFs sectoriales: QQQ, XLK, ARKK
  - Acciones blue-chip individuales: AAPL, MSFT, GOOGL, AMZN
  - Cripto top 10: BTC, ETH, SOL
  - DeFi pools de bajo riesgo: stablecoins en Aave
  - Copy trading de traders moderados (drawdown < 15%)
  - Forex majors solo en demo

LÍMITES:
  - Máximo 20% en un solo activo
  - Máximo 30% en cripto
```

### Riesgo ALTO → Máximo rendimiento, acepta pérdidas significativas
```
ACTIVOS OBLIGATORIOS (el plan DEBE incluir):
  - Acciones de alto crecimiento / alta volatilidad: 
    NVDA, TSLA, AMD, PLTR, COIN, MSTR, SOFI, RIOT, MARA
  - Altcoins de alta capitalización: SOL, AVAX, LINK, DOT, NEAR, RENDER
  - Altcoins de mediana capitalización (moonshots): ARB, OP, INJ, TIA, SUI, SEI
  - DeFi yield farming en pools agresivos (APY > 10%)
  - Cripto con narrativa activa: memecoins curados, tokens de IA, DePIN
  - Copy trading de traders agresivos (rendimiento > 30% anual, acepta drawdown 20-30%)
  - Forex con apalancamiento moderado (2x-5x) en pares volátiles

DISTRIBUCIÓN SUGERIDA para $500 riesgo alto:
  - 40% cripto agresivo ($200): altcoins + DeFi yield farming
  - 30% acciones de crecimiento ($150): NVDA, TSLA, o acciones de momentum
  - 20% copy trading agresivo ($100): traders de alto rendimiento en eToro
  - 10% stablecoins lending ($50): reserva de liquidez para oportunidades

NO incluir en riesgo alto:
  - VOO, VT, SCHD (demasiado conservadores)
  - QQQ solo si es TQQQ (apalancado 3x)
  - CDTs, fondos de renta fija
  - Staking simple de ETH (rendimiento muy bajo para este perfil)

DIFERENCIADOR vs moderado:
  - En moderado: "compra ETH y haz staking" (3-4% APY)
  - En alto: "compra SOL, haz liquid staking en Marinade (7% APY), y deposita mSOL en un pool de yield farming para rendimiento adicional compuesto (15-25% APY total)"
```

## Análisis geopolítico y macroeconómico

### Factores que el agente DEBE considerar ANTES de recomendar
```
SIEMPRE consultar TradingView screener + Alpha Vantage para evaluar:

1. TENDENCIA DEL MERCADO GENERAL
   → Usar TradingView: consultar S&P 500, Nasdaq, BTC
   → SI S&P 500 RSI > 70 Y cerca de máximos históricos:
     "Mercado en zona de sobrecompra. Considerar posiciones más pequeñas o esperar corrección"
   → SI S&P 500 RSI < 30:
     "Mercado sobrevendido. Posible oportunidad de compra agresiva"
   → SI BTC dominancia > 60%:
     "Altseason improbable a corto plazo. Concentrar en BTC"
   → SI BTC dominancia < 45%:
     "Posible altseason. Aumentar peso en altcoins"

2. POLÍTICA MONETARIA (Fed/tasas de interés)
   → SI tasas subiendo o altas:
     "Presión bajista en acciones de crecimiento y cripto. Favorecer value stocks y stablecoins lending"
   → SI tasas bajando o se esperan recortes:
     "Favorable para tech y cripto. Aumentar exposición a activos de riesgo"
   → SI inflación > 3%:
     "Considerar oro (XAUUSD vía MT5), commodities, y Bitcoin como cobertura"

3. TENSIONES GEOPOLÍTICAS
   → SI hay conflicto activo (guerras, sanciones):
     "Volatilidad alta. Oportunidad para traders pero riesgo para holders. Considerar posiciones más pequeñas con stop loss definido"
   → SI hay elecciones próximas en USA:
     "Incertidumbre política. Históricamente el mercado sube después de elecciones independientemente del resultado"
   → SI hay crisis bancaria o de liquidez:
     "Flight to quality: BTC y oro suben, acciones bancarias bajan. Evitar exposición a bancos regionales"

4. REGULACIÓN CRIPTO
   → SI regulación positiva (aprobación de ETFs, claridad legal):
     "Favorable para cripto institucional: BTC, ETH, SOL"
   → SI regulación negativa (demandas SEC, prohibiciones):
     "Presión bajista corto plazo pero oportunidad de compra si fundamentales no cambian"
   → SI país específico prohíbe cripto:
     "Verificar que el activo recomendado es accesible desde Colombia"

5. NARRATIVAS DE MERCADO ACTUALES
   → Identificar las narrativas dominantes del momento:
     "IA/ML tokens", "DePIN", "RWA (Real World Assets)", "Layer 2", "Bitcoin Ordinals"
   → Para riesgo alto: SIEMPRE incluir al menos 1 posición en la narrativa dominante
   → Las narrativas cambian cada 3-6 meses — el agente debe consultar datos frescos
```

### Cómo obtener contexto actual
```
ANTES de generar cualquier plan:
  1. TradingView screener → estado del mercado general (bull/bear/neutral)
  2. Alpha Vantage → RSI y MACD del S&P 500, Nasdaq, y BTC
  3. CoinGecko → top gainers/losers 24h, tendencias, market cap total
  4. DeFiLlama → TVL total del ecosistema DeFi (creciendo o cayendo?)
  5. Yahoo Finance → próximos earnings de acciones recomendadas

SINTETIZAR en un párrafo de contexto antes del plan:
  "El mercado está en [estado]. El S&P 500 cotiza a [X] con RSI de [Y] (sobrecompra/neutro/sobreventa).
  Bitcoin está a $[Z] con dominancia de [W]%. La tendencia macro es [favorable/desfavorable] para activos
  de riesgo porque [razón]. Las narrativas dominantes son [X, Y, Z]. Basándome en este contexto..."
```

## Estrategias avanzadas para perfil agresivo

### En eToro (para perfil de riesgo alto)
```
COPY TRADING AGRESIVO:
  → Buscar traders con rendimiento > 30% anual
  → Aceptar drawdown hasta 25-30%
  → Priorizar traders que operen acciones tech y cripto
  → Copiar 2-3 traders máximo (concentración = más rendimiento)
  → NO copiar traders que solo operen forex con bajo rendimiento

ACCIONES INDIVIDUALES DE CRECIMIENTO:
  → NVDA: líder en IA/GPUs — alta volatilidad pero tendencia fuerte
  → TSLA: polarizante, movimientos de 5-10% en un día
  → COIN: proxy de cripto en el mercado de acciones
  → MSTR: apalancamiento implícito a Bitcoin
  → AMD: competencia directa de NVDA en IA
  → PLTR: contratos gobierno + IA empresarial

ETFs APALANCADOS (solo para riesgo alto):
  → TQQQ: Nasdaq 3x apalancado (NO para hold largo, solo momentum)
  → SOXL: semiconductores 3x
  → ADVERTENCIA: los ETFs apalancados pierden valor en mercados laterales por decay
```

### En Binance (para perfil de riesgo alto)
```
ESTRATEGIA CRIPTO AGRESIVA:
  Capa 1 - Core (50% del capital cripto):
    → BTC: 20% — base de cualquier portafolio cripto
    → ETH: 15% — ecosistema DeFi dominante
    → SOL: 15% — ecosistema de mayor crecimiento

  Capa 2 - Altcoins de convicción (30%):
    → Tokens de narrativa dominante actual (consultar CoinGecko trends)
    → Ejemplos por narrativa:
      - IA: RENDER, FET, OCEAN
      - Layer 2: ARB, OP, MATIC
      - DePIN: HNT, RNDR, FIL
      - Gaming: IMX, GALA, AXS
    → Máximo 5% por altcoin individual

  Capa 3 - Moonshots (10%):
    → Tokens de baja capitalización con potencial 5-10x
    → Invertir solo lo que puedas perder completamente
    → Máximo 2-3% por moonshot
    → SIEMPRE verificar: liquidez, equipo, TVL, auditorías

  Capa 4 - Yield farming (10%):
    → Stablecoins en Aave/Compound: USDC pool Polygon (3-8% APY)
    → Liquid staking: SOL en Marinade → mSOL en pool de LP
    → SIEMPRE verificar APY actual en DeFiLlama antes de recomendar
```

## Señales de entrada y salida

### Cuándo COMPRAR (señales alcistas)
```
TÉCNICAS:
  → RSI < 35 + precio en soporte → sobreventa, posible rebote
  → MACD cruce alcista + volumen creciente → confirmación de tendencia
  → Precio rompe resistencia con volumen alto → breakout

FUNDAMENTALES:
  → Earnings beat + guidance positivo → momentum de corto plazo
  → Aprobación regulatoria (ETF, licencia) → catalizador
  → Partnership o integración importante → adopción

MACRO:
  → Fed señala recortes de tasas → favorable para riesgo
  → Mercado corrige > 10% sin cambio de fundamentales → oportunidad
```

### Cuándo VENDER o reducir posición
```
TÉCNICAS:
  → RSI > 75 + volumen decreciente → agotamiento de tendencia
  → MACD cruce bajista → cambio de tendencia
  → Precio pierde soporte importante → posible caída mayor

FUNDAMENTALES:
  → Earnings miss significativo → cambio de tesis
  → Hack de protocolo DeFi → vender inmediatamente
  → Cambio regulatorio negativo directo → reducir exposición

REGLAS DE GESTIÓN:
  → Take profit parcial al +30%: vender 25-50% de la posición
  → Stop loss mental al -20%: evaluar si fundamentales cambiaron
  → Si fundamentales intactos + caída > 20%: oportunidad de DCA
  → Si fundamentales deteriorados: vender sin importar el precio
```

## Formato de recomendación enriquecida
```
Para cada activo recomendado, el agente DEBE incluir:

1. CONTEXTO DE MERCADO
   "El mercado de [sector] está en [estado] porque [razón]. Esto [favorece/desfavorece] a [activo]"

2. TESIS DE INVERSIÓN
   "Invierto en [activo] porque [razón fundamental]. El catalizador próximo es [evento/fecha]"

3. DATOS TÉCNICOS ACTUALES
   - Precio actual (via MCP)
   - RSI actual (via Alpha Vantage o TradingView)
   - Tendencia (alcista/bajista/lateral)
   - Soporte/resistencia clave

4. ESCENARIOS CON CONTEXTO
   - Optimista: "Si [evento favorable] ocurre, el precio puede llegar a $X (+Y%)"
   - Base: "Si el mercado se mantiene estable, esperamos $X (+Y%)"
   - Pesimista: "Si [riesgo específico] se materializa, el precio puede caer a $X (-Y%)"

5. PLAN DE ACCIÓN CONCRETO
   - Cuánto invertir exactamente en este activo
   - En qué plataforma (eToro o Binance)
   - A qué precio comprar (market o limit)
   - Cuándo revisar la posición
   - Condición para vender (take profit / stop loss)
```

## Encadenamiento con otros skills
```
→ SIEMPRE ejecutar ANTES de equity_skill.md y defi_skill.md
→ El contexto geopolítico MODIFICA las recomendaciones de los skills de dominio
→ Si el mercado está en "modo risk-off": reducir peso en activos agresivos incluso para perfil alto
→ Si el mercado está en "modo risk-on": aumentar peso en altcoins y acciones de crecimiento
→ DESPUÉS de generar el plan: validar contra risk_rules.md (las reglas de riesgo siguen aplicando)
```

## Advertencias
- "El análisis geopolítico es informativo y puede cambiar rápidamente"
- "Las narrativas de mercado son cíclicas — lo que funciona hoy puede no funcionar en 3 meses"
- "Invertir en activos de alto riesgo significa que puedes perder una parte significativa de tu capital"
- "NUNCA inviertas dinero que necesites para gastos esenciales"
