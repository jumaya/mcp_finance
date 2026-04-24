"""
MCP Server propio: calculadoras financieras para el sistema de inversión.
v3 — Fix 1: floor mínimo de risk score por leverage
     Fix 2: monthly_cost_usd en calculate_scenarios para overnight fees
v4 — Fix 3: validate_allocation_minimums — checkpoint determinística
     para mínimos por venue/producto (antes el §4 de platforms_skill.md
     era prosa; ahora es una tool que el agente DEBE llamar post-allocate).
v5 — Fix 4: calculate_scenarios modela explícitamente retención de
     dividendos (dividend_withholding_pct) y funding rate diario de
     futures (funding_rate_daily_pct). Antes el agente tenía que
     embutirlos en passive_income_annual_usd / monthly_cost_usd a mano
     y se saltaba la retención del 30% USA o el funding de Binance
     Futures (§1.5 y §2.6 de platforms_skill.md).
v6 — Fix 5: compare_portfolio_to_baseline — checkpoint determinística
     para seguimiento post-inversión. Antes el tracking_skill.md hacía
     P&L, desviaciones de peso, detección de nuevas/cerradas y alertas
     semáforo (§Fase D) en prompting, lo cual es propenso a errores de
     aritmética en portafolios con 5+ posiciones y viola el principio
     #1 de system.md ("nunca inventes números; si no tienes el dato,
     consúltalo con una tool"). Ahora la aritmética del tracking es
     una tool.
v7 — Fix 6: calculate_portfolio_risk_score — ajuste por correlación.
     Antes R6 de risk_rules.md definía score_ponderado = Σ(weight_i ×
     risk_score_i), lo cual ignora por completo la correlación entre
     posiciones. Dos activos con risk=8 correlacionados a 0.9 son
     mucho más riesgosos que los mismos dos activos correlacionados
     a 0.2, pero la suma ponderada los trata idénticamente. La nueva
     tool recibe una correlation_matrix opcional y ajusta el score
     agregado: si la correlación promedio ponderada > 0.7 → +1.0
     (portafolio menos diversificado de lo que parece), si < 0.3 →
     -0.5 (diversificación real reduce riesgo agregado). Regla
     simple y defendible; documentada en risk_rules.md R6.
v8 — Fix 7: allocate_portfolio dinámico.
     Antes había 4 plantillas Python literales; dos usuarios con el
     mismo risk_tolerance y capital obtenían EXACTAMENTE el mismo
     split, sin importar el contexto de mercado, el horizonte numérico,
     la edad, ni las preferencias. Esto violaba el principio #1 de
     system.md ("nunca inventes números; si no tienes el dato,
     consúltalo con una tool"): la decisión de asignación es la MÁS
     consecuencial del plan y se tomaba sin mirar ningún dato real.
     Ahora los templates son el ANCLA y sobre ellos se aplican ajustes
     incrementales (en puntos porcentuales) por: (a) contexto macro
     del market_intelligence_skill — RSI SPY/QQQ, TVL trend, BTC
     dominance; (b) horizonte numérico en meses — <12m reduce equity
     y sube reserve, >=36m lo inverso; (c) preferencias del usuario;
     (d) régimen de capital pequeño (<$200) que fuerza consolidación
     para cumplir mínimos de venue. Devuelve `rationale` (list[str])
     y `adjustments_applied` (trazabilidad pp a pp) para que el plan
     explique al usuario qué ajustes se aplicaron y por qué. Los
     ajustes están capeados (±8pp por vertical) para no violar
     risk_rules.md R1/R2 y el piso de reserve (R3) se aplica siempre.

Ejecutar: uv run --no-project --with fastmcp server.py
"""

import math
from fastmcp import FastMCP

mcp = FastMCP("Investment Calculators")


# ============================================================
# MÍNIMOS POR VENUE + PRODUCTO (single source of truth)
# Fuente: platforms_skill.md §1.3 (eToro) y §2 (Binance).
# Si cambia un mínimo en la plataforma, se actualiza AQUÍ
# y queda reflejado en cualquier validación.
# ============================================================

VENUE_MINIMUMS_USD = {
    "eToro": {
        "stock_spot":          10.0,
        "etf_spot":            10.0,
        "crypto_spot":         10.0,
        "cfd_stock":           50.0,   # margen
        "cfd_etf":             50.0,
        "cfd_crypto":          50.0,
        "cfd_forex":           50.0,   # proxy conservador; el real varía por par
        "cfd_commodity":       50.0,
        "cfd_index":           50.0,
        "copy_trader":        200.0,
        "smart_portfolio":    500.0,
        "top_trader_portfolio": 5000.0,
    },
    "Binance": {
        "spot_crypto":         10.0,   # técnicamente permite menos, pero por ruido de fees el plan pide $10
        "simple_earn":          1.0,
        "futures":             20.0,   # proxy: depende del par, pero < $20 raramente vale la pena
        "staking":              1.0,
        "copy_trading":       100.0,   # Binance copy trading default
    },
    "Capital.com": {
        "cfd_forex":           20.0,   # proxy; Capital.com permite margen bajo
        "cfd_commodity":       20.0,
        "cfd_stock":           20.0,
        "cfd_index":           20.0,
    },
    "Aave": {
        "supply":              50.0,   # gas-driven: no vale la pena < $50 en mainnet
        "borrow":             100.0,
    },
    "Lido": {
        "stake_eth":           50.0,
    },
    "Ethena": {
        "susde":               50.0,
    },
}


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
def calculate_portfolio_risk_score(
    positions: list[dict],
    correlation_matrix: list[list[float]] | None = None,
) -> dict:
    """
    Calcula el risk score agregado del portafolio ajustando por correlación.

    Antes (R6 v1): score_ponderado = Σ(weight_i × risk_score_i). Ignoraba
    correlación. Ahora: se aplica un ajuste por correlación promedio
    ponderada para reflejar diversificación real.

    Regla de ajuste (simple y defendible):
      - correlación promedio ponderada > 0.7 → score_final = score_ponderado + 1.0
        (posiciones se mueven juntas; diversificación aparente, no real)
      - correlación promedio ponderada < 0.3 → score_final = score_ponderado - 0.5
        (diversificación real reduce el riesgo agregado)
      - en medio (0.3 ≤ corr ≤ 0.7) → sin ajuste

    La correlación promedio ponderada se calcula sobre todos los pares (i, j)
    con i < j, donde el peso de cada par es (weight_i × weight_j). Esto le da
    más importancia a los pares de posiciones grandes que a pares de posiciones
    pequeñas.

    Args:
        positions: Lista de posiciones, cada una con:
            {"asset_id": str, "weight_pct": float, "risk_score": float}
            weight_pct en porcentaje (ej: 25 = 25%), risk_score en escala 1-10.
        correlation_matrix: Matriz N×N de correlaciones entre posiciones, en el
            mismo orden que `positions`. Diagonal = 1.0, simétrica. Si se omite,
            no se aplica ajuste y se devuelve solo el score ponderado base.

    Returns:
        dict con:
          - weighted_score: Σ(weight_i × risk_score_i) (base, sin ajuste)
          - avg_weighted_correlation: correlación promedio ponderada por pares
          - correlation_adjustment: ajuste aplicado (+1.0, -0.5, o 0.0)
          - adjusted_score: weighted_score + correlation_adjustment (clamp [1, 10])
          - interpretation: texto explicativo
          - warnings: advertencias (matriz mal formada, pesos fuera de rango, etc.)
    """
    warnings: list[str] = []

    if not positions:
        return {
            "error": "Lista de posiciones vacía",
            "weighted_score": None,
            "adjusted_score": None,
        }

    # ── 1. Score ponderado base (compatible con R6 v1) ──
    total_weight = sum(p.get("weight_pct", 0) for p in positions)
    if total_weight <= 0:
        return {
            "error": "Suma de weight_pct debe ser > 0",
            "weighted_score": None,
            "adjusted_score": None,
        }
    if abs(total_weight - 100.0) > 1.0:
        warnings.append(
            f"Suma de weight_pct = {total_weight:.1f}% (esperado ~100%). "
            "Se normaliza internamente para el cálculo."
        )

    # Normalizo los pesos a fracción (0-1) para que la aritmética sea limpia
    # aunque el usuario pase 100% total o no.
    weights = [p.get("weight_pct", 0) / total_weight for p in positions]
    scores = [float(p.get("risk_score", 0)) for p in positions]

    weighted_score = sum(w * s for w, s in zip(weights, scores))

    # ── 2. Validación de correlation_matrix (si se proporcionó) ──
    n = len(positions)
    adjustment = 0.0
    avg_weighted_corr: float | None = None

    if correlation_matrix is None:
        warnings.append(
            "No se proporcionó correlation_matrix: se devuelve solo el score "
            "ponderado base sin ajuste. Ejecuta calculate_correlation para cada "
            "par y arma la matriz para obtener el score ajustado."
        )
    else:
        # Validar dimensiones
        matrix_ok = (
            len(correlation_matrix) == n
            and all(isinstance(row, list) and len(row) == n for row in correlation_matrix)
        )
        if not matrix_ok:
            warnings.append(
                f"correlation_matrix debe ser {n}x{n}. Se ignora y se devuelve "
                "solo el score ponderado base."
            )
        elif n < 2:
            # Con una sola posición no hay pares que correlacionar
            warnings.append(
                "Portafolio de una sola posición: correlación no aplica. "
                "Score = risk_score de la única posición."
            )
        else:
            # ── 3. Correlación promedio ponderada por pares (i < j) ──
            # Peso de cada par = w_i × w_j. Con pesos normalizados a 1, esto
            # le da importancia relativa correcta a cada par según el tamaño
            # combinado de las dos posiciones.
            num = 0.0
            den = 0.0
            for i in range(n):
                for j in range(i + 1, n):
                    try:
                        c = float(correlation_matrix[i][j])
                    except (TypeError, ValueError):
                        warnings.append(
                            f"correlation_matrix[{i}][{j}] no es numérico. "
                            "Se ignora la matriz."
                        )
                        num = den = 0.0
                        break
                    # Clamp defensivo: Pearson ∈ [-1, 1]
                    if c < -1.0 or c > 1.0:
                        warnings.append(
                            f"correlation_matrix[{i}][{j}]={c:.3f} fuera de "
                            "[-1, 1]. Se satura."
                        )
                        c = max(-1.0, min(1.0, c))
                    pair_weight = weights[i] * weights[j]
                    num += pair_weight * c
                    den += pair_weight
                else:
                    continue
                break

            if den > 0:
                avg_weighted_corr = num / den

                # ── 4. Regla de ajuste (R6 v2) ──
                if avg_weighted_corr > 0.7:
                    adjustment = 1.0
                elif avg_weighted_corr < 0.3:
                    adjustment = -0.5
                else:
                    adjustment = 0.0

    # ── 5. Score final con clamp a [1, 10] ──
    adjusted_score = weighted_score + adjustment
    adjusted_score = max(1.0, min(10.0, adjusted_score))

    # ── 6. Interpretación para el agente ──
    if avg_weighted_corr is None:
        interp = (
            f"Score ponderado base: {weighted_score:.2f}. Sin ajuste por "
            "correlación (matriz no provista o portafolio de una sola posición)."
        )
    elif adjustment > 0:
        interp = (
            f"Correlación promedio ponderada {avg_weighted_corr:.2f} > 0.7: "
            f"las posiciones tienden a moverse juntas, la diversificación es "
            f"aparente. Score ajustado +1.0 → {adjusted_score:.2f}."
        )
    elif adjustment < 0:
        interp = (
            f"Correlación promedio ponderada {avg_weighted_corr:.2f} < 0.3: "
            f"diversificación real entre posiciones. Score ajustado -0.5 → "
            f"{adjusted_score:.2f}."
        )
    else:
        interp = (
            f"Correlación promedio ponderada {avg_weighted_corr:.2f} en zona "
            f"neutra (0.3–0.7). Sin ajuste. Score = {adjusted_score:.2f}."
        )

    risk_label = (
        "low" if adjusted_score <= 3.5
        else "moderate" if adjusted_score <= 6.5
        else "high"
    )

    return {
        "weighted_score": round(weighted_score, 2),
        "avg_weighted_correlation": (
            round(avg_weighted_corr, 3) if avg_weighted_corr is not None else None
        ),
        "correlation_adjustment": round(adjustment, 2),
        "adjusted_score": round(adjusted_score, 2),
        "risk_label": risk_label,
        "n_positions": n,
        "total_weight_pct": round(total_weight, 2),
        "interpretation": interp,
        "warnings": warnings,
    }


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


