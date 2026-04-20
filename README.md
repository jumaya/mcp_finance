# Agent Finance — Hybrid MCP Architecture

Sistema multi-agente de inversión para generar planes de ingresos pasivos personalizados.
Arquitectura híbrida: 5 MCP servers para datos + 11 skills con lógica de decisión autónoma + MCP server propio de calculadoras.

## Estructura

```
mcp_finance/
├── project-knowledge/          ← Skills (subir a Claude Desktop Project Knowledge)
│   ├── system.md                    ← Agente orquestador: ciclo autónomo, árbol decisiones
│   ├── equity_skill.md              ← Acciones/ETFs: selección por capital, correlación, RSI
│   ├── defi_skill.md                ← Cripto/DeFi: estrategia por nivel, decisión de red
│   ├── forex_skill.md               ← Forex/CFDs: barrera entrada, selección pares
│   ├── social_skill.md              ← Copy trading: popular investors, eToro MCP
│   ├── platforms_skill.md           ← Reglas operativas eToro + Binance desde Colombia
│   ├── tracking_skill.md            ← Seguimiento post-inversión y rebalanceo
│   ├── market_intelligence_skill.md ← Paso 1/2: contexto de mercado y asimetrías
│   ├── technical_skill.md           ← Análisis técnico (Fibonacci, SL/TP, R:R)
│   ├── risk_rules.md                ← Reglas SI/ENTONCES + stress test + exit triggers
│   ├── guard_rules.md               ← Clasificación inputs fuera de scope
│   └── plan_template.md             ← Estructura JSX de 4 tabs + checklist calidad
├── mcp-server/                 ← Tu MCP server propio (Python FastMCP)
│   ├── server.py               ← 7 tools de cálculo financiero
│   └── pyproject.toml
├── claude_desktop_config.json  ← Config 5 MCP servers
└── README.md
```

## MCP Servers (5)

| Server | Tipo | Tools | Datos que provee |
|--------|------|-------|-----------------|
| Alpha Vantage | Oficial | 116 | Acciones, ETFs, forex, indicadores técnicos |
| CoinGecko | Oficial | ~30 | Cripto precios, market cap, pools DeFi |
| DeFiLlama | Comunidad | ~7 | TVL protocolos, APY yields, stablecoins |
| eToro MCP | Comunidad | 34 | Portafolio, popular investors, órdenes, DCA |
| Investment Calculators | Propio | 6 | Risk score, position size, allocation, scenarios, correlation, stress test |

## Setup

### 1. Requisitos
- Claude Desktop (plan Pro o Team)
- Node.js (para CoinGecko, DeFiLlama, eToro MCP servers)
- Python 3.11+ con `uv` (para tu MCP server)
- Git

### 2. API keys (gratuitas)
- Alpha Vantage: alphavantage.co/support/#api-key
- eToro: portal de desarrolladores de eToro

### 3. Instalar MCP servers

```bash
# Tu server de calculadoras
cd mcp-server && uv sync

# eToro MCP (clonar y compilar)
cd .. && git clone https://github.com/orkblutt/etoro-mcp.git eToro-MCP
cd eToro-MCP && npm install && npm run build
```

### 4. Configurar Claude Desktop
Abrir `%APPDATA%\Claude\claude_desktop_config.json` (Windows)
Copiar contenido de `claude_desktop_config.json` de este repo.
Reemplazar: `TU_API_KEY_AQUI`, `TU_ETORO_API_KEY`, `TU_ETORO_USER_KEY`, `TU_USUARIO`.
Reiniciar Claude Desktop.

### 5. Crear Project
1. Claude Desktop → Projects → New Project → "Investment Advisor"
2. Project Knowledge → Upload → los 11 archivos .md de `project-knowledge/`
3. Chatear: "Tengo $500 y quiero generar ingresos pasivos"

## Verticales de inversión

| Vertical | Skill | MCP Server | Rango APY | Riesgo |
|----------|-------|-----------|-----------|--------|
| ETFs indexados (VOO, QQQ, SCHD) | equity | Alpha Vantage | 8-12% | Moderado |
| Lending stablecoins (Aave, Binance) | defi | DeFiLlama + CoinGecko | 3-8% | Bajo |
| ETH staking (Lido, Binance) | defi | CoinGecko + DeFiLlama | 2.7-4% | Moderado |
| Copy trading (eToro) | social | eToro MCP | 5-20% | Moderado |
| Forex swing (EUR/USD, XAU/USD) | forex | Alpha Vantage | Variable | Alto |
