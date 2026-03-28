# Reglas tributarias Colombia (DIAN)

## Disclaimer
Guía de referencia. Siempre recomendar consultar con un contador.

## Reglas por activo
| Activo | Tipo impuesto | Retención USA | Tasa CO | Tool |
|--------|--------------|---------------|---------|------|
| Dividendos acciones USA | Renta fuente extranjera | 30% sin W-8BEN, 15% con | Tabla renta | `calculate_tax_impact` tipo "us_stock_dividend" |
| Dividendos ETFs USA | Renta fuente extranjera | 30%/15% | Tabla renta | tipo "us_etf_dividend" |
| Staking rewards | Ganancia ocasional | 0% | 15% al vender | tipo "crypto_staking" |
| Trading cripto | Ganancia ocasional | 0% | 15% sobre utilidad | tipo "crypto_trading_gain" |
| Yields DeFi | Ganancia ocasional | 0% | 15% al realizar | tipo "defi_yield" |
| Ganancias Forex | Renta ordinaria | 0% | Retención 4% | tipo "forex_gain" |
| Copy trading | Renta fuente extranjera | 0% | Tabla renta | tipo "copy_trading_gain" |

## Umbrales importantes (UVT 2025 = $47,065 COP)
| Umbral | COP | USD aprox | Acción |
|--------|-----|-----------|--------|
| Declarar renta | ~$66M | ~$15,700 | Declarar ante DIAN |
| Reportar activos exterior | Cualquier monto | Cualquiera | Reportar en declaración |
| Facturación electrónica | ~$165M | ~$39,300 | Habilitar |

## Acciones concretas para el usuario
1. INMEDIATO: Llenar W-8BEN en broker (si tiene acciones USA)
2. Llevar registro de compras/ventas con fechas y montos
3. Guardar estados de cuenta de cada plataforma
4. Feb-marzo cada año: declarar renta si supera umbral
5. Considerar cuenta en dólares (Bancolombia) para optimizar tipo de cambio

## PayPal
Ingresos via PayPal deben convertirse a COP y declararse. DIAN puede consultar movimientos.
