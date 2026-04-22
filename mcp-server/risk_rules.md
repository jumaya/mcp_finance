# Reglas de riesgo — Validación autónoma del portafolio

## Cuándo se ejecuta
Este skill se ejecuta AUTOMÁTICAMENTE (sin que el usuario lo pida) en estos momentos:
- Después de seleccionar las posiciones del plan (antes de presentar)
- Cuando se agrega o modifica cualquier posición
- Cuando el usuario reporta rendimiento real
- En cada rebalanceo trimestral sugerido

## Reglas duras (violar cualquiera = recalcular automáticamente)

### R1: Concentración individual
```
SI cualquier posición > 30% del capital:
  → Reducir a 30% máximo
  → Redistribuir excedente a la posición con menor weight
  → Informar: "Reduje [activo] del X% al 30% porque una sola posición no debería ser más del 30% de tu portafolio. Moví el excedente a [otro activo]."
```

### R2: Concentración por vertical
```
SI cualquier vertical (equity/defi/forex/social) > 50% del capital:
  → Reducir a 50% máximo
  → Redistribuir a vertical con menor allocation
  → Informar: "La vertical de [X] tenía el Y% del portafolio. La reduje al 50% para diversificar."
```

### R3: Reserva mínima
```
SI reserva líquida < 10% del capital:
  → Aumentar reserva al 10%
  → Reducir proporcionalmente todas las posiciones
  → Informar: "Mantuve 10% en reserva líquida ($X) para oportunidades y emergencias."
```

### R4: Capital ilíquido
```
SI capital en activos con lock > 30 días > 20% del total:
  → Reemplazar posiciones locked por alternativas flexibles
  → Informar: "No más del 20% debería estar bloqueado. Cambié [X locked] por [Y flexible]."
```

### R5: Correlación
```
PARA cada par de activos en el plan:
  SI ambos son de la misma clase (ej: dos ETFs de USA):
    → Ejecutar calculate_correlation con precios 30 días
    → SI correlación > 0.7:
      → Reemplazar uno de los dos por un activo descorrelacionado
      → Tabla de reemplazos:
        VOO + QQQ (corr ~0.85) → reemplazar QQQ parcial con BND o VWO
        ETH + SOL (corr ~0.75) → considerar, pero aceptable para DeFi
        VOO + MSFT (corr ~0.70) → aceptable pero advertir
```

### R6: Risk score del portafolio (ajustado por correlación)
```
→ Ejecutar calculate_portfolio_risk_score(positions, correlation_matrix)

  Esta tool calcula:
    score_ponderado = Σ(weight_i × risk_score_i)          ← base (R6 v1)

  Y luego ajusta por correlación promedio ponderada entre pares:
    corr_prom = Σ(w_i × w_j × corr_ij) / Σ(w_i × w_j)     para i < j

    SI corr_prom > 0.7:  score_final = score_ponderado + 1.0
      (posiciones se mueven juntas → diversificación aparente, no real)
    SI corr_prom < 0.3:  score_final = score_ponderado - 0.5
      (diversificación real → riesgo agregado menor al de la suma)
    EN OTRO CASO:        score_final = score_ponderado
      (zona neutra 0.3–0.7, sin ajuste)

  score_final se satura a [1, 10].

→ Cómo armar la correlation_matrix:
  - Para cada par (i, j) con i < j, ejecutar calculate_correlation con 30d
    de precios de ambos activos.
  - Construir matriz N×N simétrica con diagonal = 1.0.
  - Pasarla a calculate_portfolio_risk_score.
  - Si no se puede obtener precios de algún par, omitir correlation_matrix
    y la tool devuelve solo el score ponderado base (compat con R6 v1).

→ SI score_final > 7.0:
  → Reducir posición con mayor risk score individual
  → Mover capital a posición con menor risk score
  → Si el problema es la correlación (corr_prom > 0.7), priorizar
    reemplazar una posición del par más correlacionado antes que
    reducir tamaño — eso ataca la causa, no el síntoma.
  → Recalcular hasta que score_final < 7.0

Por qué el ajuste: dos posiciones de risk=8 correlacionadas al 0.9
son mucho más riesgosas que las mismas dos correlacionadas al 0.2
(en la caída, caen juntas). La suma ponderada sola las trataría
idénticamente. El ajuste por correlación promedio ponderada
refleja esta diferencia con una regla simple y auditable.
```

## Stress test obligatorio
```
ANTES de presentar cualquier plan:
→ Ejecutar stress_test_portfolio con escenario "moderate_crash"
→ Incluir en la presentación:
  - "Si los mercados caen moderadamente, tu portafolio de $X bajaría a $Y (Z%)"
  - "Tu ingreso de stablecoins ($W/mes) no se ve afectado"
  - "En el peor escenario, manteniendo la inversión, históricamente se recupera en 12-24 meses"
```

## Exit triggers (auto-generar por posición)
```
PARA cada posición del plan, generar:

SI vertical = equity:
  → Alerta si cae > 15% desde precio de compra
  → Pregunta sugerida: "Tu inversión en [X] bajó 15%. ¿Quieres mantener (históricamente se recupera), vender la mitad para proteger, o vender todo?"

SI vertical = defi Y no es stablecoin:
  → Alerta si cae > 20% desde precio de compra
  → Alerta si APY del pool baja del 2%
  → Alerta si TVL del protocolo cae > 30% en una semana

SI vertical = forex:
  → Stop loss definido en el plan (calculate_position_size)
  → Take profit a 1:2 y 1:3 risk:reward
  
SI vertical = social (copy trading):
  → Alerta si el trader copiado tiene drawdown > 20% en el mes
  → Alerta si deja de operar por > 2 semanas
```

## Orden de ejecución
1. Ejecutar `calculate_risk_score` para cada posición
2. Verificar R1 a R5 — ajustar si viola
3. Ejecutar `calculate_correlation` para cada par relevante de activos
   → Usar los resultados para armar la `correlation_matrix` del portafolio
4. Ejecutar `calculate_portfolio_risk_score(positions, correlation_matrix)`
   → Aplica R6 (score ponderado + ajuste por correlación)
   → Ajustar si score_final > 7.0
5. Ejecutar `stress_test_portfolio` — incluir en presentación
6. Generar exit triggers para cada posición
7. Si algún ajuste se hizo: explicar al usuario qué cambió y por qué
