# Comparación de coloreos: greedy por grado vs DSATUR

Generado con `python -m scripts.comparar_coloreos` (desde `backend/`). Se muestra la cantidad de colores (canastas) usados; menos es mejor. Welsh-Powell no figura porque da exactamente el mismo coloreo que el greedy por grado.

## Grafos al azar de 30 nodos (200 por fila)

| p | clique máx. (cota inferior) | greedy (media) | DSATUR (media) | DSATUR usa menos | DSATUR usa más |
|---|---|---|---|---|---|
| 0.1 | 2.98 | 3.42 | 3.12 | 62 | 1 |
| 0.2 | 3.73 | 4.72 | 4.21 | 98 | 1 |
| 0.3 | 4.42 | 5.92 | 5.38 | 102 | 4 |
| 0.5 | 6.33 | 8.39 | 7.75 | 111 | 10 |
| 0.7 | 9.23 | 11.37 | 10.79 | 109 | 16 |
| 0.9 | 15.76 | 16.50 | 16.07 | 79 | 2 |

## Grafos bipartitos al azar de 15+15 nodos (200 por fila)

Un coloreo óptimo usa siempre 2 colores.

| p | greedy usa más de 2 | DSATUR usa más de 2 | máx. colores del greedy |
|---|---|---|---|
| 0.1 | 117/200 | 0/200 | 3 |
| 0.2 | 135/200 | 0/200 | 5 |
| 0.3 | 84/200 | 0/200 | 5 |
| 0.5 | 27/200 | 0/200 | 6 |

## Datos reales (111 fechas de corte, 30 acciones)

Con la fuente `corr_90d` (la del modelo todavía no está lista) y con `azar`.

| fuente | θ | aristas (media) | greedy (media) | DSATUR (media) | fechas donde DSATUR usa menos | fechas donde usa más |
|---|---|---|---|---|---|---|
| corr_90d | 0.3 | 214 | 13.16 | 13.13 | 5 | 1 |
| corr_90d | 0.5 | 87 | 7.69 | 7.64 | 6 | 0 |
| corr_90d | 0.7 | 20 | 3.73 | 3.73 | 0 | 0 |
| azar | 0.3 | 152 | 6.36 | 5.97 | 43 | 6 |
| azar | 0.5 | 109 | 5.21 | 4.86 | 36 | 2 |
| azar | 0.7 | 64 | 4.08 | 3.76 | 36 | 0 |
