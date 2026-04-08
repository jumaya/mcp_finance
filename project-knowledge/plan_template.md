# Template del plan de inversión — v4

## Rendimiento mínimo por perfil (escenario BASE, 6 meses)
```
Bajo: +4-8% | Moderado: +10-20% | Alto: +30-60% | Extremo: +40-200%
SI rendimiento proyectado < mínimo → recalibrar activos
```

## Límite defensivo (stablecoins + reserva + ETFs broad)
```
Bajo: ≤60% | Moderado: ≤30% | Alto: ≤10% | Extremo: ≤5%
```

## Secciones obligatorias (12)

1. **Contexto mercado** — datos reales con fuente MCP
2. **Asimetrías** — oportunidades detectadas con datos
3. **Popular investors** — del eToro MCP + copy trading como posición
4. **Posiciones con tesis** — ticker, plataforma, tipo, monto, RSI, tesis, catalizador+fecha, riesgo, entrada, SL, TP1, TP2
5. **Cálculos reales** — escenarios (via calculate_scenarios), risk score (via calculate_risk_score), tax (via calculate_tax_impact)
6. **Correlación** — via calculate_correlation entre posiciones principales
7. **Costos totales** — overnight fees CFDs + trading fees + spread P2P
8. **Stress test** — via stress_test_portfolio con crash -20% y -40%
9. **Cronograma Mes 1** — semana a semana, incluir earnings dates
10. **Escenarios 3M y 6M** — tablas con razones específicas
11. **Impacto fiscal** — Colombia/DIAN por tipo de activo
12. **Seguimiento + disclaimers** — calendario revisión + disclaimers

## Checklist calidad (verificar ANTES de presentar)
```
□ Precios reales via MCP (no inventados)
□ Tesis específica por posición (no genérica)
□ Catalizador con fecha por posición
□ SL y TP por posición
□ Escenarios via calculate_scenarios (no inventados)
□ Risk score via calculate_risk_score (no inventado)
□ Tax via calculate_tax_impact (no inventado)
□ Correlación via calculate_correlation (no inventada)
□ Stress test via stress_test_portfolio (no inventado)
□ Copy trading incluido como posición (si eToro)
□ Overnight fees calculados (si CFDs)
□ Earnings dates en cronograma
□ % defensivo ≤ límite del perfil
□ Rendimiento base ≥ mínimo del perfil
□ Checkpoints ✅ visibles
□ Disclaimers al final
```
