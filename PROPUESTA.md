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

### Fuentes de los datos tabulados

Yahoo Finance entrega datos tabulados, pero son **precios por acción**, no el dataset por pares. Ese dataset lo construimos nosotros.

| Dato | Fuente | Formato | Observaciones |
|---|---|---|---|
| Precios diarios (`Open/High/Low/Close/Volume`) de ~30 acciones del S&P 500 y del índice (`^GSPC` o `SPY`) | `yfinance` → `yf.download(tickers, start, end, auto_adjust=True)` | DataFrame de pandas: índice = fecha, columnas MultiIndex (campo × ticker). Con `df["Close"]` queda una matriz fecha × ticker | `yfinance` es una librería de código abierto que usa los endpoints públicos de Yahoo. **No es una API oficial ni está afiliada a Yahoo**, y su documentación indica uso personal o educativo. Se cita en el informe |
| Sector de cada acción | Tabla propia `sectores.csv` (ticker, sector), armada a mano | CSV | `yf.Ticker(t).info["sector"]` existe, pero es lento y a veces falla. Fijar la tabla a mano da reproducibilidad |
| Beta respecto al mercado | **Calculado por nosotros**: regresión rodante de los retornos de la acción contra los del índice | Columna derivada | El `beta` de `.info` es un valor actual. Usarlo en fechas pasadas filtraría información del futuro |
| Volatilidad, correlaciones, `corr_futura_60d` | **Calculados por nosotros** con pandas a partir de los retornos | Columnas derivadas | Con 30 acciones hay 435 pares. Con una fecha de corte cada ~20 días durante ~10 años salen del orden de 50 mil filas |

Decisiones para que el trabajo sea reproducible:

- La descarga se hace **una sola vez** y se guarda en el repositorio (`data/precios.csv`). Así el resultado no depende de que Yahoo siga disponible ni de que cambie su formato.
- Cada feature se calcula con retornos **anteriores o iguales a `fecha_corte`**. Solo `corr_futura_60d` usa los 60 días siguientes.
- Alternativas si `yfinance` fallara: datasets públicos de Kaggle con precios del S&P 500 (un CSV por ticker) o la API gratuita de Alpha Vantage, que tiene límite de pedidos. Habría que revisar licencia y vigencia de cada uno antes de usarlos.

## Uso de grafos

La idea es apoyar el trabajo en los conceptos de Teoría de Grafos de la materia e investigar los que haga falta profundizar.

### Para qué se usan los grafos en el sistema

El grafo no es solo una visualización: es el paso que convierte las predicciones en una decisión.

- El modelo de regresión solo entrega un número por par de acciones (435 valores $\hat\rho(i,j)$ para 30 acciones). Eso no le dice al cliente qué acciones juntar.
- Lo que se necesita es una **partición global** de las acciones en canastas en las que ningún par se mueva junto. El coloreo propio del grafo la produce.

Funciones concretas:

1. **Produce el resultado del sistema.** Las canastas salen del coloreo, no del dibujo.
2. **Impone la restricción de forma global.** Mirar pares sueltos no alcanza: A-B y B-C pueden ser compatibles y A-C no. El coloreo considera todas las combinaciones a la vez y garantiza que ninguna canasta contiene una arista.
3. **$\chi(G)$ es un indicador del mercado.** La cantidad de canastas necesarias mide qué tan correlacionado está el mercado en una fecha de corte (sube en crisis), información que el modelo por sí solo no da.
4. **Hace que el modelo importe y permite evaluarlo.** Si cambia $\hat\rho$, cambian las aristas, el coloreo y las canastas. Se comparan los coloreos hechos con el modelo, con `corr_90d` y al azar, midiendo la correlación real del período de test dentro de cada canasta.

Las demás herramientas (polinomio cromático, complemento, Prim, nodos de quiebre) responden preguntas adicionales sobre el mismo grafo.

Nota para el informe: se podrían armar canastas sin grafos, por ejemplo con clustering sobre la matriz de correlaciones. El aporte del grafo es la restricción formal ("ninguna arista dentro de una canasta") y que la cantidad de canastas tenga una definición matemática, $\chi(G)$. Hay que justificarlo explícitamente.

### Modelo: grafo de conflicto

Es el mismo planteo del ejercicio de las peceras de la práctica de coloreo (ej. 12) y del de las sustancias químicas (ej. 13): hay elementos que **no pueden compartir contenedor** y se pide el mínimo de contenedores.

| Práctica | Nuestro problema |
|---|---|
| Peces (depredador-presa) | Acciones |
| Arista = no pueden estar juntos | Arista = correlación predicha > umbral $\theta$ |
| Pecera | Canasta |
| Mínimo de peceras | $\chi(G)$ = mínimo de canastas |

