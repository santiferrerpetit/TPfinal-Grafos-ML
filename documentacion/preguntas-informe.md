# Preguntas y respuestas para el informe

Explicaciones en lenguaje simple de las preguntas que surgieron al armar el proyecto. Sirven de borrador para el informe y la defensa oral. Las decisiones formales están en [decisiones.md](decisiones.md).

## ¿Qué es un retorno y por qué se trabaja con retornos y no con precios?

El retorno es cuánto subió o bajó una acción de un día al siguiente, en porcentaje (`precio_hoy / precio_ayer - 1`). Se usa en lugar del precio porque la correlación debe medir cómo se mueven las acciones y no su nivel: una acción de 500 dólares y una de 20 pueden moverse igual. Ver decisión 13.

## ¿Qué es la correlación?

Un número entre -1 y 1 que indica qué tan parecido se mueven dos acciones. Cerca de 1, suben y bajan juntas. Cerca de 0, no tienen relación. Negativa, se mueven al revés. Se calcula sobre los retornos de una ventana de días.

## ¿Qué es la fecha de corte?

El "hoy" desde el cual se mira. Lo que pasó hasta esa fecha (inclusive) se considera conocido y alimenta las features. Lo que pasa después es el futuro que el modelo intenta predecir.

## ¿Cómo se arman los pares?

Con 30 acciones hay 30 × 29 / 2 = 435 pares, tomando cada combinación de dos acciones distintas una sola vez. Se ordenan alfabéticamente para que `accion_id_1 < accion_id_2` y el mismo par no aparezca duplicado (AAPL-MSFT y MSFT-AAPL). Cada par se cruza con cada fecha de corte. En `backend/app/dataset.py` se hace con `itertools.combinations`.

## ¿Cuántas filas tiene el dataset y por qué?

48 285 filas: 435 pares × 111 fechas de corte. Hay un corte cada 20 días hábiles (aproximadamente un mes), desde 2014-12-30 hasta 2023-09-27. Con un corte por día las ventanas se superponen casi por completo y las filas serían casi copias. Ver decisión 17.

## ¿Por qué los primeros y los últimos cortes no están?

El primer corte necesita 250 retornos de historia para calcular `corr_250d`, y por eso empieza a fines de 2014. El último necesita 60 retornos posteriores para calcular el target, y por eso termina en septiembre de 2023. Las fechas sin una de las dos cosas se descartan.

## ¿Qué significa cada columna?

- `corr_30d`, `corr_90d`, `corr_250d`: correlación de los últimos 30, 90 y 250 días hábiles. Tres ventanas para ver el comportamiento reciente y el de largo plazo.
- `mismo_sector`: 1 si las dos acciones son del mismo sector, 0 si no.
- `dif_volatilidad`: diferencia (en valor absoluto) entre las volatilidades de las dos acciones. La volatilidad es el desvío estándar de los retornos, es decir cuánto se agita la acción.
- `dif_beta`: diferencia (en valor absoluto) entre las betas. La beta mide qué tan sensible es una acción al mercado: beta 1 se mueve como el mercado, beta 2 exagera el movimiento y beta 0,5 lo amortigua. Se calcula como covarianza con `SPY` dividida por la varianza de `SPY`.
- `volatilidad_mercado`: volatilidad de `SPY` en los 90 días previos. En las crisis las correlaciones suben, y esta columna le dice al modelo en qué clima está el mercado.
- `corr_futura_60d`: correlación de los 60 días hábiles siguientes al corte. Es lo que el modelo tiene que predecir.

## ¿Qué es el leakage y cómo lo evitamos?

Leakage (filtración) es cuando una feature usa por error información del futuro. El modelo parecería muy bueno en entrenamiento, pero en uso real no tendría esos datos y fallaría. Para evitarlo, todas las features usan solo retornos con fecha ≤ `fecha_corte`, y solo `corr_futura_60d` mira hacia adelante.

Lo verifica el test `test_features_no_usan_datos_posteriores_al_corte` de `backend/tests/test_dataset.py`: altera todos los precios posteriores a un corte y comprueba que las features de ese corte y de los anteriores no cambian, mientras que el target del propio corte sí cambia. Se comprobó también que el test falla si se introduce una fuga a propósito. Ver decisión 14.