# ============================================================
# ALLOCATE_PORTFOLIO — v8: asignación dinámica
# ============================================================
# Antes: 4 plantillas Python literales (conservative/moderate/aggressive/mixed).
# Dos usuarios "agresivos" con $1000 obtenían SIEMPRE el mismo split, sin mirar
# al mercado (RSI SPY/QQQ, TVL DeFi, BTC dominance del market_intelligence_skill),
# ni al horizonte numérico, ni a preferencias, ni a capital operativo real.
#
# Ahora: los templates se usan como ANCLA y sobre ellos se aplican ajustes
# incrementales en puntos porcentuales (pp), con topes de seguridad para no
# violar risk_rules.md (R1 30% posición / R2 50% vertical / R3 10% reserve).
#
# Ajustes en orden:
#   1) Exclusiones del usuario (redistribución a otros verticales direccionales).
#   2) Macro (RSI SPY/QQQ, TVL trend DeFi, BTC dominance) — ±5pp típico.
#   3) Horizonte (horizon_months numérico) — horizonte corto reduce equity
#      y aumenta reserve/defi-stable; horizonte largo hace lo inverso.
#   4) Preferencias del usuario (preferred_verticals) — +3pp a cada preferido
#      descontado pro-rata de los no preferidos direccionales.
#   5) Floor de reserve (10% R3 estricto, salvo aggressive que admite 5%).
#   6) Concentración por capital pequeño (<$200) — fuerza 1-2 verticales
#      para que cada slice sea viable en mínimos de venue.
#
# Devuelve también `rationale` (lista de strings legibles) y
# `adjustments_applied` (trazabilidad estructurada pp por pp).
# ============================================================

# Templates ancla (compat retro con v7). Expuestos como constante para
# que tests y auditoría puedan inspeccionarlos sin importar la función.
ALLOCATION_TEMPLATES = {
    "conservative": {"equity": 50, "defi": 20, "forex": 0,  "social": 15, "reserve": 15},
    "moderate":     {"equity": 40, "defi": 25, "forex": 10, "social": 15, "reserve": 10},
    "aggressive":   {"equity": 30, "defi": 30, "forex": 20, "social": 15, "reserve": 5},
    "mixed":        {"equity": 35, "defi": 25, "forex": 15, "social": 15, "reserve": 10},
}

# Piso de reserve por perfil (R3 de risk_rules.md — estricto 10%, excepto
# aggressive donde el template ancla ya baja a 5% y lo respetamos).
_RESERVE_FLOOR = {
    "conservative": 10.0,
    "moderate":     10.0,
    "aggressive":   5.0,
    "mixed":        10.0,
}

# Umbrales RSI para sobreventa / sobrecompra (convención técnica estándar).
_RSI_OVERSOLD = 30
_RSI_OVERBOUGHT = 70

# Mapeo horizonte string → meses (fallback si solo llega el string viejo).
_HORIZON_STRING_TO_MONTHS = {
    "short": 9,      # <1 año, punto medio del rango corto
    "medium": 24,    # 1-3 años
    "long": 60,      # >3 años, 5y como proxy
    "combined": 24,  # tratar como medio por defecto
}

# Capital operativo mínimo por slice para que una posición en un vertical
# sea viable en los venues del sistema (eToro CFD $50 + copy $200 + spread).
# Por debajo de este umbral, el slice se consolida con otro vertical.
_MIN_SLICE_USD = 75.0
_SMALL_CAPITAL_THRESHOLD_USD = 200.0


def _clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def _redistribute_excluded(
    base: dict, excluded: set, directional: list
) -> dict:
    """Saca a cero los verticales excluidos y reparte su peso entre los
    direccionales restantes (no en reserve, que tiene piso propio)."""
    out = dict(base)
    for v in excluded:
        if v in out and v != "reserve":
            dropped = out[v]
            out[v] = 0
            remaining = [
                k for k in directional
                if k not in excluded and out.get(k, 0) > 0
            ]
            if remaining:
                per = dropped / len(remaining)
                for r in remaining:
                    out[r] += per
            else:
                # No hay a dónde mover → va a reserve (safe harbor).
                out["reserve"] = out.get("reserve", 0) + dropped
    return out


