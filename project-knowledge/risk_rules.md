# Reglas de riesgo del portafolio

## Reglas inquebrantables (validar SIEMPRE antes de presentar un plan)
1. Ninguna posición individual > 30% del capital
2. Ninguna vertical > 50% del capital
3. Reserva líquida mínima: 10% (stablecoins o efectivo)
4. Capital en activos ilíquidos (lock > 30 días) < 20%
5. Si dos activos tienen correlación > 0.7: advertir y sugerir reemplazo
6. Risk score ponderado del portafolio < 7/10

## Proceso de validación
Para cada activo: ejecutar `calculate_risk_score` con volatility_30d, max_drawdown_12m, liquidity, platform_regulated, weight_in_portfolio_pct.

Si risk score ponderado > 7/10:
1. Reducir posición con mayor score
2. Mover capital a posición más segura
3. Re-calcular hasta cumplir

## Correlación
Si el plan incluye VOO y QQQ juntos: ejecutar `calculate_correlation`. Históricamente correlación ~0.85 (problemática).
Alternativas de menor correlación con VOO: BND (bonos, ~0.15), VWO (emergentes, ~0.62), GLD (oro, ~0.08).

## Stress test
SIEMPRE ejecutar `stress_test_portfolio` con "moderate_crash" antes de presentar. Mostrar:
- "En un escenario de caída moderada, tu portafolio bajaría de $X a $Y"
- "Tu ingreso de stablecoins ($Z/mes) NO se ve afectado"

## Exit triggers por tipo de activo
- Acciones/ETFs: alerta si caen > 15% desde precio de compra
- Cripto (no stablecoins): alerta si cae > 20%
- DeFi yield: alerta si APY baja del 2%
- DeFi TVL: alerta si TVL del protocolo cae > 30% en una semana
