# Skill: Agente de copy trading y social trading

## Cuándo se activa
Automáticamente cuando:
- El allocate_portfolio asigna capital a "social"
- El usuario menciona copy trading, copiar traders, eToro, CopyTrader, social trading, popular investors
- El capital total es >= $200 (mínimo eToro)
- El usuario quiere ingresos pasivos sin aprender trading

## MCP tools disponibles (eToro MCP server — 34 tools)
Este skill utiliza el servidor MCP de eToro directamente para:
- Consultar portafolio real del usuario
- Buscar instrumentos y sus tasas de mercado
- Consultar datos de velas para análisis
- Obtener top popular investors por rendimiento
- Crear watchlists
- Colocar órdenes (buy/sell, limit, DCA)
- Gestionar posiciones abiertas

## Lógica de decisión autónoma

### Barrera de entrada
```
SI capital_total < $200:
  → NO incluir copy trading en el plan
  → Explicar: "eToro requiere un depósito mínimo de $200. Cuando acumules ese monto, podemos agregar copy trading como vertical"
  → Sugerir: "Por ahora tu capital rinde más en ETFs ($5 mín en Hapi) y stablecoins lending"
  → DETENER este skill

SI capital_total >= $200 Y capital_social < $200:
  → Ajustar allocate_portfolio para que social tenga al menos $200
  → Redistribuir desde la vertical con mayor peso
  → Explicar el ajuste

SI capital_total >= $500:
  → Asignar 15-20% a copy trading (según risk_tolerance)
  → Diversificar entre 3-5 traders a copiar
```

### Selección autónoma de popular investors
```
→ Usar eToro MCP: obtener lista de popular investors
→ Filtrar automáticamente con estos criterios:

OBLIGATORIOS (todos deben cumplirse):
  - Historial > 12 meses de rendimiento positivo
  - Drawdown máximo < 20% en último año
  - Risk score eToro ≤ 5 (de 10)
  - Número de copiadores > 100 (señal de confianza comunitaria)
  - Activo en últimos 30 días (ha hecho trades)

PREFERIDOS (mejoran el ranking):
  - Rendimiento anual 10-25% (sostenible, no especulativo)
  - Mixto de activos (no 100% en un solo instrumento)
  - Comunicación activa (posts y análisis en su feed)
  - Tiempo promedio de trades > 7 días (swing, no scalping)

SI ningún trader cumple todos los criterios obligatorios:
  → Advertir: "No encontré traders que cumplan todos mis criterios de seguridad en este momento"
  → Sugerir: "Esperemos 1-2 semanas y revisamos de nuevo, o asignemos ese capital a ETFs temporalmente"
  → NO recomendar traders que no cumplan — esto es comportamiento de agente responsable
```

### Diversificación de traders
```
SI capital_social >= $200 Y < $500:
  → Copiar 2-3 traders diferentes
  → Mínimo $50 por trader (umbral mínimo de copia útil)
  → Buscar traders con estrategias diferentes (1 equity-focused + 1 cripto-focused)

SI capital_social >= $500:
  → Copiar 3-5 traders
  → Mínimo $100 por trader
  → Diversificar: equity, cripto, forex, commodities
  → NO copiar traders con correlación alta entre sí

SIEMPRE:
  → Verificar que los traders copiados no operen los mismos instrumentos principales
  → Si 2+ traders tienen >50% de overlap en instrumentos → advertir y sugerir alternativa
```

### Monitoreo autónomo (cuando usuario vuelve)
```
SI el usuario dice "revisa mi portafolio" o "cómo van mis inversiones":
  → Usar eToro MCP: consultar portafolio actual
  → Para cada trader copiado:
    - Rendimiento desde que lo copia
    - Drawdown actual
    - Número de trades recientes
    - Comparar vs rendimiento de referencia (VOO/SPY)
  
  → SI algún trader tiene drawdown > 15% en el mes:
    → Advertir: "El trader [X] tiene una caída del Y% este mes. Si baja del 20%, consideraría dejar de copiarlo."
  
  → SI algún trader no ha operado en > 2 semanas:
    → Advertir: "El trader [X] no ha hecho operaciones en [N] días. Podría estar inactivo."
  
  → SI el rendimiento total de copy trading < rendimiento de VOO en el mismo período:
    → Sugerir: "Tu copy trading está rindiendo menos que un simple ETF del S&P 500. Considera mover parte del capital a VOO."
```

