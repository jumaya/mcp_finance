"""
MCP Server propio: calculadoras financieras para el sistema de inversión.
v3 — Fix 1: floor mínimo de risk score por leverage
     Fix 2: monthly_cost_usd en calculate_scenarios para overnight fees

Ejecutar: uv run --no-project --with fastmcp server.py
"""

import math
from fastmcp import FastMCP

mcp = FastMCP("Investment Calculators")


# ============================================================
# RISK CALCULATOR — v3 (con floor por leverage)
# ============================================================

@mcp.tool()
def calculate_risk_score(
    volatility_30d: float,
    max_drawdown_12m: float,
    liquidity: str,
    platform_regulated: bool,
    weight_in_portfolio_pct: float,
    leverage: float = 1.0,
) -> dict:
    """
    Calcula el risk score compuesto (1-10) para un activo de inversión.

    Args:
        volatility_30d: Desviación estándar de retornos diarios últimos 30 días (ej: 0.02 = 2%)
        max_drawdown_12m: Máxima caída desde máximo en 12 meses (ej: -0.25 = -25%)
        liquidity: Liquidez del activo: "instant", "hours", "days", "weeks", "months"
        platform_regulated: True si la plataforma está regulada (SEC, FCA, ASIC, etc.)
        weight_in_portfolio_pct: Peso del activo en el portafolio (ej: 30 = 30%)
        leverage: Apalancamiento (1.0 = sin apalancamiento, 2.0 = CFD 2x, etc.)
    """
    liquidity_map = {"instant": 0, "hours": 0.3, "days": 0.8, "weeks": 1.5, "months": 2.0}

    effective_vol = volatility_30d * leverage
    effective_dd = abs(max_drawdown_12m) * leverage

    vol_score = min(effective_vol / 0.5 * 3.0, 3.0)
    dd_score = min(effective_dd / 0.6 * 2.5, 2.5)
    liq_score = liquidity_map.get(liquidity, 1.0)
    plat_score = 0.0 if platform_regulated else 1.5
    conc_score = min(weight_in_portfolio_pct / 30.0, 1.0)

    leverage_score = 0.0
    if leverage >= 2.0:
        leverage_score = min((leverage - 1.0) * 1.5, 3.0)

    composite = round(min(vol_score + dd_score + liq_score + plat_score + conc_score + leverage_score, 10.0), 1)

    # ── FIX v3: Floor mínimo por leverage ──
    risk_floor = 0.0
    if leverage >= 5.0:
        risk_floor = 8.0
    elif leverage >= 3.0:
        risk_floor = 7.0
    elif leverage >= 2.0:
        risk_floor = 5.0
    elif leverage > 1.0:
        risk_floor = 4.0

    floor_applied = composite < risk_floor
    if floor_applied:
        composite = risk_floor

    max_alloc = 30.0
    if composite > 7:
        max_alloc = 10.0
    elif composite > 5:
        max_alloc = 20.0

    warnings = []
    if effective_vol > 0.3:
        warnings.append(f"Volatilidad efectiva extrema: {effective_vol:.0%} (vol {volatility_30d:.0%} x {leverage}x)")
    if effective_dd > 0.4:
        warnings.append(f"Drawdown efectivo severo: -{effective_dd:.0%} (dd {abs(max_drawdown_12m):.0%} x {leverage}x)")
    if weight_in_portfolio_pct > 30:
        warnings.append(f"Concentracion excesiva: {weight_in_portfolio_pct:.0f}% del portafolio")
    if not platform_regulated:
        warnings.append("Plataforma sin regulacion de primer nivel")
    if leverage > 1:
        warnings.append(f"Apalancamiento {leverage}x: caida de {50/leverage:.0f}% en el activo = liquidacion")
    if floor_applied:
        warnings.append(f"Score ajustado al minimo {risk_floor} por apalancamiento {leverage}x")

    return {
        "composite_score": composite,
        "components": {
            "volatility": round(vol_score, 2),
            "drawdown": round(dd_score, 2),
            "liquidity": round(liq_score, 2),
            "platform": round(plat_score, 2),
            "concentration": round(conc_score, 2),
            "leverage": round(leverage_score, 2),
        },
        "leverage": leverage,
        "risk_floor_applied": risk_floor if floor_applied else None,
        "effective_volatility": round(effective_vol, 4),
        "effective_drawdown": round(effective_dd, 4),
        "max_allocation_pct": max_alloc,
        "risk_label": "low" if composite <= 3.5 else "moderate" if composite <= 6.5 else "high",
        "warnings": warnings,
    }


