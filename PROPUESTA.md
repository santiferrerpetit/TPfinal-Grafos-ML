# Diversificación de carteras con predicción de correlaciones

## Contexto

Una plataforma de inversiones quiere ayudar a sus clientes a armar carteras de acciones realmente diversificadas. Hoy les sugiere "comprar acciones de distintos sectores", pero eso no alcanza: dos acciones de sectores distintos pueden moverse casi igual, y la correlación entre acciones cambia con el tiempo (en las crisis suele subir justo cuando más se necesita diversificar). Hoy la plataforma usa la correlación histórica, que mira al pasado y no a lo que va a pasar. La plataforma los contrata para construir un sistema que prediga la correlación futura entre pares de acciones y use esa predicción para agrupar las acciones en canastas que no se muevan juntas.

## Objetivo

Construir un sistema que combine un modelo de regresión (para estimar la correlación futura entre cada par de acciones) con algoritmos de grafos (para agrupar las acciones en canastas diversificadas mediante coloreo).

## Datos

Se puede modelar el universo de acciones como un grafo no dirigido:

- Nodo: acción (por ejemplo, unas 30 acciones del S&P 500 de distintos sectores).
- Arista: par de acciones cuya correlación predicha supera un umbral, es decir, que probablemente se muevan juntas. El peso de la arista es la correlación predicha.

El grupo debe generar (o conseguir) un dataset histórico por par de acciones con, al menos, estas columnas:

| Campo | Tipo | Descripción |
|---|---|---|
| `accion_id_1`, `accion_id_2` | id | par de acciones |
| `fecha_corte` | fecha | momento desde el cual se predice |
| `corr_30d`, `corr_90d`, `corr_250d` | numérico | correlación histórica en distintas ventanas |
| `mismo_sector` | booleano | si ambas pertenecen al mismo sector |
| `dif_volatilidad` | numérico | diferencia de volatilidad entre ambas |
| `dif_beta` | numérico | diferencia de beta respecto al mercado |
| `volatilidad_mercado` | numérico | volatilidad reciente del índice |
| `corr_futura_60d` | numérico | correlación de retornos en los 60 días siguientes: **variable a predecir** |

Dataset real adaptado: precios diarios descargados con `yfinance` (Yahoo Finance), calculando retornos y features solo con información anterior a `fecha_corte`. Se cita la fuente y se documentan las transformaciones.

## Requisitos

1. **Modelo predictivo:** entrenar un modelo de regresión que, dado un par de acciones y una fecha de corte, prediga su correlación futura a 60 días. Comparar varios modelos (regresión lineal, KNN, árbol de decisión) contra una línea base que use directamente `corr_90d`. Analizar métricas (MAE, RMSE, R²) sobre un conjunto de test separado en el tiempo (entrenar con el pasado, testear con el futuro).
2. **Construcción del grafo:** usar la predicción del modelo para decidir qué aristas forman el grafo (solo los pares con correlación predicha por encima de un umbral) y con qué peso.
3. **Grafos:** implementar un algoritmo de coloreo greedy (ordenando los nodos por grado) que asigne una canasta (color) a cada acción, de forma que dos acciones unidas por una arista no compartan canasta. Evaluar el resultado con las correlaciones realmente observadas en el período de test, comparando las canastas armadas con el modelo, con la correlación histórica y al azar.

## Frontend

- Visualización del grafo de acciones, coloreadas según la canasta asignada.
- Selector de umbral de correlación, para ver cómo cambian el grafo y la cantidad de canastas necesarias.
- Selector de fecha de corte.
- Tabla de canastas con sus acciones y su correlación promedio interna.
- Comparación visual entre las canastas armadas con el modelo y con la correlación histórica, para que se note el valor agregado del modelo.

## Aclaración

El sistema es educativo: no da asesoramiento financiero ni predice precios, solo estima correlaciones.
