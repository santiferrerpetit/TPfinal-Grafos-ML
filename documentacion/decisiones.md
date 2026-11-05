# Decisiones

Formato: una entrada por decisión, la más nueva abajo. Si una decisión se revierte, no se borra: se agrega una entrada nueva que la reemplaza.

## 1. Stack tecnológico

- **Decisión:** backend en FastAPI con scikit-learn, pandas y networkx; frontend en Vite + React + TypeScript.
- **Por qué:** Python tiene todo el ecosistema de datos y modelos, y FastAPI expone el resultado al frontend con poco código.

## 2. Fuente y almacenamiento de datos

- **Decisión:** precios diarios de `yfinance`, descargados una sola vez y guardados en `data/precios.csv`.
- **Por qué:** el resultado no depende de que Yahoo siga disponible ni de que cambie su formato.
- **Nota:** `yfinance` no es una API oficial y su uso es personal o educativo. Se cita en el informe.

## 3. Universo de acciones

- **Decisión:** 30 acciones del S&P 500 más `SPY` como referencia de mercado. Lista y criterio en [ACCIONES.md](ACCIONES.md).
- **Por qué:** cubre los 11 sectores y mezcla pares muy correlacionados con pares casi independientes, para que el modelo vea todo el rango de correlaciones.

## 4. Sectores

- **Decisión:** tabla propia `data/sectores.csv` armada a mano.
- **Por qué:** `yf.Ticker(t).info["sector"]` es lento y a veces falla; fijar la tabla da reproducibilidad.

## 5. Cálculo de features

- **Decisión:** beta con regresión rodante contra `SPY`; todas las features usan solo retornos con fecha ≤ `fecha_corte`. Solo `corr_futura_60d` usa los 60 días siguientes.
- **Por qué:** el `beta` de `.info` es un valor actual y usarlo en fechas pasadas filtraría información del futuro.

## 6. Evaluación del modelo

- **Decisión:** split temporal (entrenar con el pasado, testear con el futuro). Modelos: regresión lineal, KNN y árbol de decisión, contra un baseline que usa `corr_90d`. Métricas: MAE, RMSE, R².
- **Por qué:** un split aleatorio mezclaría información del futuro en el entrenamiento y daría métricas optimistas.

## 7. Grafo y coloreo

- **Decisión:** grafo simple, no dirigido, con arista si la correlación predicha supera el umbral θ y peso igual a la correlación predicha. Coloreo greedy ordenando por grado descendente, por componente conexa. Los algoritmos de grafos se implementan a mano.
- **Por qué:** es el planteo de grafo de conflicto de la práctica (peceras). La materia pide implementar los algoritmos, y `networkx` se usa solo para contrastar en los tests.

## 8. Evaluación del coloreo

- **Decisión:** comparar canastas armadas con el modelo, con `corr_90d` y al azar, midiendo la correlación real del período de test dentro de cada canasta.
- **Por qué:** es lo que muestra si el modelo agrega valor sobre usar la correlación histórica.

## 9. Archivos de Claude fuera del repositorio

- **Decisión:** `CLAUDE.md` y `.claude/` están en `.gitignore`. Los documentos del proyecto (como esta carpeta) sí se suben.
- **Por qué:** son archivos de trabajo personales, no parte de la entrega.

## 10. Índice de mercado para el beta (reemplazada por la 11)

- **Decisión:** usar `^GSPC` (S&P 500) como índice de mercado para calcular el beta de cada acción y la `volatilidad_mercado`.
- **Por qué:** el beta es la pendiente de regresar los retornos de la acción contra los del mercado, y el S&P 500 es el estándar. Las 30 acciones son del S&P 500, así que el índice las representa bien.
- **Cómo:** se descarga junto con las acciones y se alinean las fechas. El beta es rodante y usa solo retornos con fecha ≤ `fecha_corte` (ver decisión 5).

## 11. SPY en lugar de ^GSPC

- **Decisión:** usar `SPY` (ETF que replica el S&P 500) como referencia de mercado para el beta y la `volatilidad_mercado`. Reemplaza a `^GSPC` de la decisión 10; las decisiones 3 y 5 ya están actualizadas.
- **Por qué:** es un instrumento más conocido para el equipo. Los retornos de `SPY` y de `^GSPC` son prácticamente idénticos (correlación mayor a 0,99), así que el beta y la volatilidad casi no cambian.
- **Nota:** con `auto_adjust=True` el precio de `SPY` incluye dividendos, mientras que `^GSPC` es solo de precio. La diferencia es pequeña y no afecta el uso que le damos.