def _apply_macro_adjustments(
    alloc: dict, macro: dict, excluded: set
) -> tuple[dict, list[str], list[dict]]:
    """Ajusta pesos según contexto macro. Deltas en pp, capeados a ±8pp
    totales por vertical para no romper risk_rules R2. Retorna alloc
    ajustada, rationale (strings) y trace (dicts)."""
    out = dict(alloc)
    rationale: list[str] = []
    trace: list[dict] = []
    if not macro:
        return out, rationale, trace

    # ---- RSI SPY: sobreventa → +5pp equity, sobrecompra → -5pp equity.
    rsi_spy = macro.get("rsi_spy")
    if isinstance(rsi_spy, (int, float)) and "equity" not in excluded:
        if rsi_spy < _RSI_OVERSOLD:
            delta = +5.0
            out["equity"] += delta
            rationale.append(
                f"RSI(SPY)={rsi_spy:.0f} < {_RSI_OVERSOLD}: sobreventa macro, "
                f"+{delta:.0f}pp a equity."
            )
            trace.append({"source": "rsi_spy", "vertical": "equity", "delta_pp": delta})
        elif rsi_spy > _RSI_OVERBOUGHT:
            delta = -5.0
            out["equity"] += delta
            rationale.append(
                f"RSI(SPY)={rsi_spy:.0f} > {_RSI_OVERBOUGHT}: sobrecompra macro, "
                f"{delta:.0f}pp a equity."
            )
            trace.append({"source": "rsi_spy", "vertical": "equity", "delta_pp": delta})

    # ---- RSI QQQ: mismo tratamiento pero con peso menor (±3pp) porque
    # QQQ y SPY están altamente correlacionados; evitamos doble conteo.
    rsi_qqq = macro.get("rsi_qqq")
    if isinstance(rsi_qqq, (int, float)) and "equity" not in excluded:
        if rsi_qqq < _RSI_OVERSOLD:
            delta = +3.0
            out["equity"] += delta
            rationale.append(
                f"RSI(QQQ)={rsi_qqq:.0f} < {_RSI_OVERSOLD}: sobreventa tech, "
                f"+{delta:.0f}pp a equity."
            )
            trace.append({"source": "rsi_qqq", "vertical": "equity", "delta_pp": delta})
        elif rsi_qqq > _RSI_OVERBOUGHT:
            delta = -3.0
            out["equity"] += delta
            rationale.append(
                f"RSI(QQQ)={rsi_qqq:.0f} > {_RSI_OVERBOUGHT}: sobrecompra tech, "
                f"{delta:.0f}pp a equity."
            )
            trace.append({"source": "rsi_qqq", "vertical": "equity", "delta_pp": delta})

    # ---- TVL trend DeFi: "up" → +4pp defi, "down" → -4pp defi.
    # Acepta tanto string ("up"/"down"/"flat") como número (% cambio 30d).
    tvl_trend = macro.get("tvl_trend")
    if tvl_trend is not None and "defi" not in excluded:
        tvl_up = (isinstance(tvl_trend, str) and tvl_trend.lower() == "up") or \
                 (isinstance(tvl_trend, (int, float)) and tvl_trend > 10)
        tvl_down = (isinstance(tvl_trend, str) and tvl_trend.lower() == "down") or \
                   (isinstance(tvl_trend, (int, float)) and tvl_trend < -10)
        if tvl_up:
            delta = +4.0
            out["defi"] += delta
            rationale.append(
                f"TVL DeFi en tendencia alcista ({tvl_trend}): +{delta:.0f}pp a defi."
            )
            trace.append({"source": "tvl_trend", "vertical": "defi", "delta_pp": delta})
        elif tvl_down:
            delta = -4.0
            out["defi"] += delta
            rationale.append(
                f"TVL DeFi en tendencia bajista ({tvl_trend}): {delta:.0f}pp a defi."
            )
            trace.append({"source": "tvl_trend", "vertical": "defi", "delta_pp": delta})

    # ---- BTC dominance: > 60% → cripto concentrado en BTC, alts sufren
    # (-3pp defi); < 45% → alt season, algo más de espacio (+3pp defi).
    btc_dom = macro.get("btc_dominance")
    if isinstance(btc_dom, (int, float)) and "defi" not in excluded:
        if btc_dom > 60:
            delta = -3.0
            out["defi"] += delta
            rationale.append(
                f"BTC dominance={btc_dom:.1f}% > 60%: régimen BTC-heavy, "
                f"alts debilitados, {delta:.0f}pp a defi."
            )
            trace.append({"source": "btc_dominance", "vertical": "defi", "delta_pp": delta})
        elif btc_dom < 45:
            delta = +3.0
            out["defi"] += delta
            rationale.append(
                f"BTC dominance={btc_dom:.1f}% < 45%: posible alt season, "
                f"+{delta:.0f}pp a defi."
            )
            trace.append({"source": "btc_dominance", "vertical": "defi", "delta_pp": delta})

    # Cap total de deltas por vertical (±8pp) — evita sobrerreacción si
    # varias señales empujan en el mismo sentido. Compara contra el alloc
    # pre-macro que recibimos.
    for v in out:
        net_delta = out[v] - alloc[v]
        if abs(net_delta) > 8.0:
            capped = _clamp(net_delta, -8.0, 8.0)
            out[v] = alloc[v] + capped
            rationale.append(
                f"Ajuste macro neto a {v} capeado a {capped:+.0f}pp "
                f"(de {net_delta:+.1f}pp) para respetar risk_rules."
            )
            trace.append({"source": "cap", "vertical": v, "delta_pp": capped - net_delta})

    return out, rationale, trace


def _apply_horizon_adjustment(
    alloc: dict, horizon_months: float, excluded: set
) -> tuple[dict, list[str], list[dict]]:
    """Horizonte corto (<12m) → menos equity, más reserve/defi estable.
    Horizonte largo (>=36m) → lo inverso, mayor equity, menor reserve.
    Deltas modestos (±4pp) porque horizonte ya está reflejado en el
    risk_tolerance del usuario a menudo."""
    out = dict(alloc)
    rationale: list[str] = []
    trace: list[dict] = []

    if horizon_months < 12:
        # Corto plazo: reducir equity (volátil), subir reserve (liquidez).
        delta_equity = -4.0
        delta_reserve = +4.0
        if "equity" not in excluded:
            out["equity"] += delta_equity
            out["reserve"] += delta_reserve
            rationale.append(
                f"Horizonte={horizon_months:.0f}m < 12m: prioridad liquidez, "
                f"{delta_equity:.0f}pp equity → +{delta_reserve:.0f}pp reserve."
            )
            trace.append({"source": "horizon_short", "vertical": "equity",  "delta_pp": delta_equity})
            trace.append({"source": "horizon_short", "vertical": "reserve", "delta_pp": delta_reserve})
    elif horizon_months >= 36:
        # Largo plazo: espacio para equity (compounding), menos cash drag.
        delta_equity = +4.0
        delta_reserve = -2.0
        delta_forex = -2.0 if "forex" not in excluded else 0.0
        if "equity" not in excluded:
            out["equity"] += delta_equity
            out["reserve"] += delta_reserve
            out["forex"] += delta_forex
            msg = (
                f"Horizonte={horizon_months:.0f}m >= 36m: ventana para compounding, "
                f"+{delta_equity:.0f}pp equity, {delta_reserve:.0f}pp reserve"
            )
            if delta_forex:
                msg += f", {delta_forex:.0f}pp forex"
            msg += "."
            rationale.append(msg)
            trace.append({"source": "horizon_long", "vertical": "equity",  "delta_pp": delta_equity})
            trace.append({"source": "horizon_long", "vertical": "reserve", "delta_pp": delta_reserve})
            if delta_forex:
                trace.append({"source": "horizon_long", "vertical": "forex", "delta_pp": delta_forex})
    # 12-36m: zona neutra, no se toca.

    return out, rationale, trace


def _apply_preferences(
    alloc: dict, preferred: list[str], excluded: set
) -> tuple[dict, list[str], list[dict]]:
    """El usuario marcó preferencia por ciertos verticales → +3pp a cada
    preferido, descontado pro-rata de los direccionales no preferidos.
    No toca reserve."""
    out = dict(alloc)
    rationale: list[str] = []
    trace: list[dict] = []
    if not preferred:
        return out, rationale, trace

    directional = ["equity", "defi", "forex", "social"]
    valid_prefs = [
        v for v in preferred
        if v in directional and v not in excluded and out.get(v, 0) > 0
    ]
    if not valid_prefs:
        return out, rationale, trace

    boost_per_pref = 3.0
    total_boost = boost_per_pref * len(valid_prefs)
    donors = [
        v for v in directional
        if v not in valid_prefs and v not in excluded and out.get(v, 0) > 0
    ]
    if not donors:
        # Sin donantes direccionales, descontar de reserve (pero sin pasar
        # del piso — el chequeo de piso posterior lo corrige si hace falta).
        out["reserve"] -= total_boost
        for v in valid_prefs:
            out[v] += boost_per_pref
            trace.append({"source": "preference", "vertical": v, "delta_pp": boost_per_pref})
        trace.append({"source": "preference", "vertical": "reserve", "delta_pp": -total_boost})
    else:
        per_donor = total_boost / len(donors)
        for v in valid_prefs:
            out[v] += boost_per_pref
            trace.append({"source": "preference", "vertical": v, "delta_pp": boost_per_pref})
        for v in donors:
            out[v] -= per_donor
            trace.append({"source": "preference", "vertical": v, "delta_pp": -per_donor})

    rationale.append(
        f"Preferencia del usuario por {valid_prefs}: +{boost_per_pref:.0f}pp a cada uno, "
        f"descontado pro-rata de {donors}."
    )
    return out, rationale, trace


def _enforce_reserve_floor(
    alloc: dict, risk_tolerance: str
) -> tuple[dict, list[str]]:
    """Aplica R3 de risk_rules.md: reserve >= floor del perfil.
    Si falta, se toma pro-rata de los direccionales."""
    out = dict(alloc)
    rationale: list[str] = []
    floor = _RESERVE_FLOOR.get(risk_tolerance, 10.0)
    if out.get("reserve", 0) < floor:
        deficit = floor - out["reserve"]
        directional = ["equity", "defi", "forex", "social"]
        donors = [v for v in directional if out.get(v, 0) > 0]
        if donors:
            total_donor = sum(out[v] for v in donors)
            for v in donors:
                out[v] -= deficit * (out[v] / total_donor)
            out["reserve"] = floor
            rationale.append(
                f"Reserve subida a {floor:.0f}% (piso R3 para perfil {risk_tolerance})."
            )
    return out, rationale


