# etoro-server

MCP server propio para eToro Public API (solo lectura).

Parte del proyecto `mcp_finance`. Vive junto a `mcp-server/` (el de
calculadoras) y se registra como un MCP adicional en Claude Desktop.

## Por qué existe

Los wrappers de terceros (`orkblutt/etoro-mcp`) devolvían 401 aun con
credenciales válidas. Este servidor usa los headers oficiales de eToro
(`x-api-key`, `x-user-key`, `x-request-id`) de forma explícita y genera un
UUID nuevo en cada request.

## Tools

| Tool | Descripción |
|---|---|
| `search_instruments` | Busca activos por ticker o nombre. `fields` es obligatorio. |
| `get_portfolio` | Posiciones abiertas de tu cuenta. |
| `get_rates` | Precios bid/ask en vivo para una lista de instrumentos. |
| `get_candles` | OHLCV histórico para análisis técnico. |
| `get_user_performance` | Métricas de un trader (retorno, risk score, win ratio). Base para copy trading basado en datos. |

## Setup

### 1. Instalar dependencias

```bash
cd etoro-server
uv sync
# o: pip install "mcp[cli]" httpx
```

### 2. Verificar que las credenciales funcionan (sin MCP)

Antes de tocar Claude Desktop, valida que las claves andan:

```bash
# Windows PowerShell
$env:ETORO_API_KEY="tu_public_api_key"
$env:ETORO_USER_KEY="tu_user_key"
python test_auth.py
```

Debes ver `Status: 200`. Si ves 401, el problema está en las credenciales
(no en el MCP) — revisa:
- Las claves no tienen espacios ni saltos de línea al copiarlas.
- `api_key` y `user_key` no están invertidas.
- La `user_key` se creó en entorno **Demo** (coincide con el MCP).
- La clave no expiró ni tiene IP whitelist que te bloquee.

### 3. Registrar en Claude Desktop

Edita `%APPDATA%\Claude\claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "etoro-server": {
      "command": "uv",
      "args": [
        "--directory",
        "C:\\Proyectos\\mcp_finance\\etoro-server",
        "run",
        "server.py"
      ],
      "env": {
        "ETORO_API_KEY": "tu_public_api_key",
        "ETORO_USER_KEY": "tu_user_key"
      }
    }
  }
}
```

Si no usas `uv`, alternativa con Python directo:

```json
{
  "mcpServers": {
    "etoro-server": {
      "command": "python",
      "args": ["C:\\Proyectos\\mcp_finance\\etoro-server\\server.py"],
      "env": {
        "ETORO_API_KEY": "tu_public_api_key",
        "ETORO_USER_KEY": "tu_user_key"
      }
    }
  }
}
```

### 4. Reiniciar Claude Desktop completamente

Cerrar desde la bandeja del sistema (no solo la ventana). Al volver a
abrirlo, `etoro-server` debe aparecer en el listado de MCPs con 5 tools.

## Notas de diseño

- **Solo lectura en esta versión.** Endpoints de ejecución (`market-open-orders`,
  `close-position`) se añadirán cuando esta versión esté estable.
- **Sin dependencias de terceros no oficiales.** Solo `httpx` + `mcp`.
- **Errores devueltos como datos, no como excepciones.** Cada tool
  devuelve `{"error": bool, ...}` para que el agente razone sobre el
  fallo en vez de ver un stack trace.
- **UUID único por request.** Requisito de la API — muchos wrappers
  fallan aquí reutilizando IDs.

## Integración con el resto del proyecto

Este MCP provee los **datos** (qué tengo, qué vale, cómo va ese trader).
El MCP de `mcp-server/` (calculadoras) procesa esos datos con reglas de
riesgo y fiscales. El skill `social_skill.md` puede ahora llamar
`get_user_performance` sobre traders candidatos en vez de repetir nombres
hardcodeados.