@mcp.tool()
def calculate_correlation(prices_a: list[float], prices_b: list[float]) -> dict:
    """
    Calcula la correlacion de Pearson entre dos series de precios.

    Args:
        prices_a: Lista de precios de cierre del activo A (minimo 10 valores)
        prices_b: Lista de precios de cierre del activo B (misma longitud que prices_a)
    """
    n = min(len(prices_a), len(prices_b))
    if n < 10:
        return {"error": "Se necesitan al menos 10 datos de precio", "correlation": None}

    returns_a = [(prices_a[i] / prices_a[i - 1]) - 1 for i in range(1, n)]
    returns_b = [(prices_b[i] / prices_b[i - 1]) - 1 for i in range(1, n)]

    mean_a = sum(returns_a) / len(returns_a)
    mean_b = sum(returns_b) / len(returns_b)

    cov = sum((a - mean_a) * (b - mean_b) for a, b in zip(returns_a, returns_b)) / (len(returns_a) - 1)
    std_a = math.sqrt(sum((a - mean_a) ** 2 for a in returns_a) / (len(returns_a) - 1))
    std_b = math.sqrt(sum((b - mean_b) ** 2 for b in returns_b) / (len(returns_b) - 1))

    if std_a == 0 or std_b == 0:
        return {"correlation": 0.0, "is_problematic": False, "interpretation": "Sin variacion"}

    corr = round(cov / (std_a * std_b), 3)
    is_problematic = abs(corr) > 0.7

    if corr > 0.7:
        interp = "Alta correlacion positiva: se mueven juntos. Poca diversificacion."
    elif corr > 0.3:
        interp = "Correlacion moderada positiva."
    elif corr > -0.3:
        interp = "Baja correlacion: buena diversificacion."
    elif corr > -0.7:
        interp = "Correlacion negativa moderada: excelente diversificacion."
    else:
        interp = "Alta correlacion negativa: se mueven en direccion opuesta."

    return {"correlation": corr, "is_problematic": is_problematic, "interpretation": interp}