def _clamp_negatives(alloc: dict) -> dict:
    """Después de tantos ajustes, un vertical podría quedar en negativo.
    Lo saturamos a 0 (no se reinyecta — el renormalizado final lo corrige)."""
    return {k: max(0.0, v) for k, v in alloc.items()}


def _concentrate_small_capital(
    allocation_pct: dict, capital_usd: float, risk_tolerance: str, excluded: set
) -> tuple[dict, list[str], list[dict]]:
    """Capital <$200 + N verticales = slices <$50 = inviable por mínimos
    de venue (ver VENUE_MINIMUMS_USD). Consolidamos en el/los verticales
    con mayor peso hasta que cada slice restante sea >= _MIN_SLICE_USD.
    Reserve se mantiene al piso del perfil."""
    rationale: list[str] = []
    trace: list[dict] = []

    if capital_usd >= _SMALL_CAPITAL_THRESHOLD_USD:
        return allocation_pct, rationale, trace

    floor = _RESERVE_FLOOR.get(risk_tolerance, 10.0)
    directional = ["equity", "defi", "forex", "social"]
    # Pesos actuales en USD.
    slices_usd = {k: capital_usd * v / 100 for k, v in allocation_pct.items()}
    # Identificar slices direccionales inviables.
    weak = [
        v for v in directional
        if v not in excluded
        and allocation_pct.get(v, 0) > 0
        and slices_usd[v] < _MIN_SLICE_USD
    ]
    if not weak:
        return allocation_pct, rationale, trace

    # Estrategia: consolidar todos los slices débiles en el vertical
    # direccional viable más pesado. Si ninguno es viable, dejar solo
    # el de mayor peso + reserve.
    candidates = [
        v for v in directional
        if v not in excluded and allocation_pct.get(v, 0) > 0
    ]
    if not candidates:
        return allocation_pct, rationale, trace

    # Ordenar por peso descendente — el "dominante" recibe la consolidación.
    candidates.sort(key=lambda v: allocation_pct[v], reverse=True)
    dominant = candidates[0]

    out = dict(allocation_pct)
    absorbed = 0.0
    absorbed_from: list[str] = []
    for v in weak:
        if v == dominant:
            continue
        absorbed += out[v]
        absorbed_from.append(v)
        out[v] = 0.0
        trace.append({"source": "small_capital", "vertical": v, "delta_pp": -allocation_pct[v]})

    if absorbed > 0:
        out[dominant] += absorbed
        trace.append({"source": "small_capital", "vertical": dominant, "delta_pp": absorbed})
        rationale.append(
            f"Capital ${capital_usd:.0f} < ${_SMALL_CAPITAL_THRESHOLD_USD:.0f}: "
            f"verticales {absorbed_from} tenían slices < ${_MIN_SLICE_USD:.0f} "
            f"(inviables por mínimos de venue); consolidados en '{dominant}'."
        )

    # Verificar que el dominant ahora sea viable. Si no, ampliar reserve.
    if capital_usd * out[dominant] / 100 < _MIN_SLICE_USD:
        # Caso extremo: ni consolidado llega al mínimo → todo a reserve.
        moved = out[dominant]
        out["reserve"] = out.get("reserve", 0) + moved
        out[dominant] = 0.0
        rationale.append(
            f"Ni consolidado el vertical '{dominant}' alcanza ${_MIN_SLICE_USD:.0f}; "
            f"capital redirigido a reserve (stablecoin lending) hasta acumular más."
        )
        trace.append({"source": "small_capital", "vertical": dominant, "delta_pp": -moved})
        trace.append({"source": "small_capital", "vertical": "reserve", "delta_pp": +moved})
    elif out.get("reserve", 0) < floor:
        # Respetar piso de reserve también en este régimen.
        deficit = floor - out["reserve"]
        out[dominant] -= deficit
        out["reserve"] = floor
        trace.append({"source": "small_capital_reserve_floor", "vertical": dominant, "delta_pp": -deficit})

    return out, rationale, trace


@mcp.tool()
def allocate_portfolio(
    capital_usd: float,
    monthly_savings_usd: float,
    risk_tolerance: str,
    horizon: str,
    exclude_verticals: list[str] | None = None,
    macro_context: dict | None = None,
    user_age: int | None = None,
    horizon_months: float | None = None,
    preferred_verticals: list[str] | None = None,
) -> dict:
    """
    Genera la asignación de portafolio por vertical DE FORMA DINÁMICA.

    En vez de elegir una plantilla fija por risk_tolerance, usa la plantilla
    como ancla y aplica ajustes incrementales (en pp) por contexto macro,
    horizonte, edad y preferencias del usuario. Los ajustes están capeados
    para no violar risk_rules.md (R2 50% por vertical, R3 reserve mínimo).

    Args:
        capital_usd: Capital total en USD.
        monthly_savings_usd: Ahorro mensual en USD (reservado para futura
            proyección 12m; actualmente no modifica la asignación).
        risk_tolerance: "conservative" | "moderate" | "aggressive" | "mixed".
            Define el template ANCLA, no el resultado final.
        horizon: "short" | "medium" | "long" | "combined". Se usa como
            fallback si horizon_months no se provee. Preferir horizon_months.
        exclude_verticals: Verticales a excluir del plan. Su peso se
            redistribuye entre los direccionales restantes.
        macro_context: dict opcional del market_intelligence_skill. Claves
            soportadas (todas opcionales):
              - rsi_spy (float): RSI(14) de SPY. <30 → +5pp equity; >70 → -5pp equity.
              - rsi_qqq (float): RSI(14) de QQQ. <30 → +3pp equity; >70 → -3pp equity.
              - tvl_trend ("up"|"down"|"flat" o número): tendencia TVL DeFi 30d.
                "up" o >+10% → +4pp defi; "down" o <-10% → -4pp defi.
              - btc_dominance (float 0-100): >60 → -3pp defi; <45 → +3pp defi.
        user_age: Edad del usuario. Reservado para regla "120 - edad =
            % equity sugerido" (no implementada aún en v8; se documenta
            en rationale si se provee).
        horizon_months: Horizonte numérico en meses. <12 → reduce equity
            y sube reserve; >=36 → sube equity. Tiene prioridad sobre `horizon`.
        preferred_verticals: Lista opcional de verticales que el usuario
            quiere sobreponderar. +3pp a cada preferido, descontado
            pro-rata de los direccionales no preferidos.

    Returns:
        dict con:
          - allocation_pct: {vertical: % del portafolio}
          - allocation_usd: {vertical: USD asignados}
          - rationale: list[str] legible con cada ajuste aplicado
          - adjustments_applied: list[dict] trazabilidad estructurada
          - base_template: nombre del template ancla usado
          - effective_horizon_months: horizonte numérico resuelto
    """
    excluded = set(exclude_verticals or [])
    rationale: list[str] = []
    trace: list[dict] = []

    # ---- Normalización de inputs ----
    risk_tolerance = risk_tolerance if risk_tolerance in ALLOCATION_TEMPLATES else "moderate"
    if horizon_months is None or horizon_months <= 0:
        horizon_months = float(_HORIZON_STRING_TO_MONTHS.get(horizon, 24))
        rationale.append(
            f"Horizonte numérico no provisto: usando fallback de horizon='{horizon}' "
            f"→ {horizon_months:.0f}m."
        )

    # ---- Paso 0: template ancla ----
    alloc = dict(ALLOCATION_TEMPLATES[risk_tolerance])
    rationale.append(
        f"Template ancla '{risk_tolerance}': "
        + ", ".join(f"{k}={v}%" for k, v in alloc.items()) + "."
    )

    # ---- Paso 1: exclusiones del usuario ----
    if excluded:
        directional = ["equity", "defi", "forex", "social"]
        alloc = _redistribute_excluded(alloc, excluded, directional)
        rationale.append(
            f"Verticales excluidos {sorted(excluded)}: peso redistribuido "
            f"a los direccionales restantes."
        )

    # ---- Paso 2: ajustes macro ----
    alloc_pre_macro = dict(alloc)
    alloc, macro_rationale, macro_trace = _apply_macro_adjustments(
        alloc, macro_context or {}, excluded
    )
    rationale.extend(macro_rationale)
    trace.extend(macro_trace)

    # ---- Paso 3: ajuste por horizonte numérico ----
    alloc, horizon_rationale, horizon_trace = _apply_horizon_adjustment(
        alloc, horizon_months, excluded
    )
    rationale.extend(horizon_rationale)
    trace.extend(horizon_trace)

    # ---- Paso 3b: nota informativa por edad (no altera pesos en v8) ----
    if user_age is not None and user_age > 0:
        equity_guideline = max(10, min(90, 120 - user_age))
        rationale.append(
            f"Edad={user_age}: regla 120-edad sugiere ~{equity_guideline}% en "
            f"equity como referencia (no se aplicó ajuste automático en v8; "
            f"revisar manualmente si diverge mucho del resultado)."
        )

    # ---- Paso 4: preferencias del usuario ----
    alloc, pref_rationale, pref_trace = _apply_preferences(
        alloc, preferred_verticals or [], excluded
    )
    rationale.extend(pref_rationale)
    trace.extend(pref_trace)

    # ---- Paso 5: saturar negativos y aplicar piso de reserve ----
    alloc = _clamp_negatives(alloc)
    alloc, reserve_rationale = _enforce_reserve_floor(alloc, risk_tolerance)
    rationale.extend(reserve_rationale)

    # ---- Paso 6: renormalizar a 100% ----
    total_pct = sum(alloc.values())
    if total_pct <= 0:
        # Degenerado: todo se canceló → fallback al template ancla.
        alloc = dict(ALLOCATION_TEMPLATES[risk_tolerance])
        total_pct = sum(alloc.values())
        rationale.append("Ajustes saturaron a 0; fallback al template ancla.")
    allocation_pct = {k: round(v / total_pct * 100, 1) for k, v in alloc.items()}

    # ---- Paso 7: concentración por capital pequeño ----
    allocation_pct, small_rationale, small_trace = _concentrate_small_capital(
        allocation_pct, capital_usd, risk_tolerance, excluded
    )
    rationale.extend(small_rationale)
    trace.extend(small_trace)
    # Renormalizar por si la consolidación dejó totales != 100 por redondeo.
    tp = sum(allocation_pct.values())
    if tp > 0:
        allocation_pct = {k: round(v / tp * 100, 1) for k, v in allocation_pct.items()}

    allocation_usd = {
        k: round(capital_usd * v / 100, 2) for k, v in allocation_pct.items()
    }

    return {
        "allocation_pct": allocation_pct,
        "allocation_usd": allocation_usd,
        "rationale": rationale,
        "adjustments_applied": trace,
        "base_template": risk_tolerance,
        "effective_horizon_months": horizon_months,
    }


