"""
MCP Server: calculadoras financieras para el sistema de inversión.
Ejecutar: uv run server.py
"""

import math
from fastmcp import FastMCP

mcp = FastMCP("Investment Calculators")


@mcp.tool()
def calculate_risk_score(
    volatility_30d: float,
    max_drawdown_12m: float,
    liquidity: str,
    platform_regulated: bool,
    weight_in_portfolio_pct: float,
) -> dict:
    """Calcula risk score compuesto 1-10 para un activo.
    Args:
        volatility_30d: Std dev retornos 30 días (ej: 0.02 = 2%)
        max_drawdown_12m: Máxima caída 12 meses (ej: -0.25 = -25%)
        liquidity: "instant", "hours", "days", "weeks", "months"
        platform_regulated: True si regulada (SEC, FCA, ASIC)
        weight_in_portfolio_pct: Peso del activo (ej: 30 = 30%)
    """
    liq_map = {"instant": 0, "hours": 0.3, "days": 0.8, "weeks": 1.5, "months": 2.0}
    vol = min(volatility_30d / 0.5 * 3.0, 3.0)
    dd = min(abs(max_drawdown_12m) / 0.6 * 2.5, 2.5)
    liq = liq_map.get(liquidity, 1.0)
    plat = 0.0 if platform_regulated else 1.5
    conc = min(weight_in_portfolio_pct / 30.0, 1.0)
    composite = round(min(vol + dd + liq + plat + conc, 10.0), 1)
    max_alloc = 10.0 if composite > 7 else 20.0 if composite > 5 else 30.0
    warnings = []
    if volatility_30d > 0.3:
        warnings.append("Volatilidad extremadamente alta (>30% mensual)")
    if abs(max_drawdown_12m) > 0.4:
        warnings.append(f"Drawdown severo: {max_drawdown_12m:.0%}")
    if weight_in_portfolio_pct > 30:
        warnings.append(f"Concentración excesiva: {weight_in_portfolio_pct:.0f}%")
    if not platform_regulated:
        warnings.append("Plataforma sin regulación de primer nivel")
    return {
        "composite_score": composite,
        "components": {"volatility": round(vol, 2), "drawdown": round(dd, 2),
                       "liquidity": round(liq, 2), "platform": round(plat, 2),
                       "concentration": round(conc, 2)},
        "max_allocation_pct": max_alloc,
        "risk_label": "low" if composite <= 3.5 else "moderate" if composite <= 6.5 else "high",
        "warnings": warnings,
    }


@mcp.tool()
def calculate_correlation(prices_a: list[float], prices_b: list[float]) -> dict:
    """Correlación de Pearson entre dos series de precios (mínimo 10 valores cada una)."""
    n = min(len(prices_a), len(prices_b))
    if n < 10:
        return {"error": "Mínimo 10 datos", "correlation": None}
    ret_a = [(prices_a[i] / prices_a[i-1]) - 1 for i in range(1, n)]
    ret_b = [(prices_b[i] / prices_b[i-1]) - 1 for i in range(1, n)]
    ma, mb = sum(ret_a)/len(ret_a), sum(ret_b)/len(ret_b)
    cov = sum((a-ma)*(b-mb) for a, b in zip(ret_a, ret_b)) / (len(ret_a)-1)
    sa = math.sqrt(sum((a-ma)**2 for a in ret_a) / (len(ret_a)-1))
    sb = math.sqrt(sum((b-mb)**2 for b in ret_b) / (len(ret_b)-1))
    if sa == 0 or sb == 0:
        return {"correlation": 0.0, "is_problematic": False, "interpretation": "Sin variación"}
    corr = round(cov / (sa * sb), 3)
    prob = abs(corr) > 0.7
    if corr > 0.7: interp = "Alta correlación positiva: poca diversificación"
    elif corr > 0.3: interp = "Correlación moderada positiva"
    elif corr > -0.3: interp = "Baja correlación: buena diversificación"
    elif corr > -0.7: interp = "Correlación negativa: excelente diversificación"
    else: interp = "Alta correlación negativa: se mueven opuestos"
    return {"correlation": corr, "is_problematic": prob, "interpretation": interp}