@mcp.tool()
def stress_test_portfolio(
    positions: list[dict],
    scenario: str = "moderate_crash",
) -> dict:
    """
    Simula el impacto de un escenario de crisis en el portafolio.

    Args:
        positions: Lista de posiciones, cada una con:
            {"asset_id": str, "amount_usd": float, "vertical": str, "monthly_income_usd": float, "leverage": float}
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
    results = []
    surviving_income = 0.0

    for p in positions:
        v = p.get("vertical", "equity")
        lev = p.get("leverage", 1.0)
        is_stable = "stable" in p.get("asset_id", "").lower() or "usdc" in p.get("asset_id", "").lower()
        base_rate = rates.get("stablecoin", 0) if is_stable else rates.get(v, -0.10)
        effective_rate = max(base_rate * lev, -1.0)

        impact_usd = round(p["amount_usd"] * effective_rate, 2)
        after = round(max(p["amount_usd"] + impact_usd, 0), 2)

        income_survival = 1.0 if is_stable else max(0.0, 1.0 + effective_rate)
        surviving = round(p.get("monthly_income_usd", 0) * income_survival, 2)
        surviving_income += surviving

        results.append({
            "asset_id": p["asset_id"],
            "before": p["amount_usd"],
            "leverage": lev,
            "base_impact_pct": round(base_rate * 100, 1),
            "effective_impact_pct": round(effective_rate * 100, 1),
            "impact_usd": impact_usd,
            "after": after,
            "liquidated": effective_rate <= -1.0,
            "surviving_monthly_income": surviving,
        })

    total_after = sum(r["after"] for r in results)
    return {
        "scenario": scenario,
        "total_before": round(total_before, 2),
        "total_after": round(total_after, 2),
        "total_loss_usd": round(total_after - total_before, 2),
        "total_loss_pct": round((total_after - total_before) / total_before * 100, 1) if total_before > 0 else 0,
        "surviving_monthly_income": round(surviving_income, 2),
        "positions": results,
    }


@mcp.tool()
def calculate_tax_impact(
    asset_type: str,
    annual_income_usd: float,
    has_w8ben: bool = False,
    usd_to_cop: float = 4200.0,
) -> dict:
    """
    Calcula el impacto fiscal para un activo de inversion bajo reglas colombianas (DIAN).

    Args:
        asset_type: "us_stock_dividend", "us_etf_dividend", "crypto_staking",
                    "crypto_trading_gain", "defi_yield", "forex_gain",
                    "copy_trading_gain", "equity_capital_gain"
        annual_income_usd: Ingreso anual estimado en USD
        has_w8ben: Si tiene formulario W-8BEN
        usd_to_cop: Tasa de cambio USD/COP actual
    """
    UVT_2025 = 47_065
    income_cop = annual_income_usd * usd_to_cop

    rules = {
        "us_stock_dividend": {"income_type": "renta_fuente_extranjera", "us_withholding": 0.15 if has_w8ben else 0.30, "co_rate": 0.0, "retention_source": 0.0, "w8ben_applicable": True},
        "us_etf_dividend": {"income_type": "renta_fuente_extranjera", "us_withholding": 0.15 if has_w8ben else 0.30, "co_rate": 0.0, "retention_source": 0.0, "w8ben_applicable": True},
        "crypto_staking": {"income_type": "ganancia_ocasional", "us_withholding": 0.0, "co_rate": 0.15, "retention_source": 0.0, "w8ben_applicable": False},
        "crypto_trading_gain": {"income_type": "ganancia_ocasional", "us_withholding": 0.0, "co_rate": 0.15, "retention_source": 0.0, "w8ben_applicable": False},
        "defi_yield": {"income_type": "ganancia_ocasional", "us_withholding": 0.0, "co_rate": 0.15, "retention_source": 0.0, "w8ben_applicable": False},
        "forex_gain": {"income_type": "renta_ordinaria", "us_withholding": 0.0, "co_rate": 0.0, "retention_source": 0.04, "w8ben_applicable": False},
        "copy_trading_gain": {"income_type": "renta_fuente_extranjera", "us_withholding": 0.0, "co_rate": 0.0, "retention_source": 0.0, "w8ben_applicable": False},
        "equity_capital_gain": {"income_type": "ganancia_ocasional", "us_withholding": 0.0, "co_rate": 0.15, "retention_source": 0.0, "w8ben_applicable": False},
    }

    r = rules.get(asset_type, rules["crypto_trading_gain"])
    after_us = annual_income_usd * (1 - r["us_withholding"])
    after_co = after_us * (1 - r["co_rate"]) * (1 - r["retention_source"])
    net_multiplier = round(after_co / annual_income_usd, 3) if annual_income_usd > 0 else 1.0
    total_tax = round(annual_income_usd - after_co, 2)

    must_declare = income_cop > 1400 * UVT_2025
    must_report_foreign = True

    actions = []
    if r["w8ben_applicable"] and not has_w8ben:
        actions.append("URGENTE: Llenar W-8BEN para reducir retencion USA del 30% al 15%")
    if must_declare:
        actions.append("Declarar renta anual ante la DIAN")
    if must_report_foreign:
        actions.append("Reportar activos en el exterior ante la DIAN")

    return {
        "asset_type": asset_type, "income_type": r["income_type"],
        "gross_income_usd": annual_income_usd,
        "net_income_usd": round(after_co, 2), "total_tax_usd": total_tax,
        "effective_tax_rate_pct": round((1 - net_multiplier) * 100, 1),
        "w8ben_applicable": r["w8ben_applicable"],
        "must_declare_renta": must_declare,
        "action_items": actions,
    }


@mcp.tool()
def calculate_position_size(
    capital_usd: float, risk_per_trade_pct: float,
    entry_price: float, stop_loss_price: float, leverage: float = 1.0,
) -> dict:
    """
    Calcula el tamano de posicion para un trade de Forex/CFDs.

    Args:
        capital_usd: Capital total disponible
        risk_per_trade_pct: % de riesgo por trade (recomendado: 1-2%)
        entry_price: Precio de entrada
        stop_loss_price: Precio de stop loss
        leverage: Apalancamiento (max recomendado: 5x)
    """
    if leverage > 10:
        return {"error": "Apalancamiento mayor a 10x es extremadamente riesgoso", "position_size": 0}

    risk_usd = capital_usd * (risk_per_trade_pct / 100)
    stop_distance = abs(entry_price - stop_loss_price)
    if stop_distance == 0:
        return {"error": "Stop loss no puede ser igual al precio de entrada", "position_size": 0}

    position_size = (risk_usd / stop_distance) * leverage
    position_value = position_size * entry_price
    margin_required = position_value / leverage

    warnings = []
    if risk_per_trade_pct > 3:
        warnings.append(f"Riesgo del {risk_per_trade_pct}% es alto. Recomendado: 1-2%")
    if leverage > 5:
        warnings.append(f"Apalancamiento {leverage}x es alto. Recomendado: 1-5x")

    return {
        "capital_usd": capital_usd, "risk_usd": round(risk_usd, 2),
        "leverage": leverage,
        "position_size_units": round(position_size, 4),
        "position_value_usd": round(position_value, 2),
        "margin_required_usd": round(margin_required, 2),
        "max_loss_usd": round(risk_usd, 2),
        "risk_reward_1_to_2_target": round(entry_price + (2 * stop_distance * (1 if entry_price > stop_loss_price else -1)), 4),
        "risk_reward_1_to_3_target": round(entry_price + (3 * stop_distance * (1 if entry_price > stop_loss_price else -1)), 4),
        "warnings": warnings,
    }


@mcp.tool()
def allocate_portfolio(
    capital_usd: float, monthly_savings_usd: float,
    risk_tolerance: str, horizon: str, exclude_verticals: list[str] | None = None,
) -> dict:
    """
    Genera la asignacion de portafolio por vertical.

    Args:
        capital_usd: Capital total
        monthly_savings_usd: Ahorro mensual
        risk_tolerance: "conservative", "moderate", "aggressive", "mixed"
        horizon: "short", "medium", "long", "combined"
        exclude_verticals: Verticales a excluir
    """
    excluded = set(exclude_verticals or [])
    templates = {
        "conservative": {"equity": 50, "defi": 20, "forex": 0, "social": 15, "reserve": 15},
        "moderate": {"equity": 40, "defi": 25, "forex": 10, "social": 15, "reserve": 10},
        "aggressive": {"equity": 30, "defi": 30, "forex": 20, "social": 15, "reserve": 5},
        "mixed": {"equity": 35, "defi": 25, "forex": 15, "social": 15, "reserve": 10},
    }
    base = templates.get(risk_tolerance, templates["moderate"]).copy()
    for v in excluded:
        if v in base and v != "reserve":
            redistributed = base[v]
            base[v] = 0
            remaining = [k for k in base if k not in excluded and k != "reserve" and base[k] > 0]
            if remaining:
                for r in remaining:
                    base[r] += redistributed / len(remaining)

    total_pct = sum(base.values())
    allocation = {k: round(v / total_pct * 100, 1) for k, v in base.items()}
    return {
        "allocation_pct": allocation,
        "allocation_usd": {k: round(capital_usd * v / 100, 2) for k, v in allocation.items()},
    }


# ============================================================
# SCENARIOS — v3 (con monthly_cost_usd)
# ============================================================

@mcp.tool()
def calculate_scenarios(
    amount_usd: float,
    expected_apy: float,
    volatility_annual: float,
    passive_income_annual_usd: float = 0.0,
    months: int = 12,
    leverage: float = 1.0,
    monthly_cost_usd: float = 0.0,
) -> dict:
    """
    Calcula 3 escenarios (optimista, base, pesimista) para una posicion de inversion.

    Args:
        amount_usd: Monto invertido (capital propio)
        expected_apy: Rendimiento anual esperado del activo subyacente (ej: 0.10 = 10%)
        volatility_annual: Volatilidad anualizada del activo (ej: 0.15 = 15%)
        passive_income_annual_usd: Ingreso pasivo anual fijo (dividendos, staking)
        months: Horizonte en meses
        leverage: Apalancamiento (1.0 = spot, 2.0 = CFD 2x)
        monthly_cost_usd: Costo mensual fijo (overnight fees CFDs). Se resta del rendimiento.
    """
    factor = months / 12.0
    passive = passive_income_annual_usd * factor
    total_costs = monthly_cost_usd * months

    optimistic_base = (expected_apy + volatility_annual) * factor
    base_base = expected_apy * factor
    pessimistic_base = (expected_apy - 1.5 * volatility_annual) * factor

    scenarios = []
    for name, change_base, prob in [
        ("optimistic", optimistic_base, 25),
        ("base", base_base, 50),
        ("pessimistic", pessimistic_base, 25),
    ]:
        change = max(change_base * leverage, -1.0)
        price_impact = amount_usd * change
        total = price_impact + passive - total_costs
        scenarios.append({
            "name": name,
            "probability_pct": prob,
            "asset_change_pct": round(change_base * 100, 1),
            "leveraged_change_pct": round(change * 100, 1),
            "price_impact_usd": round(price_impact, 2),
            "passive_income_usd": round(passive, 2),
            "costs_usd": round(total_costs, 2),
            "total_return_usd": round(total, 2),
            "total_return_pct": round(total / amount_usd * 100, 1) if amount_usd > 0 else 0,
            "portfolio_value": round(max(amount_usd + total, 0), 2),
            "liquidated": change <= -1.0,
        })

    return {
        "amount_usd": amount_usd,
        "leverage": leverage,
        "effective_exposure": round(amount_usd * leverage, 2),
        "monthly_cost_usd": monthly_cost_usd,
        "total_costs_over_period": round(total_costs, 2),
        "horizon_months": months,
        "scenarios": scenarios,
    }


if __name__ == "__main__":
    mcp.run()
