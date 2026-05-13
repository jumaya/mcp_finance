"""
eToro MCP Server — solo lectura.

Autenticación vía headers oficiales:
  - x-api-key     (Public API Key)
  - x-user-key    (User Key generada en Settings > Trading)
  - x-request-id  (UUID único por request)

Tools expuestas:
  - search_instruments      → buscar activos por ticker/nombre
  - get_portfolio           → posiciones abiertas de tu cuenta
  - get_rates               → precios bid/ask en vivo
  - get_candles             → OHLCV histórico
  - get_user_performance    → métricas de un trader (para copy trading)

Referencia: https://api-portal.etoro.com/
"""
from __future__ import annotations

import os
import sys
import uuid
from typing import Any

import httpx
from mcp.server.fastmcp import FastMCP

# -----------------------------------------------------------------------------
# Config
# -----------------------------------------------------------------------------
BASE_URL = "https://public-api.etoro.com/api/v1"
TIMEOUT = 30.0

API_KEY = os.environ.get("ETORO_API_KEY", "").strip()
USER_KEY = os.environ.get("ETORO_USER_KEY", "").strip()
# "demo" (virtual/papertrading) o "real". Debe coincidir con el entorno
# de la clave generada en eToro Settings > Trading.
TRADING_MODE = os.environ.get("ETORO_TRADING_MODE", "demo").strip().lower()
if TRADING_MODE not in ("demo", "real"):
    print(
        f"[etoro-server] WARNING: ETORO_TRADING_MODE={TRADING_MODE!r} inválido, usando 'demo'",
        file=sys.stderr,
    )
    TRADING_MODE = "demo"

if not API_KEY or not USER_KEY:
    # No levantamos exception al importar para que Claude Desktop
    # pueda mostrar el error del MCP sin tirar el proceso entero.
    print(
        "[etoro-server] WARNING: faltan ETORO_API_KEY o ETORO_USER_KEY en env",
        file=sys.stderr,
    )

mcp = FastMCP("etoro-server")


# -----------------------------------------------------------------------------
# Cliente HTTP
# -----------------------------------------------------------------------------
def _headers() -> dict[str, str]:
    """Construye headers frescos para cada request. x-request-id DEBE ser único."""
    return {
        "x-api-key": API_KEY,
        "x-user-key": USER_KEY,
        "x-request-id": str(uuid.uuid4()),
        "Accept": "application/json",
    }


