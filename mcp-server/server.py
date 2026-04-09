"""
MCP Server propio: calculadoras financieras para el sistema de inversión.
v2 — Corregido: leverage en risk_score, stress_test y scenarios.

Ejecutar: uv run --no-project --with fastmcp server.py
"""

import math
from fastmcp import FastMCP

mcp = FastMCP("Investment Calculators")


# ============================================================
# RISK CALCULATOR — v2 (con leverage)
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

    # Volatilidad ajustada por apalancamiento
    effective_vol = volatility_30d * leverage
    effective_dd = abs(max_drawdown_12m) * leverage

    vol_score = min(effective_vol / 0.5 * 3.0, 3.0)
    dd_score = min(effective_dd / 0.6 * 2.5, 2.5)
    liq_score = liquidity_map.get(liquidity, 1.0)
    plat_score = 0.0 if platform_regulated else 1.5
    conc_score = min(weight_in_portfolio_pct / 30.0, 1.0)

    # Bonus de riesgo por apalancamiento
    leverage_score = 0.0
    if leverage >= 2.0:
        leverage_score = min((leverage - 1.0) * 1.5, 3.0)  # 2x = +1.5, 3x = +3.0, 5x = +3.0 (cap)

    composite = round(min(vol_score + dd_score + liq_score + plat_score + conc_score + leverage_score, 10.0), 1)

    max_alloc = 30.0
    if composite > 7:
        max_alloc = 10.0
    elif composite > 5:
        max_alloc = 20.0

    warnings = []
    if effective_vol > 0.3:
        warnings.append(f"Volatilidad efectiva extrema: {effective_vol:.0%} (vol {volatility_30d:.0%} × {leverage}x)")
    if effective_dd > 0.4:
        warnings.append(f"Drawdown efectivo severo: -{effective_dd:.0%} (dd {abs(max_drawdown_12m):.0%} × {leverage}x)")
    if weight_in_portfolio_pct > 30:
        warnings.append(f"Concentración excesiva: {weight_in_portfolio_pct:.0f}% del portafolio")
    if not platform_regulated:
        warnings.append("Plataforma sin regulación de primer nivel")
    if leverage > 1:
        warnings.append(f"Apalancamiento {leverage}x: una caída de {50/leverage:.0f}% en el activo liquida la posición")

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
        "effective_volatility": round(effective_vol, 4),
        "effective_drawdown": round(effective_dd, 4),
        "max_allocation_pct": max_alloc,
        "risk_label": "low" if composite <= 3.5 else "moderate" if composite <= 6.5 else "high",
        "warnings": warnings,
    }


# ============================================================
# CORRELATION CALCULATOR
# ============================================================