## 12. Período y campos descargados

- **Decisión:** descargar del 2014-01-01 al 2024-01-01 (2516 días hábiles, 2014-01-02 a 2023-12-29) y guardar solo el precio de cierre ajustado (`Close` con `auto_adjust=True`). El script es `backend/scripts/descargar_precios.py`.
- **Por qué:** 10 años alcanzan para tener unas 50 mil filas en el dataset por pares y cubren varios regímenes de mercado (2015-16, 2018, 2020). El cierre ajustado incluye splits y dividendos, y las features solo necesitan retornos de cierre, así que `Open/High/Low/Volume` no se usan.
- **Nota:** las 31 series (30 acciones y `SPY`) no tienen valores faltantes. El período se cambia en las constantes `INICIO` y `FIN` del script.

## 13. Retornos y estructura del dataset por pares

- **Decisión:** trabajar con retornos diarios (variación porcentual del cierre) y no con precios. El dataset tiene una fila por par de acciones y fecha de corte. Cada par aparece una sola vez, con `accion_id_1` menor que `accion_id_2` en orden alfabético.
- **Por qué:** la correlación se mide sobre cuánto se mueve cada acción y no sobre su nivel de precio. Fijar el orden evita que el mismo par aparezca duplicado (AAPL-MSFT y MSFT-AAPL).
- **Cómo:** con 30 acciones hay 435 pares. El archivo es `data/dataset_pares.csv`.

## 14. Sin leakage en las features

- **Decisión:** `corr_30d`, `corr_90d`, `corr_250d`, `dif_volatilidad`, `dif_beta` y `volatilidad_mercado` usan solo retornos con fecha ≤ `fecha_corte`. Solo `corr_futura_60d` usa los 60 días hábiles siguientes. Un test unitario lo verifica: cambia los precios posteriores al corte y comprueba que las features no se modifican y que el target sí.
- **Por qué:** si una feature viera datos posteriores al corte, el modelo parecería bueno en entrenamiento y fallaría en uso real, donde esos datos no existen. Es el error más común al armar un dataset de series de tiempo.
- **Nota:** profundiza la decisión 5.

## 15. Ventana de 90 días para volatilidad y beta

- **Decisión:** la volatilidad (desvío estándar de los retornos), la beta (covarianza con `SPY` dividida por la varianza de `SPY`) y la `volatilidad_mercado` se calculan sobre los 90 días hábiles anteriores al corte.
- **Por qué:** 90 días (unos 4 meses) es un punto medio. Con 30 días las estimaciones son muy ruidosas, y con 250 reaccionan lento a los cambios de régimen. Coincide con la ventana de `corr_90d`, que es el baseline del modelo.
- **Nota:** es una elección nuestra y no viene de la consigna. Otras ventanas serían defendibles.

## 16. Diferencias en valor absoluto

- **Decisión:** `dif_volatilidad` y `dif_beta` son el valor absoluto de la diferencia entre las dos acciones del par.
- **Por qué:** mide qué tan distintas son sin depender del orden. Dos acciones con volatilidad muy distinta tienden a moverse menos juntas, sin importar cuál de las dos es la más volátil.

## 17. Fechas de corte y filas descartadas

- **Decisión:** una fecha de corte cada 20 días hábiles (aproximadamente un mes). Se descartan los cortes sin 250 días de historia previa y los cortes sin 60 días hábiles posteriores.
- **Por qué:** con un corte por día las ventanas se superponen casi por completo, y el dataset tendría filas casi idénticas sin aportar información nueva. Los primeros cortes no pueden calcular `corr_250d` y los últimos no pueden calcular el target.

## 18. Features del modelo

- **Decisión:** el modelo usa como entrada `corr_30d`, `corr_90d`, `corr_250d`, `mismo_sector`, `dif_volatilidad`, `dif_beta` y `volatilidad_mercado`. No usa `accion_id_1`, `accion_id_2` ni `fecha_corte`, y el target es `corr_futura_60d`.
- **Por qué:** los ids y la fecha identifican la fila, pero no describen cómo se comporta el par. Con los ids el modelo podría memorizar pares puntuales en lugar de aprender una relación general, y con la fecha no podría generalizar a períodos futuros.

## 19. Modelos entrenados con nuestros datos