### Modo trading del MCP
```
SIEMPRE empezar con ETORO_TRADING_MODE=demo:
  → Primero probar en modo demo que el flujo funciona
  → Verificar que las órdenes se ejecutan correctamente
  → Solo después de confirmar: cambiar a modo real

SI el usuario no ha probado en demo:
  → Recomendar 2 semanas en demo primero
  → "Vamos a probar la estrategia en demo (dinero virtual) por 2 semanas antes de usar capital real"
```

## Plataformas
| Plataforma | Mínimo | Copy mín | Depósito CO | Regulación |
|-----------|--------|----------|-------------|------------|
| eToro (PRINCIPAL) | $200 | $200 por trader | PayPal, tarjeta | CySEC/FCA/ASIC |
| LBX/Libertex | Sin mín | Varía | PSE, tarjeta | FSC Mauritius |

## Cálculos obligatorios
1. `calculate_scenarios(amount, apy=rendimiento_trader, volatility=drawdown_trader, passive=0, months)`
2. `calculate_risk_score(volatility_30d, max_drawdown, "instant", True, weight_pct)`
   - platform_regulated = True (eToro es regulado CySEC/FCA)
   - liquidity = "instant" (puedes dejar de copiar en cualquier momento)
3. `calculate_tax_impact("copy_trading_gain", estimated_annual_gain)`

## Cronograma tipo
```
Día 1: Registrar en eToro (10 min + KYC 1-3 días)
Día 3: Depositar $200+ via PayPal o tarjeta
Día 3: Abrir cuenta demo y explorar Popular Investors
Día 3-7: Seleccionar 2-3 traders usando los criterios del skill
Día 7: Empezar a copiar en modo DEMO
Día 14-21: Evaluar rendimiento demo
Día 21: Si demo fue positivo → empezar a copiar con capital real
Día 30: Primer review de rendimiento real

Mensual: Revisar rendimiento de cada trader copiado
Trimestral: Evaluar si mantener, cambiar o reasignar traders
```

## Encadenamientos con otros skills
```
→ Si el usuario copia traders que operan acciones USA:
  → Activar equity_skill.md para contexto de los activos
  → Ejecutar calculate_tax_impact con tipo "copy_trading_gain"

→ Si el usuario copia traders de cripto:
  → Activar defi_skill.md para evaluar los activos cripto del trader

→ Antes de presentar la recomendación:
  → Ejecutar risk_rules.md para validar que copy trading no exceda 50% de la vertical social
  → Ejecutar stress_test_portfolio incluyendo las posiciones de copy trading
```

## Explicación adaptativa
```
SI principiante:
  "Copy trading es como seguir las jugadas de un inversor experimentado. Cuando él compra algo, automáticamente tú también compras. Cuando vende, tú vendes. No necesitas saber de trading — solo elegir buenos traders para seguir. Es como tener un gestor de inversión personal, pero más barato."

SI intermedio:
  "CopyTrader de eToro replica proporcionalmente las posiciones de popular investors. Tu rendimiento es el del trader menos el spread de eToro. Evalúa por Sharpe ratio implícito: rendimiento/drawdown máximo."

SI avanzado:
  "Optimiza tu cartera de traders: selecciona por correlación baja entre ellos, maximiza diversificación de instrumentos subyacentes, y establece stop-copy basado en drawdown percentil 95."
```

## Advertencias obligatorias
- "El rendimiento pasado de un trader no garantiza rendimiento futuro"
- "Puedes perder dinero incluso copiando traders exitosos"
- "Los Popular Investors de eToro no son asesores financieros certificados"
- "Siempre empieza con cuenta demo antes de copiar con dinero real"
- "No pongas más del 20% de tu capital total en copy trading"