@mcp.tool()
def calculate_correlation(prices_a: list[float], prices_b: list[float]) -> dict:
    """
    Calcula la correlación de Pearson entre dos series de precios.
    Útil para evaluar diversificación del portafolio.

    Args:
        prices_a: Lista de precios de cierre del activo A (mínimo 10 valores)
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
        return {"correlation": 0.0, "is_problematic": False, "interpretation": "Sin variación"}

    corr = round(cov / (std_a * std_b), 3)
    is_problematic = abs(corr) > 0.7

    if corr > 0.7:
        interp = "Alta correlación positiva: se mueven juntos. Poca diversificación."
    elif corr > 0.3:
        interp = "Correlación moderada positiva."
    elif corr > -0.3:
        interp = "Baja correlación: buena diversificación."
    elif corr > -0.7:
        interp = "Correlación negativa moderada: excelente diversificación."
    else:
        interp = "Alta correlación negativa: se mueven en dirección opuesta."

    return {"correlation": corr, "is_problematic": is_problematic, "interpretation": interp}


# ============================================================
# STRESS TEST — v2 (con leverage)
# ============================================================

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
            leverage es opcional (default 1.0). Usar 2.0 para CFD 2x, etc.
        scenario: "moderate_crash" (-15% equity, -25% crypto), "severe_crash" (-30% equity, -50% crypto),
                  "crypto_winter" (0% equity, -60% crypto), "stable_only" (mild impacts)
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

        # Aplicar multiplicador de apalancamiento al impacto
        effective_rate = base_rate * lev

        # Limitar pérdida al 100% del capital invertido (liquidación)
        effective_rate = max(effective_rate, -1.0)

        impact_usd = round(p["amount_usd"] * effective_rate, 2)
        after = round(max(p["amount_usd"] + impact_usd, 0), 2)  # No puede ser negativo

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


# ============================================================
# TAX CALCULATOR (Colombia / DIAN)
# ============================================================

@mcp.tool()
def calculate_tax_impact(
    asset_type: str,
    annual_income_usd: float,
    has_w8ben: bool = False,
    usd_to_cop: float = 4200.0,
) -> dict:
    """
    Calcula el impacto fiscal para un activo de inversión bajo reglas colombianas (DIAN).

    Args:
        asset_type: Tipo de activo: "us_stock_dividend", "us_etf_dividend", "crypto_staking",
                    "crypto_trading_gain", "defi_yield", "forex_gain", "copy_trading_gain",
                    "equity_capital_gain"
        annual_income_usd: Ingreso anual estimado en USD
        has_w8ben: Si tiene formulario W-8BEN llenado (reduce retención USA)
        usd_to_cop: Tasa de cambio USD/COP actual
    """
    UVT_2025 = 47_065
    income_cop = annual_income_usd * usd_to_cop

    rules = {
        "us_stock_dividend": {
            "income_type": "renta_fuente_extranjera",
            "us_withholding": 0.15 if has_w8ben else 0.30,
            "co_rate": 0.0,
            "retention_source": 0.0,
            "w8ben_applicable": True,
        },
        "us_etf_dividend": {
            "income_type": "renta_fuente_extranjera",
            "us_withholding": 0.15 if has_w8ben else 0.30,
            "co_rate": 0.0,
            "retention_source": 0.0,
            "w8ben_applicable": True,
        },
        "crypto_staking": {
            "income_type": "ganancia_ocasional",
            "us_withholding": 0.0,
            "co_rate": 0.15,
            "retention_source": 0.0,
            "w8ben_applicable": False,
        },
        "crypto_trading_gain": {
            "income_type": "ganancia_ocasional",
            "us_withholding": 0.0,
            "co_rate": 0.15,
            "retention_source": 0.0,
            "w8ben_applicable": False,
        },
        "defi_yield": {
            "income_type": "ganancia_ocasional",
            "us_withholding": 0.0,
            "co_rate": 0.15,
            "retention_source": 0.0,
            "w8ben_applicable": False,
        },
        "forex_gain": {
            "income_type": "renta_ordinaria",
            "us_withholding": 0.0,
            "co_rate": 0.0,
            "retention_source": 0.04,
            "w8ben_applicable": False,
        },
        "copy_trading_gain": {
            "income_type": "renta_fuente_extranjera",
            "us_withholding": 0.0,
            "co_rate": 0.0,
            "retention_source": 0.0,
            "w8ben_applicable": False,
        },
        "equity_capital_gain": {
            "income_type": "ganancia_ocasional",
            "us_withholding": 0.0,
            "co_rate": 0.15,
            "retention_source": 0.0,
            "w8ben_applicable": False,
        },
    }

    r = rules.get(asset_type, rules["crypto_trading_gain"])
    after_us = annual_income_usd * (1 - r["us_withholding"])
    after_co = after_us * (1 - r["co_rate"]) * (1 - r["retention_source"])
    net_multiplier = round(after_co / annual_income_usd, 3) if annual_income_usd > 0 else 1.0
    total_tax = round(annual_income_usd - after_co, 2)

    must_declare = income_cop > 1400 * UVT_2025
    must_report_foreign = True
    electronic_invoice = income_cop > 3500 * UVT_2025

    actions = []
    if r["w8ben_applicable"] and not has_w8ben:
        actions.append("URGENTE: Llenar formulario W-8BEN para reducir retención USA del 30% al 15%")
    if must_declare:
        actions.append("Declarar renta anual ante la DIAN")
    if must_report_foreign:
        actions.append("Reportar activos en el exterior ante la DIAN")
    if electronic_invoice:
        actions.append("Habilitar facturación electrónica (ingresos superan 3500 UVT)")

    return {
        "asset_type": asset_type,
        "income_type": r["income_type"],
        "gross_income_usd": annual_income_usd,
        "us_withholding_pct": r["us_withholding"],
        "us_withholding_usd": round(annual_income_usd * r["us_withholding"], 2),
        "co_tax_pct": r["co_rate"],
        "co_retention_pct": r["retention_source"],
        "net_income_usd": round(after_co, 2),
        "total_tax_usd": total_tax,
        "net_return_multiplier": net_multiplier,
        "effective_tax_rate_pct": round((1 - net_multiplier) * 100, 1),
        "w8ben_applicable": r["w8ben_applicable"],
        "w8ben_benefit": f"Reduce retención USA del 30% al 15% (ahorras ${round(annual_income_usd * 0.15, 2)}/año)" if r["w8ben_applicable"] else None,
        "must_declare_renta": must_declare,
        "must_report_foreign_assets": must_report_foreign,
        "electronic_invoice_required": electronic_invoice,
        "action_items": actions,
    }


# ============================================================
# POSITION SIZING (Forex)
# ============================================================

@mcp.tool()
def calculate_position_size(
    capital_usd: float,
    risk_per_trade_pct: float,
    entry_price: float,
    stop_loss_price: float,
    leverage: float = 1.0,
) -> dict:
    """
    Calcula el tamaño de posición para un trade de Forex/CFDs.

    Args:
        capital_usd: Capital total disponible para trading
        risk_per_trade_pct: Porcentaje de riesgo por trade (recomendado: 1-2%)
        entry_price: Precio de entrada
        stop_loss_price: Precio de stop loss
        leverage: Apalancamiento (recomendado máximo 5x para principiantes)
    """
    if leverage > 10:
        return {"error": "Apalancamiento mayor a 10x es extremadamente riesgoso", "position_size": 0}

    risk_usd = capital_usd * (risk_per_trade_pct / 100)
    stop_distance = abs(entry_price - stop_loss_price)
    stop_distance_pct = stop_distance / entry_price * 100

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
    if margin_required > capital_usd * 0.5:
        warnings.append(f"El margen requerido (${margin_required:.2f}) supera el 50% del capital")

    return {
        "capital_usd": capital_usd,
        "risk_per_trade_pct": risk_per_trade_pct,
        "risk_usd": round(risk_usd, 2),
        "entry_price": entry_price,
        "stop_loss_price": stop_loss_price,
        "stop_distance_pct": round(stop_distance_pct, 2),
        "leverage": leverage,
        "position_size_units": round(position_size, 4),
        "position_value_usd": round(position_value, 2),
        "margin_required_usd": round(margin_required, 2),
        "max_loss_usd": round(risk_usd, 2),
        "risk_reward_1_to_2_target": round(entry_price + (2 * stop_distance * (1 if entry_price > stop_loss_price else -1)), 4),
        "risk_reward_1_to_3_target": round(entry_price + (3 * stop_distance * (1 if entry_price > stop_loss_price else -1)), 4),
        "warnings": warnings,
    }


# ============================================================
# PORTFOLIO ALLOCATOR
# ============================================================

@mcp.tool()
def allocate_portfolio(
    capital_usd: float,
    monthly_savings_usd: float,
    risk_tolerance: str,
    horizon: str,
    exclude_verticals: list[str] | None = None,
) -> dict:
    """
    Genera la asignación de portafolio por vertical y fase.

    Args:
        capital_usd: Capital total disponible
        monthly_savings_usd: Ahorro mensual para reinvertir
        risk_tolerance: "conservative", "moderate", "aggressive", "mixed"
        horizon: "short" (1-6m), "medium" (6-18m), "long" (2-5y), "combined"
        exclude_verticals: Verticales a excluir, ej: ["forex"]
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
                per_each = redistributed / len(remaining)
                for r in remaining:
                    base[r] += per_each

    total_pct = sum(base.values())
    allocation = {k: round(v / total_pct * 100, 1) for k, v in base.items()}
    amounts = {k: round(capital_usd * v / 100, 2) for k, v in allocation.items()}

    return {
        "allocation_pct": allocation,
        "allocation_usd": amounts,
        "constraints_applied": {
            "max_single_position": "30%",
            "max_single_vertical": "50%",
            "min_reserve": "5-15%",
            "excluded": list(excluded),
        },
    }


