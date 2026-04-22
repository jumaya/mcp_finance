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