- **Decisión:** usar los algoritmos de `scikit-learn` (`LinearRegression`, `KNeighborsRegressor`, `DecisionTreeRegressor`) y entrenarlos con nuestro dataset, en vez de modelos preentrenados.
- **Por qué:** la tarea es específica (correlación a 60 días entre pares de estas 30 acciones, con estas features) y no existe un modelo ya entrenado para ella. Además la consigna pide comparar estos tres modelos contra el baseline `corr_90d`. Con una tabla de 7 columnas y unas 48 mil filas, los modelos simples alcanzan y uno grande se sobreajustaría.

## 20. Split temporal con gap y validación temporal

- **Decisión:** el 30 % final de las fechas de corte es test; antes de test se descartan 3 fechas de corte (60 días hábiles = `HORIZONTE`). Los hiperparámetros se eligen con 4 folds de ventana expansiva sobre train, también con ese gap, usando MAE. Código en `backend/app/modelo.py`.
- **Por qué:** el target de un corte mira 60 días adelante; sin gap, el target del último corte de train se solaparía con el período de test. Elegir hiperparámetros en train (no en test) evita ajustar al test.
- **Resultado:** train 2014-12-30 a 2020-11-13, test 2021-03-12 a 2023-09-27.

## 21. Modelo elegido y resultado frente al baseline

- **Decisión:** el modelo guardado en `data/modelo.joblib` es el de menor MAE en validación temporal (hoy KNN, k=1000). Métricas en `data/metricas.json`, gráficos en `informe/figuras/`; se regeneran con `python -m scripts.entrenar_modelo`.
- **Resultado en test (MAE / R²):** baseline 0,161 / 0,21; regresión lineal 0,156 / 0,29; KNN 0,161 / 0,25; árbol 0,201 / -0,16. La mejora sobre el baseline es chica y la regresión lineal gana en test aunque KNN gana en validación.
- **Por qué importa:** `corr_90d` ya es un predictor fuerte, así que el aporte de las otras features es modesto. El informe tiene que decirlo con esos números y no vender el modelo como mucho mejor.
- **Crisis vs calma:** "crisis" = `volatilidad_mercado` sobre el percentil 75 de train. En crisis ningún modelo le gana al baseline; en calma la regresión lineal sí.

## 22. Construcción del grafo de conflicto

- **Fecha:** 2026-11-05.
- **Decisión:** el módulo `backend/app/grafos/construccion.py` arma el grafo dada una fecha de corte, un umbral θ y una fuente de pesos. Nodos = acciones; arista entre `i` y `j` si ρ(i,j) **>** θ (desigualdad estricta); peso de la arista = ρ(i,j). Tests en `backend/tests/test_construccion_grafo.py`.
- **Representación:** la clase `GrafoConflicto` guarda dos matrices n×n con `numpy`:
  - `pesos`: ρ de todos los pares, simétrica, diagonal en 0.
  - `adyacencia`: 0/1, sale de `pesos > θ`, simétrica, diagonal en 0 (grafo simple, sin lazos).

  El grado de un nodo es la suma de su fila (`grado()`), que es lo que necesita el greedy por grado. `a_networkx()` devuelve el mismo grafo como `nx.Graph` con atributo `weight`, para dibujarlo y para contrastar nuestros algoritmos en los tests.
- **Por qué matriz de adyacencia y no listas:** es la representación de clase, con 30 nodos el tamaño no importa, y el grado, el complemento (`1 - A` sin la diagonal) y la lectura de pesos son operaciones directas sobre la matriz. `networkx` queda solo como adaptador, ya que los algoritmos se implementan a mano (decisión 7).
- **Por qué `pesos` completa y `adyacencia` aparte:** cambiar θ solo cambia `adyacencia`, no hace falta recalcular nada. Además la evaluación de las canastas necesita ρ de pares que **no** son arista. Y como θ puede ser negativo, un peso 0 no sirve para marcar "no hay arista"; por eso la adyacencia no se deduce de `pesos != 0`.
- **Fuentes de pesos intercambiables** (parámetro `fuente`):
  - `"modelo"`: usa la columna `corr_predicha` del dataset. La agrega el paso del modelo; hasta que exista, el módulo solo exige que la columna esté.
  - `"corr_90d"`: usa la columna `corr_90d` (la línea base).
  - `"azar"`: ρ uniforme en [-1, 1] con semilla fija (`semilla`), ignora los datos. Es el piso de comparación y es reproducible.

  Las tres devuelven el mismo tipo de objeto, así que el coloreo y la evaluación no saben de dónde vinieron los pesos. Comparar fuentes es cambiar un string.
