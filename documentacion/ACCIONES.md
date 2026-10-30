# Acciones elegidas

30 acciones del S&P 500 más el índice (`^GSPC`) para calcular beta y volatilidad de mercado.

## Criterio

- Cubrir los 11 sectores, con 1 a 4 acciones por sector.
- Mezclar pares muy correlacionados (mismo sector) con pares casi independientes (sectores distintos), para que el modelo vea todo el rango de correlaciones.
- Incluir acciones cíclicas, defensivas y de beta extremo, para que `dif_beta` y `dif_volatilidad` tengan variación.
- Historia completa desde 2014, sin fusiones ni spin-offs que cambien el ticker.

## Lista

| Sector | Acciones | Motivo |
|---|---|---|
| Tecnología | AAPL, MSFT, NVDA | Núcleo del mercado, muy correlacionadas. NVDA tiene beta y volatilidad altas. |
| Comunicaciones | GOOGL, VZ | Una growth y una defensiva en el mismo sector. |
| Consumo discrecional | AMZN, HD, MCD, TSLA | Sensibles al ciclo. TSLA es muy idiosincrática. |
| Consumo básico | KO, PG, WMT | Defensivas, beta baja. |
| Salud | JNJ, PFE, UNH | Poco ligadas al ciclo económico. |
| Financiero | JPM, BAC, GS | Muy correlacionadas entre sí, sensibles a tasas. |
| Energía | XOM, CVX, COP | Siguen al petróleo y se desacoplan del resto en 2015-16 y 2020. |
| Industriales | CAT, BA, UNP | Cíclicas. BA tiene shocks propios (2019-20). |
| Materiales | NEM, FCX | NEM (oro) actúa como refugio, FCX (cobre) es muy cíclica. |
| Utilities | NEE, DUK | Defensivas, sensibles a tasas. |
| Inmobiliario | AMT, PLD | Sensibles a tasas. |

## Pares de referencia

- Muy correlacionados: JPM-BAC, XOM-CVX.
- Casi independientes: NEM-NVDA, KO-TSLA.

## Limitaciones a declarar en el informe

- Sesgo de supervivencia: son empresas que hoy están en el S&P 500.
- Los sectores son los actuales (por ejemplo, GOOGL pasó a Comunicaciones en 2018).
- Solo ~30 de los 435 pares son del mismo sector, así que `mismo_sector` está desbalanceada.
- Falta confirmar que los 30 tickers descargan completos desde `yfinance`.
