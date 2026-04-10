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
EJECUTAR calculate_correlation entre los activos principales del plan.

SI correlación > 0.7:
  → ADVERTIR (no bloquear automáticamente para riesgo alto)
  → Para riesgo bajo/moderado: reemplazar uno por activo descorrelacionado
  → Para riesgo alto/extremo: advertir pero permitir si el usuario lo acepta

Pares conocidos de alta correlación:
  VOO + QQQ (~0.85) → problema para cualquier perfil
  COIN + BTC/ETH (~0.80) → aceptable si es la tesis del plan
  NVDA + AMD (~0.70) → advertir
  ETH + SOL (~0.65) → aceptable
```

### R6: Risk score del portafolio
```
Calcular risk score ponderado: Σ(weight_i × risk_score_i)

RIESGO BAJO:     score ponderado debe ser ≤ 4.0
RIESGO MODERADO: score ponderado debe ser ≤ 6.0
RIESGO ALTO:     score ponderado debe ser ≤ 8.0
RIESGO EXTREMO:  sin límite (acepta cualquier score)

SI viola → reducir posición con mayor risk score y redistribuir.
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
2. Verificar R1 a R6 según el perfil de riesgo del usuario
3. Ejecutar `calculate_correlation` para pares principales
4. Ejecutar `stress_test_portfolio` con moderate Y severe
5. Generar exit triggers por posición
6. Si algún ajuste se hizo: explicar al usuario qué cambió y por qué