@mcp.tool()
def stress_test_portfolio(positions: list[dict], scenario: str = "moderate_crash") -> dict:
    """Simula crisis en el portafolio.
    Args:
        positions: [{"asset_id": str, "amount_usd": float, "vertical": str, "monthly_income_usd": float}]
        scenario: "moderate_crash", "severe_crash", "crypto_winter", "stable_only"
    """
    impacts = {
        "moderate_crash": {"equity": -0.15, "defi": -0.25, "forex": -0.05, "social": -0.12, "stablecoin": 0},
        "severe_crash": {"equity": -0.30, "defi": -0.50, "forex": -0.10, "social": -0.25, "stablecoin": -0.01},
        "crypto_winter": {"equity": 0.0, "defi": -0.60, "forex": 0.0, "social": -0.05, "stablecoin": 0},
        "stable_only": {"equity": -0.05, "defi": -0.10, "forex": -0.03, "social": -0.05, "stablecoin": 0},
    }
    rates = impacts.get(scenario, impacts["moderate_crash"])
    total_before = sum(p["amount_usd"] for p in positions)
    results, surviving = [], 0.0
    for p in positions:
        v = p.get("vertical", "equity")
        is_stable = "stable" in p.get("asset_id", "").lower() or "usdc" in p.get("asset_id", "").lower()
        rate = rates.get("stablecoin", 0) if is_stable else rates.get(v, -0.10)
        impact = round(p["amount_usd"] * rate, 2)
        surv = round(p.get("monthly_income_usd", 0) * (1.0 if is_stable else max(0.3, 1+rate)), 2)
        surviving += surv
        results.append({"asset_id": p["asset_id"], "before": p["amount_usd"],
                        "impact_usd": impact, "after": round(p["amount_usd"]+impact, 2),
                        "surviving_monthly_income": surv})
    total_after = sum(r["after"] for r in results)
    return {
        "scenario": scenario, "total_before": round(total_before, 2),
        "total_after": round(total_after, 2),
        "total_loss_usd": round(total_after-total_before, 2),
        "total_loss_pct": round((total_after-total_before)/total_before*100, 1) if total_before > 0 else 0,
        "surviving_monthly_income": round(surviving, 2), "positions": results,
    }


@mcp.tool()
def calculate_tax_impact(asset_type: str, annual_income_usd: float,
                         has_w8ben: bool = False, usd_to_cop: float = 4200.0) -> dict:
    """Impacto fiscal Colombia (DIAN) para un activo.
    Args:
        asset_type: "us_stock_dividend", "us_etf_dividend", "crypto_staking",
                    "crypto_trading_gain", "defi_yield", "forex_gain", "copy_trading_gain"
        annual_income_usd: Ingreso anual estimado
        has_w8ben: Tiene W-8BEN llenado
        usd_to_cop: Tasa de cambio
    """
    UVT = 47_065
    cop = annual_income_usd * usd_to_cop
    rules = {
        "us_stock_dividend": {"type": "renta_fuente_extranjera", "us": 0.15 if has_w8ben else 0.30, "co": 0.0, "ret": 0.0, "w8": True},
        "us_etf_dividend": {"type": "renta_fuente_extranjera", "us": 0.15 if has_w8ben else 0.30, "co": 0.0, "ret": 0.0, "w8": True},
        "crypto_staking": {"type": "ganancia_ocasional", "us": 0.0, "co": 0.15, "ret": 0.0, "w8": False},
        "crypto_trading_gain": {"type": "ganancia_ocasional", "us": 0.0, "co": 0.15, "ret": 0.0, "w8": False},
        "defi_yield": {"type": "ganancia_ocasional", "us": 0.0, "co": 0.15, "ret": 0.0, "w8": False},
        "forex_gain": {"type": "renta_ordinaria", "us": 0.0, "co": 0.0, "ret": 0.04, "w8": False},
        "copy_trading_gain": {"type": "renta_fuente_extranjera", "us": 0.0, "co": 0.0, "ret": 0.0, "w8": False},
    }
    r = rules.get(asset_type, rules["crypto_trading_gain"])
    net = annual_income_usd * (1-r["us"]) * (1-r["co"]) * (1-r["ret"])
    mult = round(net / annual_income_usd, 3) if annual_income_usd > 0 else 1.0
    actions = []
    if r["w8"] and not has_w8ben:
        actions.append("URGENTE: Llenar W-8BEN para reducir retención USA del 30% al 15%")
    if cop > 1400 * UVT:
        actions.append("Declarar renta ante DIAN")
    actions.append("Reportar activos en exterior ante DIAN")
    return {
        "asset_type": asset_type, "income_type": r["type"],
        "gross_usd": annual_income_usd, "net_usd": round(net, 2),
        "total_tax_usd": round(annual_income_usd-net, 2),
        "net_return_multiplier": mult,
        "effective_tax_rate_pct": round((1-mult)*100, 1),
        "w8ben_applicable": r["w8"],
        "w8ben_benefit": f"Ahorra ${round(annual_income_usd*0.15, 2)}/año" if r["w8"] and not has_w8ben else None,
        "must_declare_renta": cop > 1400 * UVT,
        "action_items": actions,
    }


