# Reglas de riesgo — Validación autónoma del portafolio v2

## Cuándo se ejecuta
Este skill se ejecuta AUTOMÁTICAMENTE en el Paso 5 del orquestador:
- Después de seleccionar las posiciones del plan (antes de presentar)
- Cuando se agrega o modifica cualquier posición
- Cuando el usuario reporta rendimiento real
- En cada rebalanceo trimestral sugerido

## Reglas por perfil de riesgo

### R1: Concentración individual
```
RIESGO BAJO (1-3):    ninguna posición > 25% del capital
RIESGO MODERADO (4-6): ninguna posición > 30% del capital
RIESGO ALTO (7-8):    ninguna posición > 35% del capital
RIESGO EXTREMO (9-10): ninguna posición > 40% del capital

SI viola → reducir al máximo permitido y redistribuir excedente.
```

### R2: Concentración por vertical
```
TODOS LOS PERFILES: ninguna vertical > 50% del capital
SI viola → reducir a 50% y redistribuir.
```

### R3: Reserva mínima
```
RIESGO BAJO:     reserva líquida ≥ 15%
RIESGO MODERADO: reserva líquida ≥ 10%
RIESGO ALTO:     reserva líquida ≥ 0% (no obligatoria)
RIESGO EXTREMO:  reserva líquida ≥ 0% (no obligatoria)

Para riesgo alto y extremo, la reserva es OPCIONAL.
El usuario acepta no tener colchón de seguridad.
```

### R4: Capital ilíquido
```
TODOS LOS PERFILES: activos con lock > 30 días ≤ 20% del total
SI viola → reemplazar por alternativas flexibles.
```

### R5: Correlación
```
PARA cada par (i, j) de activos del plan con i < j:
  → Obtener 30 días de precios de cierre reales desde Alpha Vantage
    para ambos activos.
  → Ejecutar calculate_correlation(prices_a, prices_b).

Umbrales (sobre el valor devuelto por la tool, no sobre supuestos):
  SI correlación > 0.7:
    → Riesgo BAJO / MODERADO: reemplazar uno de los dos por un activo
      descorrelacionado y recalcular.
    → Riesgo ALTO / EXTREMO: advertir, permitir si el usuario lo acepta
      explícitamente.
  SI 0.3 < correlación ≤ 0.7:
    → Aceptable. Reportar el valor en la presentación del plan.
  SI correlación ≤ 0.3:
    → Buena diversificación. Reportar el valor.

Datos faltantes:
  Si no se obtienen 30 días de precios para algún activo (ticker no
  cubierto, símbolo nuevo, error de la API), NO inventar correlaciones
  ni usar estimaciones del modelo. Marcar el par como "correlación no
  disponible" en la presentación y dejar la decisión al usuario.

Prohibido: usar correlaciones precalculadas o pares "conocidos" que no
provengan de calculate_correlation sobre datos reales del periodo.
```

### R6: Risk score del portafolio (ajustado por correlación)
```
Ejecutar calculate_portfolio_risk_score(positions, correlation_matrix)

La tool calcula:
  score_ponderado = Σ(weight_i × risk_score_i)            ← base

Y luego ajusta por correlación promedio ponderada entre pares:
  corr_prom = Σ(w_i × w_j × corr_ij) / Σ(w_i × w_j)       para i < j

  SI corr_prom > 0.7:  score_final = score_ponderado + 1.0
  SI corr_prom < 0.3:  score_final = score_ponderado - 0.5
  EN OTRO CASO:        score_final = score_ponderado

score_final se satura a [1, 10].

Límites por perfil (evaluar sobre score_final, no sobre el ponderado base):
  RIESGO BAJO:     score_final ≤ 4.0
  RIESGO MODERADO: score_final ≤ 6.0
  RIESGO ALTO:     score_final ≤ 8.0
  RIESGO EXTREMO:  sin límite (acepta cualquier score)

Cómo armar la correlation_matrix:
  - Para cada par (i, j) con i < j, ejecutar calculate_correlation con 30d.
  - Construir matriz N×N simétrica con diagonal = 1.0.
  - Pasarla a calculate_portfolio_risk_score.
  - Si no hay precios para algún par, omitir la matriz: la tool devuelve
    solo el score ponderado base (compatible con R6 v1).

SI viola → reducir posición con mayor risk score y redistribuir.
  Si además corr_prom > 0.7, priorizar reemplazar una posición del par
  más correlacionado antes que solo reducir tamaño — eso ataca la causa
  (concentración en un mismo factor), no el síntoma.

Por qué el ajuste: dos posiciones de risk=8 correlacionadas al 0.9 son
mucho más riesgosas que las mismas dos correlacionadas al 0.2. En caída
caen juntas. La suma ponderada sola las trata idénticamente; el ajuste
por correlación promedio ponderada refleja la diversificación real.
```

## Stress test obligatorio
```
ANTES de presentar cualquier plan:
  → Ejecutar stress_test_portfolio con "moderate_crash" Y "severe_crash"
  → Incluir AMBOS en la presentación con montos en dólares
  → Verificar que la pérdida máxima NO exceda la tolerancia declarada:
    - Riesgo bajo: pérdida max ≤ 20%
    - Riesgo moderado: pérdida max ≤ 40%
    - Riesgo alto: pérdida max ≤ tolerancia declarada (típicamente 70-80%)
    - Riesgo extremo: acepta pérdida total
```

## Exit triggers (auto-generar por posición)
```
SI vertical = equity:
  → Alerta si cae > 15% desde precio de compra (riesgo bajo/moderado)
  → Alerta si cae > 25% desde precio de compra (riesgo alto)

SI vertical = defi Y no es stablecoin:
  → Alerta si cae > 20%
  → Alerta si APY baja del 2%
  → Alerta si TVL del protocolo cae > 30% en una semana

SI vertical = forex:
  → Stop loss definido en el plan (calculate_position_size)

SI vertical = social (copy trading):
  → Alerta si drawdown del trader > 25% en el mes
  → Alerta si deja de operar > 2 semanas
```

## Orden de ejecución
1. Ejecutar `calculate_risk_score` para cada posición
2. Verificar R1 a R5 según el perfil de riesgo del usuario
3. Ejecutar `calculate_correlation` para cada par principal de activos
   → Armar la `correlation_matrix` del portafolio con los resultados
4. Ejecutar `calculate_portfolio_risk_score(positions, correlation_matrix)`
   → Aplica R6 (score ponderado + ajuste por correlación)
   → Verificar límite según perfil del usuario (BAJO/MODERADO/ALTO/EXTREMO)
5. Ejecutar `stress_test_portfolio` con moderate Y severe
6. Generar exit triggers por posición
7. Si algún ajuste se hizo: explicar al usuario qué cambió y por qué