- **Casos borde:** un par sin dato (falta la fila o ρ es NaN) no es arista, porque `NaN > θ` es falso. Si la fecha de corte no existe, la fuente es desconocida o falta la columna, se lanza `ValueError` con un mensaje claro.
- **Limitación conocida:** con `"azar"` la cantidad de aristas depende solo de θ (cerca de (1-θ)/2 de los pares), mientras que con el modelo depende de las correlaciones reales, que son casi todas positivas. A igual θ el azar tendrá un grafo con densidad distinta. Si en la comparación eso molesta, una alternativa es permutar al azar los ρ del modelo (misma distribución, pares mezclados); queda para decidir cuando se evalúe el coloreo.
- **Uso de IA:** esta pieza se hizo con Claude (diseño de la clase, código y tests); registrar en el informe.

## 23. Coloreo greedy por grado y variantes

- **Fecha:** 2026-11-05.
- **Decisión:** `backend/app/grafos/coloreo.py` implementa a mano el coloreo greedy: se ordenan los nodos por grado descendente y cada uno recibe el menor color que no usa ningún vecino ya coloreado. Se colorea cada componente conexa por separado. Las funciones reciben la matriz de adyacencia y devuelven una lista `colores` (índice de nodo → color); cada color es una canasta (`canastas()` las agrupa). `es_coloreo_propio()` y `aristas_monocromaticas()` validan que ninguna arista tenga sus dos extremos del mismo color. Tests en `backend/tests/test_coloreo.py`.
- **Desempate:** entre nodos del mismo grado gana el de menor índice (orden alfabético de ticker), para que el resultado sea determinista. Los pesos ρ no se usan todavía en el coloreo (queda como tema a investigar de la propuesta).
- **Por componente:** como las componentes no comparten aristas, colorearlas por separado da el mismo resultado que hacerlo todo junto; sirve para mostrar que χ(G) = máx χ(componentes) y para que cada componente reutilice los colores desde 0.
- **Welsh-Powell:** es el mismo algoritmo (orden por grado descendente). La versión clásica arma el color 0 completo, después el 1, etc., pero da exactamente el mismo coloreo que el secuencial. Lo comprobamos en un test sobre 30 grafos al azar, en vez de implementarlo dos veces.
- **DSATUR (opcional):** implementado para comparar. Colorea siempre el nodo con más colores distintos entre sus vecinos (saturación), desempatando por grado. Es exacto en grafos bipartitos (usa 2 colores).
- **Hallazgo importante: el greedy por grado NO garantiza 2 colores en un bipartito.** Es una heurística: siempre da un coloreo propio, pero puede usar más de χ(G). Ejemplo en el test: grafo corona de 8 nodos (bipartito, todos de grado 3) con los nodos intercalados: el greedy usa 4 colores y DSATUR 2. Los tests de "bipartito ⇒ 2 colores" valen para casos concretos (caminos, ciclos pares, K_{m,n}, estrellas) y no como propiedad general. En el informe hay que decirlo; para el chequeo exacto en bipartitos se usa el algoritmo de clase o DSATUR.
- **Tests:** sin aristas ⇒ 1 color; K_n ⇒ n colores (n = 1, 2, 3, 5, 8, 30); ciclo impar ⇒ 3; χ = máx de las componentes; el coloreo es siempre propio y usa a lo sumo Δ+1 colores en grafos al azar; nunca usa menos colores que la clique máxima (calculada con `networkx`).
- **Pendiente:** contrastar con χ por polinomio cromático en grafos chicos (todavía no implementado).
- **Uso de IA:** diseño, código y tests hechos con Claude; registrar en el informe.
- **Comparación de variantes (agregado):** `python -m scripts.comparar_coloreos` (desde `backend/`) genera [comparacion_coloreo.md](comparacion_coloreo.md). Resumen: DSATUR usa casi siempre igual o menos colores que el greedy por grado; en bipartitos al azar el greedy usa más de 2 colores en 27% a 68% de los casos y DSATUR en ninguno; sobre los datos reales con `corr_90d` la diferencia es mínima (7,69 vs 7,64 canastas con θ = 0,5). Por eso mantenemos el greedy por grado como algoritmo principal (es el que pide la materia) y DSATUR como comparación.
