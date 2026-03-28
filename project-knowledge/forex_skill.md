# Skill: Análisis de Forex y CFDs

## Cuándo aplicar
Solo para perfiles moderados-agresivos con horizonte corto-mediano. NUNCA como primera recomendación para principiantes. Siempre recomendar cuenta demo primero.

## Reglas estrictas
- Apalancamiento máximo: 5x (NUNCA más para principiantes)
- Riesgo por trade: máximo 2% del capital asignado a forex
- Siempre definir stop-loss ANTES de la entrada
- Siempre usar `calculate_position_size` para dimensionar
- Cuenta demo mínimo 1 mes antes de capital real
- Forex NO genera ingreso pasivo — es semi-activo

## Plataformas Colombia
| Plataforma | Activos | Depósito CO | Regulación |
|-----------|---------|-------------|------------|
| Capital.com | 3,700+ CFDs | PSE directo | FCA/CySEC |
| XTB | 5,800+ | PSE, oficina CO | KNF/FCA |
| eToro | 4,500+ | PayPal, tarjeta | CySEC/FCA/ASIC |
| Pepperstone | Forex, CFDs | Transferencia | ASIC/FCA/BaFIN |

## Pares para principiantes
| Par | Spread | Volatilidad | Nota |
|-----|--------|------------|------|
| EUR/USD | 0.6-1.0 pip | Baja-media | Más líquido, ideal inicio |
| GBP/USD | 1.0-1.5 pip | Media | Más volátil |
| USD/JPY | 0.7-1.2 pip | Baja-media | Buenos movimientos tendenciales |
| XAU/USD | 2-4 pips | Media-alta | Cobertura contra inflación |

## Estrategia: Swing trading
- Horizonte: 2-10 días por trade
- Timeframes: D1 y H4
- Indicadores: medias móviles 20/50/200, RSI 14, soportes/resistencias
- Máximo 2-3 trades simultáneos

## Proceso
1. Datos: Alpha Vantage FX_DAILY y CURRENCY_EXCHANGE_RATE
2. Setup: tendencia en D1 + retroceso a S/R + RSI no extremo
3. Posición: `calculate_position_size` con entry, stop, capital, 2% riesgo
4. Impuestos: `calculate_tax_impact` tipo "forex_gain"

## Cronograma tipo
- Semana 1-4: Cuenta demo exclusivamente
- Mes 2: Si demo fue rentable, cuenta real con máximo $100, micro-lotes
- Mes 4+: Evaluar si continuar o reasignar capital

## Explicación para principiantes
"El trading de divisas es comprar una moneda esperando que suba contra otra. A diferencia de acciones o staking, aquí NO generas ingresos pasivos — requiere tu atención. El 70-80% de cuentas minoristas pierden dinero."

## Advertencias obligatorias
- "70-80% de cuentas de trading minorista pierden dinero"
- "El apalancamiento amplifica ganancias Y pérdidas"
- "SIEMPRE empieza con cuenta demo"
