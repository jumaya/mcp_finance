# Agent Finance — Hybrid MCP Architecture

Sistema de inversión para generar planes de ingresos pasivos personalizados.
Arquitectura híbrida: MCP servers externos para datos + skills como Project Knowledge + MCP server propio de calculadoras.

## Estructura

```
agent-finance-mcp/
├── project-knowledge/          ← Skills (subir a Claude Desktop Project Knowledge)
│   ├── system.md               ← Instrucciones del orquestador
│   ├── equity_skill.md         ← Acciones y ETFs
│   ├── defi_skill.md           ← Cripto, staking, DeFi
│   ├── forex_skill.md          ← Forex y CFDs
│   ├── risk_rules.md           ← Reglas de riesgo
│   ├── tax_colombia.md         ← Reglas fiscales DIAN
│   ├── guard_rules.md          ← Manejo inputs fuera de scope
│   └── plan_template.md        ← Estructura del plan de salida
├── mcp-server/                 ← Tu MCP server propio (Python FastMCP)
│   ├── server.py               ← 7 tools de cálculo financiero
│   └── pyproject.toml
├── claude_desktop_config.json  ← Config MCP servers para Claude Desktop
└── README.md
```

## Setup (3 pasos)

### 1. Tu MCP server de calculadoras
```bash
cd mcp-server
uv sync
uv run server.py  # Verificar que arranca
```

### 2. Configurar Claude Desktop
Abre el config de Claude Desktop:
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`

Copia el contenido de `claude_desktop_config.json`. Reemplaza:
- `TU_API_KEY_AQUI` → tu key de Alpha Vantage (gratis en alphavantage.co)
- `/RUTA/A/agent-finance-mcp/mcp-server` → ruta real en tu máquina

Reinicia Claude Desktop.

### 3. Crear Project en Claude Desktop
1. Projects → New Project → nombre: "Investment Advisor"
2. En Project Knowledge, sube los 8 archivos `.md` de `project-knowledge/`
3. Empieza: "Tengo $500 y quiero generar ingresos pasivos"

## Tools del MCP server

| Tool | Qué hace |
|------|----------|
| `calculate_risk_score` | Risk score 1-10 con componentes desglosados |
| `calculate_correlation` | Correlación de Pearson entre dos activos |
| `stress_test_portfolio` | Simula escenarios de crisis |
| `calculate_tax_impact` | Impacto fiscal Colombia (DIAN) |
| `calculate_position_size` | Dimensionar posición Forex/CFDs |
| `allocate_portfolio` | Asignación por vertical con proyecciones 12m |
| `calculate_scenarios` | 3 escenarios (optimista/base/pesimista) |

## Requisitos
- Claude Desktop (con plan Pro o Team)
- Node.js (para MCP servers de CoinGecko y DeFiLlama)
- Python 3.11+ con `uv`
- API key Alpha Vantage (gratis: alphavantage.co/support/#api-key)
