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
