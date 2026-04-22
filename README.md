# Agent Finance — Hybrid MCP Architecture

Sistema multi-agente de inversión para generar planes de ingresos pasivos personalizados.
Arquitectura híbrida: **9 MCP servers** para datos + ejecución + **12 skills** con lógica de decisión autónoma + MCP server propio de calculadoras.

## Estructura

```
mcp_finance/
├── project-knowledge/          ← Skills (subir a Claude Desktop Project Knowledge)
│   ├── system.md                      ← Agente orquestador: ciclo autónomo, árbol de decisiones
│   ├── guard_rules.md                 ← Clasificación de inputs fuera de scope (primer filtro)
│   ├── market_intelligence_skill.md   ← Paso 1/2: contexto de mercado y asimetrías
│   ├── risk_rules.md                  ← Reglas SI/ENTONCES + stress test + exit triggers
│   ├── plan_template.md               ← Estructura JSX de 4 tabs + checklist de calidad
│   ├── platforms_skill.md             ← Reglas operativas eToro + Binance desde Colombia
│   ├── technical_skill.md             ← Análisis técnico (Fibonacci, SL/TP vinculantes, R:R)
│   ├── tracking_skill.md              ← Seguimiento post-inversión y rebalanceo entre sesiones
│   ├── equity_skill.md                ← Vertical acciones/ETFs: selección por capital, correlación, RSI
│   ├── defi_skill.md                  ← Vertical cripto/DeFi: estrategia por nivel, decisión de red
│   ├── forex_skill.md                 ← Vertical forex/CFDs: barrera entrada, selección de pares
│   └── social_skill.md                ← Vertical copy trading: popular investors vía eToro MCP
├── mcp-server/                 ← MCP server propio (Python FastMCP)
│   ├── server.py                      ← Tools de cálculo financiero (risk, position, allocation, …)
│   ├── risk_rules.md
│   └── pyproject.toml
├── etoro-server/               ← MCP server propio para eToro (Python FastMCP)
│   ├── server.py                      ← Tools de portafolio, popular investors, candles, rates
│   ├── test_auth.py
│   └── pyproject.toml
├── claude_desktop_config.json  ← Config de los 9 MCP servers
└── README.md
```

## Skills — cuándo se cargan

Los 12 skills viven todos en Project Knowledge, pero **no todos son relevantes en cada consulta**. El orquestador (`system.md`) decide cuáles invocar según el tipo de input y los verticales que el plan necesite. A efectos prácticos se agrupan así:

| Skill | Cuándo se carga |
|-------|-----------------|
| `system.md` | **Siempre** — orquestador, define el ciclo de decisión de toda sesión. |
| `guard_rules.md` | **Siempre** — primer filtro en CADA mensaje, antes de cualquier otro skill. |
| `market_intelligence_skill.md` | **Siempre** — pasos 1 y 2 del orquestador, arma el contexto de mercado. |
| `risk_rules.md` | **Siempre** — paso 5 del orquestador, valida el portafolio antes de presentar y en cada rebalanceo. |
| `plan_template.md` | **Siempre** — estructura de salida (4 tabs + BASELINE de seguimiento). |
| `platforms_skill.md` | **Siempre** — gate de disponibilidad eToro / Binance CO; el agente no puede proponer posiciones inejecutables. |
| `technical_skill.md` | **Bajo demanda** — se carga junto a un vertical cuando el plan incluye posiciones con exposición direccional al precio (equity, forex, cripto spot). SL/TP **vinculantes** se derivan aquí. |
| `tracking_skill.md` | **Bajo demanda** — se activa con "revisa mi portafolio", "cómo va el plan", "rebalancear", o cuando el usuario pega un bloque `BASELINE DE SEGUIMIENTO` de una sesión previa. |
| `equity_skill.md` | **Bajo demanda** — cuando `allocate_portfolio` asigna capital a acciones/ETFs. |
| `defi_skill.md` | **Bajo demanda** — cuando el plan incluye cripto, staking, lending o yield. |
| `forex_skill.md` | **Bajo demanda** — cuando el plan asigna capital a forex/CFDs. Nunca como primera recomendación para principiantes. |
| `social_skill.md` | **Bajo demanda** — cuando el usuario menciona copy trading o popular investors. |