# ============================================================
# VALIDATE_ALLOCATION_MINIMUMS — checkpoint determinística
# ============================================================
# Convierte el §4 de platforms_skill.md (prosa aspiracional) en una
# tool que el agente debe llamar SIEMPRE después de allocate_portfolio
# y ANTES del gate de search_instruments. Evita que el plan proponga
# posiciones imposibles de ejecutar (ej: copy_trader $50 con min $200).

@mcp.tool()
def validate_allocation_minimums(
    allocation_usd: dict,
    venue_map: dict,
) -> dict:
    """
    Valida que cada posición propuesta cumpla el mínimo del venue/producto.

    Recibe la asignación por vertical de `allocate_portfolio` y un mapa
    que detalla, por vertical, el venue + tipo de producto + cuántas
    posiciones se van a abrir en ese vertical. Devuelve:
      (a) lista de violaciones con el motivo exacto,
      (b) sugerencia concreta por cada violación (consolidar / cambiar
          venue / eliminar),
      (c) una allocation ajustada que SÍ respeta los mínimos (reasignando
          el capital de posiciones imposibles al reserve).

    Esto convierte el chequeo de mínimos en un gate determinístico
    (una tool que devuelve estructura), no en una regla aspiracional
    que el agente podría saltarse por olvido.

    Args:
        allocation_usd: output `allocation_usd` de allocate_portfolio,
            ej. {"equity": 400, "defi": 250, "forex": 100, "social": 150, "reserve": 100}
        venue_map: plan de ejecución por vertical. Cada vertical mapea a
            uno o más "buckets" de posiciones. Formato:
            {
              "equity": [
                {"venue": "eToro", "product_type": "stock_spot",
                 "num_positions": 3, "weight_within_vertical": 1.0}
              ],
              "defi": [
                {"venue": "Binance", "product_type": "spot_crypto",
                 "num_positions": 2, "weight_within_vertical": 0.6},
                {"venue": "Aave",    "product_type": "supply",
                 "num_positions": 1, "weight_within_vertical": 0.4}
              ],
              "social": [
                {"venue": "eToro", "product_type": "copy_trader",
                 "num_positions": 1, "weight_within_vertical": 1.0}
              ],
              "reserve": [
                {"venue": "Binance", "product_type": "simple_earn",
                 "num_positions": 1, "weight_within_vertical": 1.0}
              ]
            }
            - weight_within_vertical: fracción (0..1) del capital del
              vertical que va a ese bucket. Los pesos de un vertical
              deben sumar ~1.0; si no, la tool normaliza y avisa.
            - num_positions: número de posiciones dentro del bucket
              (el capital del bucket se divide equi-ponderado entre
              ellas para el check de mínimo, que es lo que define si
              una posición es ejecutable).
    """

    violations = []
    suggestions = []
    adjusted_allocation = {k: round(v, 2) for k, v in allocation_usd.items()}
    normalization_warnings = []
    unknown_venues = []

    # Itera cada vertical y sus buckets
    for vertical, capital_vertical in allocation_usd.items():
        if capital_vertical <= 0:
            continue

        buckets = venue_map.get(vertical, [])
        if not buckets:
            # vertical con capital pero sin plan de venue → no validable
            # (no es violación per se; es un gap de información)
            continue

        # Normalizar weight_within_vertical si no suma 1.0
        total_weight = sum(b.get("weight_within_vertical", 0) for b in buckets)
        if total_weight <= 0:
            # Fallback: distribución igualitaria
            normalized_weights = [1.0 / len(buckets)] * len(buckets)
            normalization_warnings.append(
                f"Vertical '{vertical}': los weight_within_vertical suman 0, se asume distribución igualitaria"
            )
        elif abs(total_weight - 1.0) > 0.01:
            normalized_weights = [
                b.get("weight_within_vertical", 0) / total_weight for b in buckets
            ]
            normalization_warnings.append(
                f"Vertical '{vertical}': los weight_within_vertical suman {total_weight:.2f}, normalizados a 1.0"
            )
        else:
            normalized_weights = [b.get("weight_within_vertical", 0) for b in buckets]

        # Validar cada bucket
        for bucket, w in zip(buckets, normalized_weights):
            venue = bucket.get("venue", "")
            product_type = bucket.get("product_type", "")
            num_positions = max(int(bucket.get("num_positions", 1)), 1)

            capital_bucket = capital_vertical * w
            capital_per_position = capital_bucket / num_positions

            # Lookup del mínimo
            venue_mins = VENUE_MINIMUMS_USD.get(venue)
            if venue_mins is None:
                unknown_venues.append(venue)
                violations.append({
                    "vertical": vertical,
                    "venue": venue,
                    "product_type": product_type,
                    "num_positions": num_positions,
                    "capital_per_position_usd": round(capital_per_position, 2),
                    "minimum_required_usd": None,
                    "reason": f"Venue '{venue}' no está en la tabla de mínimos conocidos",
                })
                suggestions.append({
                    "vertical": vertical,
                    "venue": venue,
                    "action": "verify_venue",
                    "detail": f"Añadir '{venue}' a VENUE_MINIMUMS_USD o confirmar venue canónico (eToro / Binance / Capital.com / Aave / Lido / Ethena)",
                })
                continue

            minimum = venue_mins.get(product_type)
            if minimum is None:
                violations.append({
                    "vertical": vertical,
                    "venue": venue,
                    "product_type": product_type,
                    "num_positions": num_positions,
                    "capital_per_position_usd": round(capital_per_position, 2),
                    "minimum_required_usd": None,
                    "reason": f"product_type '{product_type}' no existe para venue '{venue}'. Tipos válidos: {sorted(venue_mins.keys())}",
                })
                suggestions.append({
                    "vertical": vertical,
                    "venue": venue,
                    "action": "fix_product_type",
                    "detail": f"Revisar product_type; opciones en {venue}: {sorted(venue_mins.keys())}",
                })
                continue

            # Check de mínimo
            if capital_per_position < minimum:
                gap = minimum - capital_per_position
                required_bucket_capital = minimum * num_positions

                # Sugerencia de consolidación: cuántas posiciones caben
                # con el capital del bucket respetando el mínimo
                max_positions_possible = int(capital_bucket // minimum)

                violations.append({
                    "vertical": vertical,
                    "venue": venue,
                    "product_type": product_type,
                    "num_positions": num_positions,
                    "capital_bucket_usd": round(capital_bucket, 2),
                    "capital_per_position_usd": round(capital_per_position, 2),
                    "minimum_required_usd": minimum,
                    "gap_usd": round(gap, 2),
                    "reason": (
                        f"Posición de ${capital_per_position:.2f} en {venue}/{product_type} "
                        f"< mínimo ${minimum:.2f}. Faltan ${gap:.2f} por posición."
                    ),
                })

                # Rama 1: aún puede abrir ≥1 posición si consolida
                if max_positions_possible >= 1:
                    suggestions.append({
                        "vertical": vertical,
                        "venue": venue,
                        "product_type": product_type,
                        "action": "consolidate",
                        "from_positions": num_positions,
                        "to_positions": max_positions_possible,
                        "detail": (
                            f"Reducir a {max_positions_possible} posición(es) de "
                            f"${capital_bucket / max_positions_possible:.2f} cada una "
                            f"(en lugar de {num_positions} × ${capital_per_position:.2f}). "
                            f"Cumple el mínimo de ${minimum:.2f}."
                        ),
                    })
                # Rama 2: ni consolidando cabe → cambiar de venue o eliminar
                else:
                    # Buscar un venue alternativo con el mínimo más bajo para
                    # un product_type "equivalente" en mismo dominio
                    alternative = _find_cheaper_alternative(
                        vertical=vertical,
                        product_type=product_type,
                        capital_bucket=capital_bucket,
                        current_venue=venue,
                    )
                    if alternative is not None:
                        suggestions.append({
                            "vertical": vertical,
                            "venue": venue,
                            "product_type": product_type,
                            "action": "switch_venue",
                            "to_venue": alternative["venue"],
                            "to_product_type": alternative["product_type"],
                            "to_minimum_usd": alternative["minimum"],
                            "detail": (
                                f"El bucket tiene ${capital_bucket:.2f} pero ni siquiera una "
                                f"posición cabe con mínimo ${minimum:.2f} en {venue}/{product_type}. "
                                f"Mover a {alternative['venue']}/{alternative['product_type']} "
                                f"(mínimo ${alternative['minimum']:.2f})."
                            ),
                        })
                    else:
                        suggestions.append({
                            "vertical": vertical,
                            "venue": venue,
                            "product_type": product_type,
                            "action": "drop_and_redistribute",
                            "detail": (
                                f"Capital insuficiente (${capital_bucket:.2f}) para cualquier "
                                f"posición {product_type} en {venue} ni en venues alternativos. "
                                f"Eliminar este bucket y sumar los ${capital_bucket:.2f} a 'reserve' "
                                f"o a otro vertical que sí cumpla mínimos."
                            ),
                        })
                        # Aplicar el ajuste propuesto al allocation_usd "adjusted"
                        adjusted_allocation[vertical] = max(
                            adjusted_allocation.get(vertical, 0) - capital_bucket, 0
                        )
                        adjusted_allocation["reserve"] = (
                            adjusted_allocation.get("reserve", 0) + capital_bucket
                        )

    # Redondeo final de la allocation ajustada
    adjusted_allocation = {k: round(v, 2) for k, v in adjusted_allocation.items()}

    is_valid = len(violations) == 0

    return {
        "is_valid": is_valid,
        "violations": violations,
        "suggestions": suggestions,
        "adjusted_allocation_usd": adjusted_allocation,
        "allocation_changed": adjusted_allocation != {k: round(v, 2) for k, v in allocation_usd.items()},
        "normalization_warnings": normalization_warnings,
        "unknown_venues": list(set(unknown_venues)),
        "summary": (
            "OK: todas las posiciones cumplen el mínimo del venue"
            if is_valid
            else f"{len(violations)} violación(es) de mínimo detectada(s). "
                 f"Revisar 'suggestions' y aplicar 'adjusted_allocation_usd' antes de presentar el plan."
        ),
    }


def _find_cheaper_alternative(
    vertical: str, product_type: str, capital_bucket: float, current_venue: str,
) -> dict | None:
    """
    Busca un venue alternativo donde el mismo 'espíritu' de posición quepa.
    Regla simple basada en dominio (no sustituye al árbol de decisión del
    §3 de platforms_skill.md, solo sugiere cuándo el capital es el bloqueo).
    """
    # Mapeo de equivalencias por dominio de producto
    equivalences = {
        # crypto spot: eToro ↔ Binance
        "crypto_spot":    [("Binance", "spot_crypto")],
        "spot_crypto":    [("eToro",   "crypto_spot")],
        # cfd forex: eToro ↔ Capital.com
        "cfd_forex":      [("Capital.com", "cfd_forex"), ("eToro", "cfd_forex")],
        "cfd_commodity":  [("Capital.com", "cfd_commodity"), ("eToro", "cfd_commodity")],
        "cfd_index":      [("Capital.com", "cfd_index"), ("eToro", "cfd_index")],
        # copy trader: eToro ↔ Binance (copy_trading de Binance es más barato pero universo distinto)
        "copy_trader":    [("Binance", "copy_trading")],
        # DeFi supply: Aave mainnet es caro; no hay equivalencia directa barata en este stack
    }

    for alt_venue, alt_product in equivalences.get(product_type, []):
        if alt_venue == current_venue:
            continue
        alt_min = VENUE_MINIMUMS_USD.get(alt_venue, {}).get(alt_product)
        if alt_min is not None and capital_bucket >= alt_min:
            return {"venue": alt_venue, "product_type": alt_product, "minimum": alt_min}
    return None


# ============================================================
# SCENARIOS — v5 (con dividend_withholding_pct y funding_rate_daily_pct)
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
    dividend_withholding_pct: float = 0.0,
    funding_rate_daily_pct: float = 0.0,
) -> dict:
    """
    Calcula 3 escenarios (optimista, base, pesimista) para una posicion de inversion.

    Args:
        amount_usd: Monto invertido (capital propio en USD).
        expected_apy: Rendimiento anual esperado del activo subyacente
            (ej: 0.10 = 10%). Aplica al precio, no incluye ingreso pasivo.
        volatility_annual: Volatilidad anualizada del activo (ej: 0.15 = 15%).
        passive_income_annual_usd: Ingreso pasivo anual BRUTO en USD
            (dividendos antes de retención, rewards de staking, intereses
            de Simple Earn). El neto efectivo se calcula aplicando
            dividend_withholding_pct.
        months: Horizonte en meses.
        leverage: Apalancamiento (1.0 = spot, 2.0 = CFD 2x, etc.). El
            notional expuesto es amount_usd * leverage.
        monthly_cost_usd: Costo mensual fijo en USD (ej: overnight fees de
            CFDs, fees por inactividad). Se resta lineal del resultado.
        dividend_withholding_pct: Fracción de retención en origen sobre
            passive_income_annual_usd (ej: 0.30 para acciones US que pagan
            dividendos a residentes no-US sin tratado, tal como indica
            platforms_skill §1.5). Default 0.0 (sin retención) para que
            no altere a posiciones que no son dividend-paying (cripto
            staking, APY de Simple Earn, intereses DeFi, etc.).
            Rango válido: [0.0, 1.0].
        funding_rate_daily_pct: Funding rate PROMEDIO diario para futures
            perpetuos (ej: Binance USDⓈ-M), expresado como fracción
            (ej: 0.0003 = 0.03%/día ≈ 11%/año sobre notional). Convención:
            valor POSITIVO = costo para el LONG (paga a los shorts);
            valor NEGATIVO = ingreso para el long. Se aplica sobre el
            notional apalancado (amount_usd * leverage), NO sobre el
            margen. platforms_skill §2.6 documenta que el rango típico es
            -0.3% a +0.3% diario. Default 0.0 (ignorado) para que no
            afecte a posiciones spot / CFDs eToro / DeFi passive.

    Convenciones:
        * passive_income_annual_usd se prorratea por months/12 y luego se
          aplica la retención: passive_neto = passive_bruto * factor
          * (1 - dividend_withholding_pct).
        * funding_cost = notional * funding_rate_daily_pct * días.
          Si el rate es +, el costo es positivo (reduce retorno).
          Si el rate es -, el costo es negativo (suma al retorno).
        * Los costos (monthly_cost_usd, funding) NO se multiplican por
          leverage aquí porque se asume que el agente ya los pasa
          calculados sobre el notional correspondiente (el caso de
          overnight fees eToro en equity_skill), EXCEPTO el funding, que
          SÍ se multiplica automáticamente por leverage porque su
          definición de mercado es sobre el notional.
    """
    # Validaciones defensivas (no lanzan excepción, recortan a rangos sanos)
    if dividend_withholding_pct < 0:
        dividend_withholding_pct = 0.0
    if dividend_withholding_pct > 1:
        dividend_withholding_pct = 1.0

    factor = months / 12.0
    days = months * 30  # convención consistente con monthly_cost_usd

    # Ingreso pasivo neto de retención en origen
    passive_gross = passive_income_annual_usd * factor
    passive_net = passive_gross * (1.0 - dividend_withholding_pct)
    withholding_deducted = passive_gross - passive_net

    # Costos fijos mensuales (overnight CFD, inactividad)
    total_monthly_costs = monthly_cost_usd * months

    # Funding rate sobre notional apalancado. Positivo = costo.
    # Nota: el signo del total es el mismo que el del rate; si rate > 0
    # incrementa total_costs (resta al retorno); si rate < 0 lo reduce
    # (suma al retorno).
    notional = amount_usd * leverage
    total_funding_cost = notional * funding_rate_daily_pct * days

    # Total de costos (puede ser negativo si el funding neto es ingreso)
    total_costs = total_monthly_costs + total_funding_cost

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
        total = price_impact + passive_net - total_costs
        scenarios.append({
            "name": name,
            "probability_pct": prob,
            "asset_change_pct": round(change_base * 100, 1),
            "leveraged_change_pct": round(change * 100, 1),
            "price_impact_usd": round(price_impact, 2),
            "passive_income_gross_usd": round(passive_gross, 2),
            "passive_income_net_usd": round(passive_net, 2),
            "withholding_deducted_usd": round(withholding_deducted, 2),
            "monthly_costs_usd": round(total_monthly_costs, 2),
            "funding_cost_usd": round(total_funding_cost, 2),
            "costs_usd": round(total_costs, 2),
            "total_return_usd": round(total, 2),
            "total_return_pct": round(total / amount_usd * 100, 1) if amount_usd > 0 else 0,
            "portfolio_value": round(max(amount_usd + total, 0), 2),
            "liquidated": change <= -1.0,
        })

    # Advertencias para que el agente no pase valores absurdos sin darse cuenta
    warnings = []
    if funding_rate_daily_pct != 0.0 and leverage <= 1.0:
        warnings.append(
            "funding_rate_daily_pct != 0 con leverage=1.0: el funding rate solo "
            "aplica a futures perpetuos (leverage > 1). Revisar si la posición "
            "es realmente de futures."
        )
    if abs(funding_rate_daily_pct) > 0.003:
        warnings.append(
            f"funding_rate_daily_pct={funding_rate_daily_pct:.4f} fuera del rango "
            f"típico [-0.003, +0.003] documentado en platforms_skill §2.6. "
            f"Verificar que sea un rate diario (no anual ni por 8h)."
        )
    if dividend_withholding_pct > 0 and passive_income_annual_usd <= 0:
        warnings.append(
            "dividend_withholding_pct > 0 pero passive_income_annual_usd = 0: "
            "la retención no tiene efecto. ¿Se olvidó pasar el dividendo bruto?"
        )

    return {
        "amount_usd": amount_usd,
        "leverage": leverage,
        "effective_exposure": round(notional, 2),
        "monthly_cost_usd": monthly_cost_usd,
        "total_monthly_costs_over_period": round(total_monthly_costs, 2),
        "dividend_withholding_pct": dividend_withholding_pct,
        "passive_income_gross_over_period": round(passive_gross, 2),
        "passive_income_net_over_period": round(passive_net, 2),
        "withholding_deducted_over_period": round(withholding_deducted, 2),
        "funding_rate_daily_pct": funding_rate_daily_pct,
        "funding_cost_over_period": round(total_funding_cost, 2),
        "horizon_months": months,
        "scenarios": scenarios,
        "warnings": warnings,
    }