## ¿Por qué ventana de 90 días para volatilidad y beta?

Es un punto medio. Con 30 días las estimaciones son muy ruidosas y con 250 reaccionan lento a los cambios de régimen. Además coincide con `corr_90d`, que es el baseline. Es una elección nuestra y otras ventanas serían defendibles. Ver decisión 15.

## ¿Por qué valor absoluto en las diferencias?

Para el par AAPL-MSFT, "AAPL menos MSFT" y "MSFT menos AAPL" darían signos opuestos para el mismo par. Con el valor absoluto se mide qué tan distintas son, sin depender del orden. Ver decisión 16.

## ¿Cómo se entrena el modelo con este dataset?

Es una regresión supervisada. El modelo recibe las features (X) y tiene que acertar el target (y):

- **X:** `corr_30d`, `corr_90d`, `corr_250d`, `mismo_sector`, `dif_volatilidad`, `dif_beta`, `volatilidad_mercado`.
- **y:** `corr_futura_60d`.

Los ids de las acciones y la fecha no entran como features: identifican la fila, pero no describen el comportamiento del par. Ver decisión 18.

## ¿Por qué el split es por tiempo y no al azar?

Se entrena con el pasado (por ejemplo 2014 a 2020) y se testea con el futuro (2021 a 2023). Con un split al azar, un corte del 15 de marzo caería en entrenamiento y uno del 20 de abril en test, y comparten casi los mismos días de datos. Eso infla las métricas. El split temporal simula el uso real: predecir un futuro que el modelo no vio. Ver decisión 6.

## ¿Qué modelos se comparan?

- **Baseline:** no se entrena. Predice que la correlación futura será igual a `corr_90d`, que es lo que hace hoy la plataforma. Es la vara que hay que superar.
- **Regresión lineal:** busca una fórmula del tipo `futura = a·corr_90d + b·corr_250d + c·mismo_sector + ...`. Simple y fácil de explicar.
- **KNN:** para predecir una fila busca las K filas de entrenamiento más parecidas y promedia su target.
- **Árbol de decisión:** aprende reglas del tipo "si `corr_90d` > 0,6 y `mismo_sector` = 1, predigo 0,75". Captura relaciones que no son una recta.

Se comparan con MAE (error absoluto promedio), RMSE (penaliza más los errores grandes) y R² (fracción de la variación que explica el modelo). Si ningún modelo le gana al baseline, también es un resultado válido y se explica en el informe.

## ¿Usamos un modelo preentrenado, como los que reconocen imágenes?

No. Un modelo preentrenado sirve para conocimientos generales (qué es una maleza en una foto), porque se entrenó con millones de ejemplos y lo único que se hace es usarlo. Nuestra tarea es específica: predecir la correlación a 60 días entre pares de estas 30 acciones con estas features, y no existe un modelo ya entrenado para eso. Además, los datos son una tabla chica de 7 columnas y unas 48 mil filas: para eso alcanzan los modelos simples, y uno grande memorizaría el pasado y fallaría en el futuro.

Lo que sí reutilizamos es la librería `scikit-learn`, que trae el método (`LinearRegression`, `KNeighborsRegressor`, `DecisionTreeRegressor`). Lo que el modelo aprende sale de nuestros datos con `.fit(X, y)`. El modelo no "entiende" las acciones: solo encuentra patrones numéricos. Ver decisión 19.

## ¿De dónde salen los datos y se puede usar yfinance?

Los precios salen de Yahoo Finance con `yfinance`, una librería de código abierto que usa los endpoints públicos de Yahoo. No es una API oficial ni está afiliada a Yahoo, y su documentación indica uso personal o educativo. La descarga se hizo una sola vez y se guardó en `data/precios.csv`, para que el resultado no dependa de que Yahoo siga disponible. Ver decisiones 2 y 12.

## ¿Cómo se regenera todo?

Desde `backend/` con el entorno virtual activado:

```bash
python scripts/descargar_precios.py     # data/precios.csv
python -m scripts.construir_dataset     # data/dataset_pares.csv
pytest                                   # tests, incluido el de leakage
```