> Aunque los "bajo demanda" se cargan selectivamente en el razonamiento, **los 12 archivos deben subirse a Project Knowledge**. Si falta uno, el orquestador no puede invocarlo cuando lo necesite.

## MCP Servers (9)

| Server | Tipo | Uso principal |
|--------|------|---------------|
| Alpha Vantage | Oficial | Acciones, ETFs, forex, indicadores técnicos (RSI, MACD, EMA). |
| DeFiLlama | Comunidad | TVL de protocolos, APY de yields, stablecoins. |
| Yahoo Finance | Comunidad | Datos históricos, fundamentals, cobertura amplia de tickers. |
| TradingView | Comunidad | Screeners (RSI < 30, breakout, momentum), datos técnicos. |
| Binance | Comunidad | Precios spot, order book, staking/earn, datos de pares CO. |
| MetaTrader | Comunidad | Forex/CFDs en broker externo (demo/live), ejecución y cotizaciones. |
| eToro MCP | Propio (`etoro-server/`) | Portafolio, popular investors, candles, rates, búsqueda de instrumentos. |
| Investment Calculators | Propio (`mcp-server/`) | Risk score, position size, allocation, scenarios, correlation, stress test. |

> **Nota sobre eToro**: el MCP ahora es propio (carpeta `etoro-server/`). El config puede apuntar al servidor local o, alternativamente, a `https://api-portal.etoro.com/mcp` vía `mcp-remote`. Ambos modos están soportados.

## Setup

### 1. Requisitos
- Claude Desktop (plan Pro o Team)
- Node.js (para CoinGecko, DeFiLlama, TradingView, Binance, eToro remote)
- Python 3.11+ con `uv` (para Alpha Vantage, Yahoo Finance, MetaTrader y los MCP propios)
- Git

### 2. API keys (gratuitas o de tus cuentas)
- **Alpha Vantage**: alphavantage.co/support/#api-key
- **eToro**: portal de desarrolladores de eToro (API key + user key)
- **Binance**: API key + secret desde tu cuenta Binance (con permisos de solo lectura si no vas a ejecutar)
- **MetaTrader**: credenciales de tu cuenta demo o real del broker

### 3. Instalar MCP servers propios

```bash
# Server de calculadoras
cd mcp-server && uv sync

# Server de eToro (propio)
cd ../etoro-server && uv sync
```

Los demás MCP servers (CoinGecko, DeFiLlama, Yahoo, TradingView, Binance, MetaTrader, Alpha Vantage) se descargan automáticamente vía `npx` / `uvx` la primera vez que Claude Desktop los invoca.

### 4. Configurar Claude Desktop
Abrir `%APPDATA%\Claude\claude_desktop_config.json` (Windows) o `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS).
Copiar el contenido de `claude_desktop_config.json` de este repo.
Reemplazar los placeholders por tus credenciales reales:
- `TU_ALPHAVANTAGE_API_KEY`
- `BINANCE_API_KEY` / `BINANCE_API_SECRET`
- `ETORO_API_KEY` / `ETORO_USER_KEY` (si usas el server propio)
- Credenciales de MetaTrader (login, password, server)
- Rutas absolutas en Windows (`C:\\Proyectos\\AgenteFinanzas\\...`)

Reiniciar Claude Desktop para que recargue la config.

### 5. Crear el Project en Claude Desktop
1. Claude Desktop → Projects → New Project → "Investment Advisor".
2. Project Knowledge → Upload → **los 12 archivos .md** de `project-knowledge/`.
3. Chatear, por ejemplo: *"Tengo $500 y quiero generar ingresos pasivos."*

## Verticales de inversión

| Vertical | Skill | MCP Server(s) | Rango APY | Riesgo |
|----------|-------|---------------|-----------|--------|
| ETFs indexados (VOO, QQQ, SCHD) | `equity_skill` | Alpha Vantage, Yahoo Finance, TradingView | 8–12% | Moderado |
| Lending stablecoins (Aave, Binance) | `defi_skill` | DeFiLlama, CoinGecko, Binance | 3–8% | Bajo |
| ETH staking (Lido, Binance) | `defi_skill` | CoinGecko, DeFiLlama, Binance | 2.7–4% | Moderado |
| Copy trading (eToro) | `social_skill` | eToro MCP | 5–20% | Moderado |
| Forex swing (EUR/USD, XAU/USD) | `forex_skill` | Alpha Vantage, MetaTrader | Variable | Alto |