# ============================================================
# TRACKING — v6 (Fix 5)
# compare_portfolio_to_baseline
#
# Objetivo: convertir la aritmética del tracking_skill.md (§Fase C
# cálculos y §Fase D alertas semáforo) en una tool determinística.
# Antes el agente estimaba P&L, desviaciones de peso, P&L total y
# clasificación semáforo en prompting. En un portafolio con 5+
# posiciones eso es propenso a errores de redondeo y de arrastre
# (ej. un peso mal calculado desplaza todos los demás).
#
# Esta tool NO toma decisiones de qué hacer (eso es del skill, que
# cruza con risk_rules.md y platforms_skill.md). Solo entrega los
# números crudos + la clasificación semáforo por umbral.
# ============================================================

# Umbrales de Fase D del tracking_skill.md. Single source of truth:
# si cambia un umbral en el skill, se cambia AQUÍ y queda reflejado
# en la clasificación. Idéntico patrón al de VENUE_MINIMUMS_USD.
_TRACKING_THRESHOLDS = {
    # P&L por posición (porcentual, negativo = pérdida)
    "pnl_pct_critical": -0.15,   # 🔴 pérdida > 15%
    "pnl_pct_warning":  -0.05,   # 🟡 pérdida entre 5% y 15%
    # Desviación de peso absoluta en puntos porcentuales
    "weight_dev_critical_pp": 15.0,  # 🔴 desviación > 15 p.p.
    "weight_dev_warning_pp":   5.0,  # 🟡 desviación entre 5 y 15 p.p.
}


