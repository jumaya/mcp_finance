"""
MCP Server propio: calculadoras financieras para el sistema de inversión.
v3 — Fix 1: floor mínimo de risk score por leverage
     Fix 2: monthly_cost_usd en calculate_scenarios para overnight fees
v4 — Fix 3: validate_allocation_minimums — checkpoint determinística
     para mínimos por venue/producto (antes el §4 de platforms_skill.md
     era prosa; ahora es una tool que el agente DEBE llamar post-allocate).

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