# ============================================================
# SCENARIOS — v2 (con leverage)
# ============================================================

@mcp.tool()
def calculate_scenarios(
    amount_usd: float,
    expected_apy: float,
    volatility_annual: float,
    passive_income_annual_usd: float = 0.0,
    months: int = 12,
    leverage: float = 1.0,
) -> dict:
    """
    Calcula 3 escenarios (optimista, base, pesimista) para una posición de inversión.

    Args:
        amount_usd: Monto invertido (capital propio, no la exposición apalancada)
        expected_apy: Rendimiento anual esperado del activo subyacente (ej: 0.10 = 10%)
        volatility_annual: Volatilidad anualizada del activo subyacente (ej: 0.15 = 15%)
        passive_income_annual_usd: Ingreso pasivo anual fijo (dividendos, staking rewards)
        months: Horizonte en meses
        leverage: Apalancamiento (1.0 = spot, 2.0 = CFD 2x). Multiplica rendimiento Y pérdida.
    """
    factor = months / 12.0
    passive = passive_income_annual_usd * factor

    # Rendimientos del activo subyacente
    optimistic_return_base = (expected_apy + volatility_annual) * factor
    base_return_base = expected_apy * factor
    pessimistic_return_base = (expected_apy - 1.5 * volatility_annual) * factor

    scenarios = []
    for name, price_change_base, prob in [
        ("optimistic", optimistic_return_base, 25),
        ("base", base_return_base, 50),
        ("pessimistic", pessimistic_return_base, 25),
    ]:
        # Aplicar leverage al rendimiento
        price_change = price_change_base * leverage

        # Limitar pérdida al -100% (liquidación)
        price_change = max(price_change, -1.0)

        price_impact = amount_usd * price_change
        total = price_impact + passive
        scenarios.append({
            "name": name,
            "probability_pct": prob,
            "asset_change_pct": round(price_change_base * 100, 1),
            "leveraged_change_pct": round(price_change * 100, 1),
            "price_impact_usd": round(price_impact, 2),
            "passive_income_usd": round(passive, 2),
            "total_return_usd": round(total, 2),
            "total_return_pct": round(total / amount_usd * 100, 1) if amount_usd > 0 else 0,
            "portfolio_value": round(max(amount_usd + total, 0), 2),
            "liquidated": price_change <= -1.0,
        })

    return {
        "amount_usd": amount_usd,
        "leverage": leverage,
        "effective_exposure": round(amount_usd * leverage, 2),
        "horizon_months": months,
        "scenarios": scenarios,
    }


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    mcp.run()