@mcp.tool()
def compare_portfolio_to_baseline(
    baseline: dict,
    current_positions: list[dict],
) -> dict:
    """
    Compara el estado ACTUAL del portafolio contra el baseline del plan
    original y devuelve P&L, desviaciones de peso, posiciones
    nuevas/cerradas y alertas semáforo según los umbrales de
    tracking_skill.md §Fase D.

    Esta es la checkpoint determinística del tracking. El agente solo
    debe llamar esta tool y PRESENTAR el resultado. No recalcular nada
    en prompting — eso vuelve a violar el principio #1 de system.md.

    Args:
        baseline: bloque `BASELINE DE SEGUIMIENTO` parseado. Debe seguir
            el schema de tracking_skill.md. Campos usados por esta tool:
              - user_profile.capital_usd (float): capital total del plan.
              - positions[]: cada posición con al menos
                  ticker (str), weight_target_pct (float),
                  entry_price (float), capital_assigned_usd (float).
                Opcional pero útil: venue (str), leverage (float).
            El resto de campos del baseline (tesis, catalyst, SL/TP,
            risk_score, portfolio_level, schedule) no se tocan aquí —
            viven en prompting porque son cualitativos.

        current_positions: lista de posiciones vivas hoy. Cada dict:
              - ticker (str): obligatorio, se usa para matchear contra
                baseline.positions[].ticker (case-insensitive).
              - quantity (float): cantidad actual.
              - current_price (float): precio de mercado actual.
              - current_value_usd (float, opcional): valor actual de la
                posición. Si no viene, se calcula como
                quantity * current_price. Útil cuando la fuente ya lo
                da (ej. etoro-server.get_portfolio lo expone).
              - unrealized_pnl_usd (float, opcional): si la plataforma
                ya calcula el P&L (eToro lo hace), se usa ese valor
                para el P&L absoluto y se recalcula solo el porcentual
                vs entry_price. Si no viene, se calcula todo.
              - venue (str, opcional): para trazabilidad.

    Returns:
        dict con:
          - summary: P&L total del portafolio (abs, %), valor actual
            total, capital inicial, conteo de alertas.
          - positions: lista por posición con peso actual, peso
            objetivo, desviación en p.p., P&L abs y %, status semáforo,
            motivo del status.
          - new_positions: posiciones que están hoy pero no en el
            baseline (marcadas "fuera de plan").
          - closed_positions: posiciones del baseline que ya no están
            hoy (el agente debe preguntar al usuario el motivo y el
            P&L realizado — la tool no lo puede saber).
          - alerts: lista de alertas semáforo consolidadas, ordenadas
            por severidad (🔴 primero).
          - warnings: lista de problemas de data (campos faltantes,
            pesos objetivo que no suman 100, etc.).
    """

    warnings: list[str] = []

    # ─────────────────────────────────────────────────────────
    # 1. Validar y extraer del baseline
    # ─────────────────────────────────────────────────────────
    user_profile = baseline.get("user_profile") or {}
    capital_initial = float(user_profile.get("capital_usd") or 0.0)
    baseline_positions = baseline.get("positions") or []

    if capital_initial <= 0:
        warnings.append(
            "baseline.user_profile.capital_usd no está o es 0: no se puede "
            "calcular P&L total del portafolio en %. Se reporta solo en USD."
        )

    if not baseline_positions:
        warnings.append(
            "baseline.positions está vacío: no hay nada contra qué comparar. "
            "¿El baseline se parseó bien?"
        )

    # Indexar baseline por ticker (normalizado) para matching eficiente
    baseline_by_ticker: dict[str, dict] = {}
    weight_target_sum = 0.0
    for p in baseline_positions:
        tkr = str(p.get("ticker") or "").strip().upper()
        if not tkr:
            warnings.append("Posición del baseline sin ticker: se omite.")
            continue
        baseline_by_ticker[tkr] = p
        weight_target_sum += float(p.get("weight_target_pct") or 0.0)

    if baseline_positions and abs(weight_target_sum - 100.0) > 1.0:
        warnings.append(
            f"Los weight_target_pct del baseline suman {weight_target_sum:.1f}% "
            f"(esperado ~100%). Las desviaciones de peso pueden estar sesgadas."
        )

    # ─────────────────────────────────────────────────────────
    # 2. Calcular valor total actual del portafolio
    #    (necesario ANTES de calcular pesos actuales)
    # ─────────────────────────────────────────────────────────
    current_by_ticker: dict[str, dict] = {}
    total_value_current = 0.0

    for cp in current_positions:
        tkr = str(cp.get("ticker") or "").strip().upper()
        if not tkr:
            warnings.append("Posición actual sin ticker: se omite.")
            continue

        quantity = float(cp.get("quantity") or 0.0)
        current_price = float(cp.get("current_price") or 0.0)

        # current_value_usd es preferible si viene (la plataforma ya lo
        # calculó con datos que la tool no tiene: fees, ajustes, etc.)
        if cp.get("current_value_usd") is not None:
            value = float(cp["current_value_usd"])
        elif quantity > 0 and current_price > 0:
            value = quantity * current_price
        else:
            value = 0.0
            warnings.append(
                f"{tkr}: sin current_value_usd y sin quantity*current_price "
                f"válidos. Se asume valor 0 (P&L no se puede calcular bien)."
            )

        current_by_ticker[tkr] = {
            "ticker": tkr,
            "quantity": quantity,
            "current_price": current_price,
            "current_value_usd": value,
            "unrealized_pnl_usd": cp.get("unrealized_pnl_usd"),
            "venue": cp.get("venue"),
        }
        total_value_current += value

    # ─────────────────────────────────────────────────────────
    # 3. Posición por posición: match baseline ↔ actual
    # ─────────────────────────────────────────────────────────
    positions_report: list[dict] = []
    alerts: list[dict] = []

    for tkr, bp in baseline_by_ticker.items():
        weight_target_pct = float(bp.get("weight_target_pct") or 0.0)
        entry_price = float(bp.get("entry_price") or 0.0)
        capital_assigned = float(bp.get("capital_assigned_usd") or 0.0)
        leverage = float(bp.get("leverage") or 1.0)
        venue_baseline = bp.get("venue")

        cp = current_by_ticker.get(tkr)
        if cp is None:
            # Ya se reportará en closed_positions; no es una fila aquí.
            continue

        quantity = cp["quantity"]
        current_price = cp["current_price"]
        current_value = cp["current_value_usd"]

        # ── P&L absoluto ──
        # Preferimos el unrealized_pnl_usd de la plataforma si viene
        # (ver tracking_skill §Fase C: "Para posiciones en eToro, usar
        # el unrealizedPnL que ya devuelve get_portfolio — no recalcular").
        pnl_abs_source = "platform"
        if cp["unrealized_pnl_usd"] is not None:
            pnl_abs = float(cp["unrealized_pnl_usd"])
        else:
            pnl_abs_source = "computed"
            if entry_price > 0 and quantity > 0 and current_price > 0:
                pnl_abs = quantity * (current_price - entry_price)
            else:
                pnl_abs = 0.0
                warnings.append(
                    f"{tkr}: falta entry_price, quantity o current_price "
                    f"para calcular P&L absoluto. Se reporta 0."
                )

        # ── P&L porcentual ──
        # Siempre vs entry_price del baseline (fuente de verdad del plan).
        if entry_price > 0 and current_price > 0:
            pnl_pct = (current_price / entry_price) - 1.0
        elif capital_assigned > 0:
            # Fallback: pnl_pct ≈ pnl_abs / capital_assigned.
            # Menos preciso (ignora leverage, funding, dividendos) pero
            # mejor que no reportar nada. Se avisa.
            pnl_pct = pnl_abs / capital_assigned
            warnings.append(
                f"{tkr}: sin entry_price; P&L % estimado como "
                f"pnl_abs / capital_assigned. Menos preciso."
            )
        else:
            pnl_pct = 0.0
            warnings.append(
                f"{tkr}: no se puede calcular P&L % (falta entry_price y "
                f"capital_assigned_usd). Se reporta 0."
            )

        # ── Peso actual y desviación ──
        if total_value_current > 0:
            weight_current_pct = (current_value / total_value_current) * 100.0
        else:
            weight_current_pct = 0.0

        weight_dev_pp = weight_current_pct - weight_target_pct

        # ── Clasificación semáforo ──
        # Se evalúan ambas dimensiones (P&L y desviación de peso) y se
        # queda con la peor. Umbrales desde _TRACKING_THRESHOLDS.
        status = "🟢"
        reasons: list[str] = []

        if pnl_pct <= _TRACKING_THRESHOLDS["pnl_pct_critical"]:
            status = "🔴"
            reasons.append(
                f"pérdida {pnl_pct * 100:.1f}% > umbral crítico "
                f"{_TRACKING_THRESHOLDS['pnl_pct_critical'] * 100:.0f}%"
            )
        elif pnl_pct <= _TRACKING_THRESHOLDS["pnl_pct_warning"]:
            status = "🟡"
            reasons.append(
                f"pérdida {pnl_pct * 100:.1f}% entre "
                f"{_TRACKING_THRESHOLDS['pnl_pct_warning'] * 100:.0f}% y "
                f"{_TRACKING_THRESHOLDS['pnl_pct_critical'] * 100:.0f}%"
            )

        if abs(weight_dev_pp) >= _TRACKING_THRESHOLDS["weight_dev_critical_pp"]:
            status = "🔴"  # mayor severidad, sobrescribe
            reasons.append(
                f"desviación de peso {weight_dev_pp:+.1f} p.p. > "
                f"{_TRACKING_THRESHOLDS['weight_dev_critical_pp']:.0f} p.p."
            )
        elif abs(weight_dev_pp) >= _TRACKING_THRESHOLDS["weight_dev_warning_pp"]:
            if status == "🟢":
                status = "🟡"
            reasons.append(
                f"desviación de peso {weight_dev_pp:+.1f} p.p. entre "
                f"{_TRACKING_THRESHOLDS['weight_dev_warning_pp']:.0f} y "
                f"{_TRACKING_THRESHOLDS['weight_dev_critical_pp']:.0f} p.p."
            )

        row = {
            "ticker": tkr,
            "venue": cp["venue"] or venue_baseline,
            "weight_current_pct": round(weight_current_pct, 2),
            "weight_target_pct": round(weight_target_pct, 2),
            "weight_deviation_pp": round(weight_dev_pp, 2),
            "entry_price": round(entry_price, 6) if entry_price else None,
            "current_price": round(current_price, 6) if current_price else None,
            "quantity": quantity,
            "current_value_usd": round(current_value, 2),
            "pnl_abs_usd": round(pnl_abs, 2),
            "pnl_pct": round(pnl_pct, 4),
            "pnl_abs_source": pnl_abs_source,  # "platform" o "computed"
            "leverage": leverage,
            "status": status,
            "status_reasons": reasons,
        }
        positions_report.append(row)

        # Cada posición no-🟢 genera una alerta consolidada
        if status != "🟢":
            alerts.append({
                "severity": status,
                "ticker": tkr,
                "reasons": reasons,
                "pnl_pct": round(pnl_pct, 4),
                "weight_deviation_pp": round(weight_dev_pp, 2),
            })

    # ─────────────────────────────────────────────────────────
    # 4. Nuevas y cerradas
    # ─────────────────────────────────────────────────────────
    baseline_tickers = set(baseline_by_ticker.keys())
    current_tickers = set(current_by_ticker.keys())

    new_positions = []
    for tkr in sorted(current_tickers - baseline_tickers):
        cp = current_by_ticker[tkr]
        weight_pct = (
            (cp["current_value_usd"] / total_value_current) * 100.0
            if total_value_current > 0 else 0.0
        )
        new_positions.append({
            "ticker": tkr,
            "venue": cp["venue"],
            "current_value_usd": round(cp["current_value_usd"], 2),
            "weight_current_pct": round(weight_pct, 2),
            "note": "fuera de plan: no estaba en el baseline original",
        })
        alerts.append({
            "severity": "🟡",
            "ticker": tkr,
            "reasons": ["posición nueva no prevista en el baseline"],
            "pnl_pct": None,
            "weight_deviation_pp": None,
        })

    closed_positions = []
    for tkr in sorted(baseline_tickers - current_tickers):
        bp = baseline_by_ticker[tkr]
        closed_positions.append({
            "ticker": tkr,
            "venue": bp.get("venue"),
            "weight_target_pct": float(bp.get("weight_target_pct") or 0.0),
            "capital_assigned_usd": float(bp.get("capital_assigned_usd") or 0.0),
            "entry_price": float(bp.get("entry_price") or 0.0),
            "note": (
                "estaba en el baseline pero no en posiciones actuales: "
                "preguntar al usuario motivo (SL, TP, cierre manual) y "
                "P&L realizado. La tool no puede saberlo."
            ),
        })
        alerts.append({
            "severity": "🟡",
            "ticker": tkr,
            "reasons": [
                "posición del baseline ya no está abierta: requiere "
                "confirmación de motivo y P&L realizado con el usuario"
            ],
            "pnl_pct": None,
            "weight_deviation_pp": None,
        })

    # ─────────────────────────────────────────────────────────
    # 5. Resumen de portafolio
    # ─────────────────────────────────────────────────────────
    # P&L total absoluto: suma de los P&L absolutos de posiciones
    # matcheadas (las "nuevas" no tienen entry_price en el baseline,
    # así que su P&L real no es calculable sin data adicional).
    pnl_total_abs = sum(r["pnl_abs_usd"] for r in positions_report)

    if capital_initial > 0:
        pnl_total_pct = pnl_total_abs / capital_initial
    else:
        pnl_total_pct = 0.0

    # Ordenar alertas: 🔴 primero, 🟡 después
    severity_order = {"🔴": 0, "🟡": 1, "🟢": 2}
    alerts.sort(key=lambda a: severity_order.get(a["severity"], 9))

    counts = {
        "red": sum(1 for a in alerts if a["severity"] == "🔴"),
        "yellow": sum(1 for a in alerts if a["severity"] == "🟡"),
        "green": sum(1 for r in positions_report if r["status"] == "🟢"),
    }

    summary = {
        "capital_initial_usd": round(capital_initial, 2),
        "total_value_current_usd": round(total_value_current, 2),
        "pnl_total_abs_usd": round(pnl_total_abs, 2),
        "pnl_total_pct": round(pnl_total_pct, 4),
        "positions_in_baseline": len(baseline_by_ticker),
        "positions_current": len(current_by_ticker),
        "positions_matched": len(positions_report),
        "positions_new": len(new_positions),
        "positions_closed": len(closed_positions),
        "alert_counts": counts,
    }

    return {
        "summary": summary,
        "positions": positions_report,
        "new_positions": new_positions,
        "closed_positions": closed_positions,
        "alerts": alerts,
        "thresholds_used": _TRACKING_THRESHOLDS,
        "warnings": warnings,
    }


if __name__ == "__main__":
    mcp.run()
