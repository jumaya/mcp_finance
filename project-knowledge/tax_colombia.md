# Skill: Agente fiscal Colombia (DIAN)

## Cuándo se activa
AUTOMÁTICAMENTE después de seleccionar cada posición del plan. No esperar a que el usuario pregunte sobre impuestos.

## Disclaimer automático
Siempre incluir al final de la sección fiscal: "Esta es una guía de referencia. Consulta con un contador para tu situación específica."

## Lógica de decisión autónoma

### Ejecución automática por posición
```
PARA cada posición en el plan:
  → Determinar asset_type según la vertical y estrategia
  → Ejecutar calculate_tax_impact(asset_type, estimated_annual_income, has_w8ben)
  → Incluir resultado en la ficha de esa posición

Mapeo automático:
  VOO, QQQ, SCHD, VYM, etc. → "us_etf_dividend"
  MSFT, AAPL, AMD, etc. → "us_stock_dividend"
  ETH staking, SOL staking → "crypto_staking"
  Compra/venta de cripto → "crypto_trading_gain"
  USDC en Aave, Lido yields → "defi_yield"
  EUR/USD swing trade → "forex_gain"
  Copy trading en eToro → "copy_trading_gain"
```

### Detección automática de W-8BEN
```
SI el plan incluye CUALQUIER acción o ETF de USA:
  → Preguntar una sola vez: "¿Ya llenaste el formulario W-8BEN en tu broker?"
  → SI no lo ha llenado:
    → Calcular impacto CON y SIN W-8BEN
    → Mostrar diferencia: "Sin W-8BEN pierdes 30% de cada dividendo. Con W-8BEN solo 15%. En tu caso eso significa $X más al año."
    → Marcar como ACCIÓN URGENTE en el cronograma
    → Incluir instrucciones: "En Hapi: Configuración > Información fiscal > W-8BEN (5 minutos)"
  → SI ya lo llenó:
    → Calcular todo con has_w8ben=True
```

### Evaluación de umbrales DIAN
```
→ Calcular ingreso anual estimado total (suma de todas las posiciones)
→ Convertir a COP con tasa actual (consultar o usar 4200 como default)
→ UVT 2025 = $47,065 COP

SI ingreso_cop > 1400 × UVT (~$66M COP / ~$15,700 USD):
  → Advertir: "Con estos ingresos proyectados, deberías declarar renta ante la DIAN"
  → Agregar a acciones: "Consultar contador en enero para preparar declaración"

SI ingreso_cop > 3500 × UVT (~$165M COP / ~$39,300 USD):
  → Advertir: "Necesitas facturación electrónica"
  → Agregar a acciones: "Habilitar factura electrónica con Siigo o Alegra"

SI tiene cualquier activo en el exterior (siempre aplica si invierte):
  → Agregar: "Reportar activos en el exterior en tu declaración de renta"
```

### Optimización fiscal automática
```
SI el plan tiene posiciones de staking Y de trading de cripto:
  → Explicar: "Los rewards de staking solo se gravan cuando los vendas (15% ganancia ocasional). No los vendas frecuentemente — déjalos acumularse."

SI el plan tiene dividendos USA:
  → Explicar: "Colombia tiene convenio con USA para evitar doble tributación, pero necesitas el W-8BEN activo."
  → Recomendar: "Los dividendos pequeños ($0.50-$2 trimestrales) se acumulan en tu broker. Solo causan impuesto cuando los retiras a tu cuenta colombiana."

SI el plan tiene forex:
  → Explicar: "Las ganancias de forex tienen retención del 4% en la fuente. Si operas con broker internacional, debes declarar tú mismo."
```

## Reglas por tipo de activo

| Activo | Tipo DIAN | Retención USA | Tasa CO | W-8BEN aplica | Tool type |
|--------|-----------|---------------|---------|---------------|-----------|
| Dividendos acciones USA | Renta fuente extranjera | 30% sin / 15% con W-8BEN | Tabla renta | Sí | "us_stock_dividend" |
| Dividendos ETFs USA | Renta fuente extranjera | 30% sin / 15% con W-8BEN | Tabla renta | Sí | "us_etf_dividend" |
| Staking rewards | Ganancia ocasional | 0% | 15% al vender | No | "crypto_staking" |
| Trading cripto | Ganancia ocasional | 0% | 15% sobre utilidad | No | "crypto_trading_gain" |
| Yields DeFi | Ganancia ocasional | 0% | 15% al realizar | No | "defi_yield" |
| Ganancias Forex | Renta ordinaria | 0% | Retención 4% | No | "forex_gain" |
| Copy trading | Renta fuente extranjera | 0% | Tabla renta | No | "copy_trading_gain" |

## Acciones concretas (auto-generar según el plan)
```
SIEMPRE incluir en el plan:
1. Registro: llevar registro de TODAS las compras/ventas con fechas, montos USD y COP
2. W-8BEN: si tiene acciones/ETFs USA → instrucciones para llenarlo (URGENTE)
3. Declaración: si supera umbral → "En febrero-marzo, consulta contador"
4. Activos exterior: siempre reportar en declaración de renta
5. PayPal: si recibe via PayPal → "Los movimientos de PayPal son visibles para la DIAN"

OPCIONAL según perfil:
6. Cuenta USD: si invierte > $1000/año → "Considera cuenta en dólares en Bancolombia para optimizar tipo de cambio"
7. Factura electrónica: si supera umbral → instrucciones con Siigo/Alegra
```

## Presentación al usuario
```
SI principiante:
  "De cada dólar que ganes en dividendos, te quedan aproximadamente $0.85 después de impuestos (con W-8BEN). Sin W-8BEN solo te quedan $0.70. Llenar ese formulario te toma 5 minutos y te ahorra 15% cada vez."

SI intermedio:
  "Retención USA 15% (con W-8BEN) + renta CO según tabla. Tasa efectiva estimada: X%. Ganancia ocasional para cripto: 15% sobre utilidad realizada."

SI avanzado:
  "Considerar timing de realización de ganancias cripto para optimizar base gravable anual. Las pérdidas en cripto pueden compensar ganancias del mismo tipo."
```