$G = (V, E)$ es un grafo simple, no dirigido y con pesos en las aristas ($w = \hat\rho$). El coloreo propio impone que dos acciones unidas por una arista queden en canastas distintas.

### Conceptos de clase que usamos

1. **Coloreo propio y número cromático $\chi(G)$.** Cada color es una canasta. El valor de $\chi(G)$ aparece en el frontend en función del umbral.
2. **Matriz de adyacencia y grado.** El grafo se guarda como matriz de adyacencia (la de `networkx` o la nuestra). El grado de cada vértice es la suma de su fila, y con él se ordenan los nodos para el greedy.
3. **Componentes conexas.** Se colorea cada componente por separado. Además $\chi(G) = \max_i \chi(G_i)$, y esto simplifica el algoritmo.
4. **Grafo completo $K_n$.** Con $\theta$ muy bajo el grafo se acerca a $K_{30}$, que tiene $\binom{30}{2} = 435$ aristas y necesita 30 canastas. Es el caso extremo para explicar el selector de umbral. Con $\theta$ muy alto no hay aristas y $\chi = 1$.
5. **Grafo bipartito.** Un grafo es bipartito si y solo si no tiene ciclos impares. Se usa el algoritmo de clase (asignar a $V_1$, vecinos a $V_2$, y así sucesivamente) como atajo. Si el grafo es bipartito, $\chi = 2$. Sirve también como **test de corrección**: el greedy tiene que devolver 2 colores en esos casos.
6. **Complemento.** Una canasta es un conjunto sin aristas entre sí, o sea una clique en el complemento $\bar G$. $\bar G$ une los pares poco correlacionados, es decir, los que conviene combinar. Se muestra como segunda vista en el frontend.
7. **Polinomio cromático $P(G,\lambda)$.** Responde: *con $k$ canastas, ¿de cuántas formas se pueden repartir las acciones sin que dos correlacionadas queden juntas?* Se cumple $P(G,k) > 0 \iff k \ge \chi(G)$. Se calcula por deleción-contracción (teorema de la diferencia de grafos) y por producto sobre las componentes conexas. Como el costo es exponencial, se aplica a subgrafos chicos o a valores chicos de $k$.

8. **Árbol recubridor mínimo (algoritmo de Prim).** Se aplica sobre la distancia $d = \sqrt{2(1-\rho)}$ y da una vista alternativa de cómo se agrupa el mercado. Se usa el algoritmo y la tabla de etiquetas vistos en clase.
9. **Nodos de quiebre.** Un vértice $v$ es nodo de quiebre si $k(G - v) > k(G)$. Se identifican con el método visto (eliminar el vértice y contar componentes) y señalan acciones que funcionan de puente entre grupos correlacionados.

### Algoritmo de coloreo y temas a investigar

El algoritmo para **construir** el coloreo es el coloreo greedy por grado:

- **Coloreo greedy por grado:** se ordenan los vértices por grado descendente y a cada uno se le asigna el menor color que no usa ninguno de sus vecinos ya coloreados. El resultado es siempre un coloreo propio, aunque puede usar más de $\chi(G)$ colores.
- **Verificación:** en grafos chicos se contrasta el número de colores del greedy con $\chi(G)$ obtenido a partir de $P(G,\lambda)$ (el menor $k$ con $P(G,k) > 0$), y en grafos bipartitos tiene que dar 2.

Temas que debemos investigar para poder trabajarlos con más profundidad:

- **Algoritmos de coloreo:** coloreo greedy y sus variantes de orden (Welsh-Powell, DSATUR), por qué es heurístico y cómo se compara con $\chi(G)$.
- **Cotas del número cromático:** relación entre $\chi(G)$, el grado máximo $\Delta(G)$ y las cliques del grafo.
- **Uso de los pesos:** cómo hacer que el peso $\hat\rho$ de las aristas influya en el coloreo (por ejemplo, para elegir entre colores válidos), más allá de definir qué aristas existen según el umbral.
- **Correlación de retornos y redes financieras:** cómo se mide la correlación entre acciones y cómo se usan los grafos (por ejemplo, el árbol recubridor mínimo sobre distancias de correlación) para estudiar mercados.

### Conexión con el modelo

Si el modelo cambia su predicción $\hat\rho$, cambian las aristas del grafo, y con ellas el coloreo, $\chi(G)$ y las canastas. Eso se ve en el frontend al variar umbral y fecha de corte. En épocas de crisis $\hat\rho$ sube, aparecen más aristas y hacen falta más canastas.

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