def _get(path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """GET autenticado contra la API pública de eToro.

    Construye el query string manualmente porque httpx URL-encode las comas
    (`,` → `%2C`) y eToro no parsea correctamente el parámetro `fields`
    cuando viene escapado. Usamos codificación simple solo para los valores
    individuales, preservando las comas en las listas.

    Devuelve siempre un dict. En caso de error devuelve
    {"error": True, "status": N, "message": "...", "body": {...}}
    para que el agente pueda razonar sobre el fallo en vez de crashear.
    """
    url = f"{BASE_URL}{path}"
    if params:
        # quote_via=quote para NO escapar comas (safe chars por defecto en quote).
        # Así "fields=a,b,c" llega tal cual a eToro.
        from urllib.parse import urlencode, quote
        qs = urlencode(
            {k: v for k, v in params.items() if v is not None},
            quote_via=quote,
            safe=",",
        )
        url = f"{url}?{qs}"

    try:
        with httpx.Client(timeout=TIMEOUT) as client:
            r = client.get(url, headers=_headers())
    except httpx.HTTPError as e:
        return {"error": True, "status": 0, "message": f"network: {e}"}

    if r.status_code >= 400:
        try:
            body = r.json()
        except Exception:
            body = {"raw": r.text[:500]}
        return {
            "error": True,
            "status": r.status_code,
            "message": f"eToro API {r.status_code}",
            "body": body,
            "hint": _hint_for_status(r.status_code),
        }

    try:
        return {"error": False, "data": r.json()}
    except Exception:
        return {"error": False, "data": {"raw": r.text}}


def _hint_for_status(status: int) -> str:
    """Pista de diagnóstico legible para el agente."""
    if status == 401:
        return (
            "Unauthorized. Verifica: (1) api_key y user_key correctos, "
            "(2) entorno de la key (Demo/Real) coincide con el endpoint, "
            "(3) la key no expiró, (4) IP whitelist."
        )
    if status == 403:
        return "Forbidden. La key no tiene permisos (p.ej. Read-only intentando escribir)."
    if status == 429:
        return "Rate limit. Espera y reintenta más tarde."
    return ""


# -----------------------------------------------------------------------------
# Tools
# -----------------------------------------------------------------------------
@mcp.tool()
def search_instruments(
    query: str,
    search_by: str = "internalSymbolFull",
    fields: str = (
        "instrumentId,displayname,symbol,internalSymbolFull,instrumentType,"
        "internalExchangeName,currentRate,dailyPriceChange,"
        "oneYearPriceChange,isBuyEnabled"
    ),
    page_size: int = 10,
) -> dict[str, Any]:
    """Busca activos en eToro (acciones, cripto, ETFs, forex).

    La API de eToro usa CUALQUIER campo como filtro de búsqueda: pasas el
    nombre del campo como query param y su valor. El parámetro `searchText`
    de la documentación no filtra en la práctica — hay que usar un campo
    concreto.

    Args:
        query: valor a buscar (ej. "BTC", "AAPL", "Apple").
        search_by: campo a usar como filtro. Opciones útiles:
            - internalSymbolFull (default, ticker exacto: "BTC", "AAPL")
            - displayname (nombre visible: "Apple", "Bitcoin")
            - symbol (símbolo corto)
        fields: campos a devolver en la respuesta, separados por coma.
        page_size: número de resultados (default 10).
    """
    params: dict[str, Any] = {
        search_by: query,
        "fields": fields,
        "pageSize": page_size,
        "pageNumber": 1,
    }
    return _get("/market-data/search", params=params)


@mcp.tool()
def get_portfolio() -> dict[str, Any]:
    """Obtiene las posiciones abiertas de tu cuenta personal + PnL.

    Usa /trading/info/{mode}/pnl según ETORO_TRADING_MODE (demo o real).
    Este es el endpoint oficial para cuentas de usuario; el /agent-portfolios
    es solo para cuentas de asesor.

    Devuelve `clientPortfolio` con: credit, unrealizedPnL, mirrors (copy
    trading), positions (posiciones abiertas con PnL), orders, etc.
    """
    path = f"/trading/info/{TRADING_MODE}/pnl"
    return _get(path)


@mcp.tool()
def get_rates(instrument_ids: list[int]) -> dict[str, Any]:
    """Obtiene precios bid/ask en vivo para uno o varios instrumentos.

    Endpoint oficial: /market-data/instruments/rates
    Máximo 100 IDs por request.

    Args:
        instrument_ids: lista de IDs (ej. [1001, 100000] para Apple y BTC).
                        Usa search_instruments primero si no conoces el ID.
    """
    if not instrument_ids:
        return {"error": True, "message": "instrument_ids no puede estar vacío"}
    if len(instrument_ids) > 100:
        return {"error": True, "message": "máximo 100 instrument_ids por request"}
    params = {"instrumentIds": ",".join(str(i) for i in instrument_ids)}
    return _get("/market-data/instruments/rates", params=params)


@mcp.tool()
def get_candles(
    instrument_id: int,
    interval: str = "OneDay",
    count: int = 100,
    direction: str = "desc",
) -> dict[str, Any]:
    """Obtiene velas OHLCV históricas para un instrumento.

    Endpoint oficial:
      /market-data/instruments/{instrumentId}/history/candles/{direction}/{interval}/{count}

    Args:
        instrument_id: ID del instrumento (resuélvelo con search_instruments).
        interval: granularidad. Valores válidos: OneMinute, FiveMinutes,
                TenMinutes, FifteenMinutes, ThirtyMinutes, OneHour,
                FourHours, OneDay, OneWeek.
        count: número de velas (máx 1000).
        direction: "desc" (más recientes primero, default) o "asc".
    """
    if count > 1000:
        return {"error": True, "message": "count máximo es 1000"}
    if direction not in ("asc", "desc"):
        return {"error": True, "message": "direction debe ser 'asc' o 'desc'"}

    path = (
        f"/market-data/instruments/{instrument_id}"
        f"/history/candles/{direction}/{interval}/{count}"
    )
    return _get(path)


@mcp.tool()
def get_user_performance(
    username: str,
    period: str = "OneYearAgo",
) -> dict[str, Any]:
    """Métricas de rendimiento y riesgo de un trader público eToro.

    Úsala para evaluar popular investors antes de sugerir copy trading.
    Devuelve retornos, risk score, copiers, copy performance, drawdowns,
    winning weeks, instrumento más traded, etc.

    Endpoint oficial: /user-info/people/{username}/tradeinfo

    Args:
        username: handle público del trader (ej. "JeppeKirkBonde", sin @).
        period: ventana temporal. Valores válidos:
                CurrMonth, CurrQuarter, CurrYear, LastYear, LastTwoYears,
                OneMonthAgo, TwoMonthsAgo, ThreeMonthsAgo, SixMonthsAgo,
                OneYearAgo (default).
    """
    valid_periods = {
        "CurrMonth", "CurrQuarter", "CurrYear", "LastYear", "LastTwoYears",
        "OneMonthAgo", "TwoMonthsAgo", "ThreeMonthsAgo", "SixMonthsAgo",
        "OneYearAgo",
    }
    if period not in valid_periods:
        return {
            "error": True,
            "message": f"period inválido. Usa uno de: {sorted(valid_periods)}",
        }
    params = {"period": period}
    return _get(f"/user-info/people/{username}/tradeinfo", params=params)


@mcp.tool()
def discover_popular_investors(
    period: str = "OneYearAgo",
    page_size: int = 10,
    sort: str | None = None,
    popular_investor: bool | None = None,
    max_daily_risk_score_max: int | None = None,
    max_monthly_risk_score_max: int | None = None,
    min_weeks_since_registration: int | None = None,
    country_id: int | None = None,
    instrument_id: int | None = None,
    gain_min: float | None = None,
) -> dict[str, Any]:
    """Descubre popular investors de eToro filtrando por rendimiento y riesgo.

    Tool clave para el agente de copy trading inteligente: en vez de
    usar nombres hardcodeados, el agente puede filtrar traders reales por
    criterios objetivos (ganancia, riesgo, experiencia) y rankearlos.

    Endpoint oficial: /user-info/people/search
    Solo `period` es obligatorio. Todos los demás filtros son opcionales.

    Args:
        period: ventana temporal (OBLIGATORIO). Valores: CurrMonth,
                CurrQuarter, CurrYear, LastYear, LastTwoYears,
                OneMonthAgo, TwoMonthsAgo, ThreeMonthsAgo, SixMonthsAgo,
                OneYearAgo (default).
        page_size: número de traders a devolver (default 10).
        sort: campo y dirección, ej "gain desc". None = orden default API.
        popular_investor: True = solo PIs oficiales. None = no filtrar.
        max_daily_risk_score_max: máx risk score diario (1-10). None = no filtrar.
        max_monthly_risk_score_max: máx risk score mensual (1-10).
        min_weeks_since_registration: experiencia mínima en semanas.
        country_id: filtrar por país (int).
        instrument_id: traders que operan cierto instrumento.
        gain_min: ganancia mínima en el período (%).
    """
    # Solo incluimos parámetros que el usuario pasó explícitamente.
    # La API se queja si le mandas filtros vacíos o combinaciones raras.
    params: dict[str, Any] = {
        "period": period,
        "pageSize": page_size,
    }
    if sort is not None:
        params["sort"] = sort
    if popular_investor is not None:
        params["popularInvestor"] = str(popular_investor).lower()
    if max_daily_risk_score_max is not None:
        params["maxDailyRiskScoreMax"] = max_daily_risk_score_max
    if max_monthly_risk_score_max is not None:
        params["maxMonthlyRiskScoreMax"] = max_monthly_risk_score_max
    if min_weeks_since_registration is not None:
        params["weeksSinceRegistrationMin"] = min_weeks_since_registration
    if country_id is not None:
        params["countryId"] = country_id
    if instrument_id is not None:
        params["instrumentId"] = instrument_id
    if gain_min is not None:
        params["gainMin"] = gain_min
    return _get("/user-info/people/search", params=params)


# -----------------------------------------------------------------------------
# Entry point
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    mcp.run()