@mcp.tool()
def calculate_position_size(capital_usd: float, risk_per_trade_pct: float,
                            entry_price: float, stop_loss_price: float,
                            leverage: float = 1.0) -> dict:
    """Tamaño de posición para Forex/CFDs.
    Args:
        capital_usd: Capital total para trading
        risk_per_trade_pct: % riesgo por trade (recomendado 1-2%)
        entry_price: Precio de entrada
        stop_loss_price: Precio stop loss
        leverage: Apalancamiento (max recomendado 5x)
    """
    if leverage > 10:
        return {"error": "Apalancamiento > 10x extremadamente riesgoso. Máx recomendado: 5x"}
    risk_usd = capital_usd * (risk_per_trade_pct / 100)
    stop_dist = abs(entry_price - stop_loss_price)
    if stop_dist == 0:
        return {"error": "Stop loss no puede ser igual al entry"}
    pos_size = (risk_usd / stop_dist) * leverage
    pos_value = pos_size * entry_price
    margin = pos_value / leverage
    sign = 1 if entry_price > stop_loss_price else -1
    warnings = []
    if risk_per_trade_pct > 3: warnings.append(f"Riesgo {risk_per_trade_pct}% alto. Recomendado: 1-2%")
    if leverage > 5: warnings.append(f"Apalancamiento {leverage}x alto. Recomendado: 1-5x")
    if margin > capital_usd * 0.5: warnings.append("Margen supera 50% del capital")
    return {
        "risk_usd": round(risk_usd, 2), "position_units": round(pos_size, 4),
        "position_value_usd": round(pos_value, 2), "margin_required": round(margin, 2),
        "tp_1to2": round(entry_price + 2*stop_dist*sign, 4),
        "tp_1to3": round(entry_price + 3*stop_dist*sign, 4),
        "warnings": warnings,
    }


@mcp.tool()
def allocate_portfolio(capital_usd: float, monthly_savings_usd: float,
                       risk_tolerance: str, horizon: str,
                       exclude_verticals: list[str] | None = None) -> dict:
    """Genera asignación de portafolio por vertical con proyecciones a 12 meses.
    Args:
        capital_usd: Capital total
        monthly_savings_usd: Ahorro mensual
        risk_tolerance: "conservative", "moderate", "aggressive", "mixed"
        horizon: "short", "medium", "long", "combined"
        exclude_verticals: ["forex"] por ejemplo
    """
    excluded = set(exclude_verticals or [])
    templates = {
        "conservative": {"equity": 50, "defi": 20, "forex": 0, "social": 15, "reserve": 15},
        "moderate": {"equity": 40, "defi": 25, "forex": 10, "social": 15, "reserve": 10},
        "aggressive": {"equity": 30, "defi": 30, "forex": 20, "social": 15, "reserve": 5},
        "mixed": {"equity": 35, "defi": 25, "forex": 15, "social": 15, "reserve": 10},
    }
    base = dict(templates.get(risk_tolerance, templates["moderate"]))
    for v in excluded:
        if v in base and v != "reserve":
            extra = base[v]; base[v] = 0
            remaining = [k for k in base if k not in excluded and k != "reserve" and base[k] > 0]
            if remaining:
                for r in remaining: base[r] += extra / len(remaining)
    total = sum(base.values())
    alloc = {k: round(v/total*100, 1) for k, v in base.items()}
    amounts = {k: round(capital_usd*v/100, 2) for k, v in alloc.items()}
    monthly = {k: round(monthly_savings_usd*v/100, 2) for k, v in alloc.items() if k != "reserve"}
    est_ret = {"equity": 0.008, "defi": 0.005, "forex": 0.0, "social": 0.006, "reserve": 0.001}
    projections, cum_cap, cum_inc = [], capital_usd, 0.0
    amts = dict(amounts)
    for m in range(1, 13):
        mi = sum(amts.get(v, 0)*est_ret.get(v, 0) for v in alloc)
        cum_inc += mi; cum_cap += monthly_savings_usd + mi
        for v in monthly: amts[v] = amts.get(v, 0) + monthly.get(v, 0)
        if m in (1, 3, 6, 12):
            projections.append({"month": m, "total_capital": round(cum_cap, 2),
                               "monthly_income": round(mi, 2), "cumulative_income": round(cum_inc, 2)})
    return {"allocation_pct": alloc, "allocation_usd": amounts,
            "monthly_contribution": monthly, "projections": projections}


@mcp.tool()
def calculate_scenarios(amount_usd: float, expected_apy: float,
                        volatility_annual: float,
                        passive_income_annual_usd: float = 0.0,
                        months: int = 12) -> dict:
    """3 escenarios (optimista/base/pesimista) para una posición.
    Args:
        amount_usd: Monto invertido
        expected_apy: Rendimiento anual esperado (0.10 = 10%)
        volatility_annual: Volatilidad anualizada (0.15 = 15%)
        passive_income_annual_usd: Ingreso pasivo fijo anual (dividendos, staking)
        months: Horizonte en meses
    """
    f = months / 12.0
    passive = passive_income_annual_usd * f
    scenarios = []
    for name, ret, prob in [
        ("optimistic", (expected_apy + volatility_annual) * f, 25),
        ("base", expected_apy * f, 50),
        ("pessimistic", (expected_apy - 1.5 * volatility_annual) * f, 25),
    ]:
        price_impact = amount_usd * ret
        total = price_impact + passive
        scenarios.append({
            "name": name, "probability_pct": prob,
            "price_change_pct": round(ret*100, 1),
            "passive_income_usd": round(passive, 2),
            "total_return_usd": round(total, 2),
            "total_return_pct": round(total/amount_usd*100, 1) if amount_usd > 0 else 0,
            "portfolio_value": round(amount_usd+total, 2),
        })
    return {"amount_usd": amount_usd, "months": months, "scenarios": scenarios}


if __name__ == "__main__":
    mcp.run()
