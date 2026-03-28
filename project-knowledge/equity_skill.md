# Skill: Análisis de acciones y ETFs

## Cuándo aplicar
Cuando el usuario quiere invertir en acciones del mercado USA o ETFs. Aplica para perfiles moderados y agresivos.

## Plataformas Colombia
| Plataforma | Mínimo | Comisión | Depósito | Regulación |
|-----------|--------|----------|----------|------------|
| Hapi (PREFERIDA) | $5 USD | 0% broker, ~$0.10 clearing | PSE, Nequi | SEC/FINRA/SIPC |
| eToro | $200 | 0% acciones reales | PayPal, tarjeta | CySEC/FCA |
| XTB | $0 | 0% hasta 100K EUR/mes | PSE | KNF/FCA |
| Interactive Brokers | $0 | Desde $0.005/acción | Transferencia | SEC/FINRA |

## ETFs base
| ETF | Qué es | Expense | Uso |
|-----|--------|---------|-----|
| VOO | S&P 500 (500 empresas USA) | 0.03% | Base de todo portafolio |
| QQQ | NASDAQ 100 (tecnología) | 0.20% | Mayor crecimiento, más volátil |
| VT | Mercado global completo | 0.07% | Máxima diversificación |
| SCHD | Dividendos USA seleccionados | 0.06% | Ingreso pasivo en efectivo |
| VYM | Alto dividendo | 0.06% | Ingreso pasivo estable |
| BND | Bonos USA | 0.03% | Reducir riesgo total |

## Proceso
1. Obtener datos con Alpha Vantage: precio, P/E, dividend yield, RSI 14d
2. Filtrar: solo activos con volumen > $1M diario, ETFs con expense < 0.5%
3. Calcular escenarios: `calculate_scenarios` con volatilidad histórica
4. Calcular dividendos netos: `calculate_tax_impact` tipo "us_stock_dividend"
5. Evaluar riesgo: `calculate_risk_score`

## Cronograma tipo
- Día 1: Descargar Hapi, registrarse con cédula (15 min + 24h verificación)
- Día 2: Depositar via PSE (instantáneo, $0). Comprar con orden limit (~$0.10 clearing)
- Día 15: Verificar posición en portafolio
- Día 30: Segundo aporte mensual (DCA)
- Trimestral: Revisar dividendos, reinvertir si > $5

## W-8BEN (CRÍTICO)
- Sin W-8BEN: USA retiene 30% del dividendo
- Con W-8BEN: solo 15%
- En Hapi: Configuración > Información fiscal > W-8BEN (5 minutos)
- Con $150 en VOO: ~$0.82 neto/trimestre (con W-8BEN) vs ~$0.57 (sin)

## Explicación para principiantes
"Un ETF es como una canasta con pedacitos de muchas empresas. En lugar de comprar una acción de Apple por $230, compras un pedacito de un fondo que INCLUYE Apple junto con otras 499 empresas. Si una va mal, las otras compensan."
