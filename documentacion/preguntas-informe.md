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

## ¿Qué proporción se usa para train y test, y qué es el gap?

Es aproximadamente 70/30, pero por fechas de corte y no por filas al azar: el 30% de las fechas más recientes va a test y el resto a train. De las 111 fechas de corte, 75 van a train (32.625 filas, de 2014-12-30 a 2020-11-13), 33 a test (14.355 filas, de 2021-03-12 a 2023-09-27) y 3 se descartan.

Esas 3 fechas descartadas son el **gap** (2020-12-14, 2021-01-13 y 2021-02-11). Hacen falta porque el target de cada fila es la correlación de las 60 ruedas siguientes a la fecha de corte. El target del último corte de train llega hasta mediados de febrero de 2021, y si test empezara enseguida, train y test compartirían información de los mismos días (fuga de información). Los cortes están separados por 20 ruedas y el horizonte es de 60, así que el gap es `ceil(60 / 20) = 3` cortes (`GAP_CORTES` en `backend/app/modelo.py`). Es una elección conservadora: el mínimo para que los targets no se pisen es 2 cortes (con 0 se comparten 40 ruedas y con 1, 20), y con 3 el primer corte de test queda 20 ruedas después del último día del target de train. El notebook `02-split-y-baseline` lo comprueba con los datos reales.

Descartarlas cuesta el 2,7% de las filas (1.305 de 48.285) a cambio de que el resultado en test sea confiable. La validación temporal que se usa para elegir hiperparámetros dentro de train aplica la misma idea, con un gap entre el train y la validación de cada fold. Ver decisión 6 y el notebook `02-split-y-baseline`.

## ¿Qué modelos se comparan?

- **Baseline:** no se entrena. Predice que la correlación futura será igual a `corr_90d`, que es lo que hace hoy la plataforma. Es la vara que hay que superar.
- **Regresión lineal:** busca una fórmula del tipo `futura = a·corr_90d + b·corr_250d + c·mismo_sector + ...`. Simple y fácil de explicar.
- **KNN:** para predecir una fila busca las K filas de entrenamiento más parecidas y promedia su target.
- **Árbol de decisión:** aprende reglas del tipo "si `corr_90d` > 0,6 y `mismo_sector` = 1, predigo 0,75". Captura relaciones que no son una recta.

Se comparan con MAE (error absoluto promedio), RMSE (penaliza más los errores grandes) y R² (fracción de la variación que explica el modelo). Si ningún modelo le gana al baseline, también es un resultado válido y se explica en el informe.

## ¿Usamos un modelo preentrenado, como los que reconocen imágenes?

No. Un modelo preentrenado sirve para conocimientos generales (qué es una maleza en una foto), porque se entrenó con millones de ejemplos y lo único que se hace es usarlo. Nuestra tarea es específica: predecir la correlación a 60 días entre pares de estas 30 acciones con estas features, y no existe un modelo ya entrenado para eso. Además, los datos son una tabla chica de 7 columnas y unas 48 mil filas: para eso alcanzan los modelos simples, y uno grande memorizaría el pasado y fallaría en el futuro.

Lo que sí reutilizamos es la librería `scikit-learn`, que trae el método (`LinearRegression`, `KNeighborsRegressor`, `DecisionTreeRegressor`). Lo que el modelo aprende sale de nuestros datos con `.fit(X, y)`. El modelo no "entiende" las acciones: solo encuentra patrones numéricos. Ver decisión 19.

## ¿Qué predice el modelo y qué se hace con esa predicción?

Dado un par de acciones y una fecha de corte, el modelo predice la correlación que van a tener en los 60 días siguientes (`corr_futura_60d`, un número entre -1 y 1). Es una regresión, no una clasificación.

Esa predicción es la entrada del grafo:

1. Con 30 acciones hay 435 pares y el modelo predice la correlación de cada uno.
2. Se arma un grafo: nodo = acción, y arista entre dos acciones si la correlación predicha supera un umbral θ (se mueven juntas).
3. Se colorea el grafo con greedy por grado, de modo que dos acciones unidas por una arista no queden con el mismo color. Cada color es una canasta: un grupo de acciones que no se mueven juntas.
4. La cantidad de colores necesarios, χ(G), mide qué tan correlacionado está el mercado. Sube en las crisis.

Es el mismo planteo del ejercicio de las peceras de la práctica: los peces depredador-presa no pueden compartir pecera, y las acciones correlacionadas no pueden compartir canasta.

## ¿Para qué serviría en la práctica?

Para armar una cartera que no caiga toda junta. Si alguien compra AAPL, MSFT y NVDA parece diversificado (tres empresas), pero las tres se mueven casi igual: si el sector tech cae, pierde en las tres a la vez. La diversificación era falsa.

El sistema indica qué acciones forman una canasta en la que ninguna se mueve junto con otra. Armar la cartera con una canasta, o repartiendo entre canastas, reduce el riesgo de que todo caiga a la vez.

¿Por qué predecir en lugar de usar la correlación histórica? Porque la histórica mira el pasado, y en una crisis las correlaciones suben justo cuando más se necesita diversificar. Si el modelo anticipa eso mejor, las canastas aguantan más cuando importa.

El sistema entrega:

- **Canastas:** qué acciones juntar para diversificar.
- **χ(G) como termómetro:** si de golpe hacen falta más canastas, el mercado se está volviendo más correlacionado, o sea, hay más riesgo sistémico.
- **Selector de umbral:** qué tan estricto se es. Umbral bajo da más canastas y más puras. Umbral alto da menos canastas y más laxas.

## ¿Cómo se evalúa si el sistema sirve?

Se arman canastas con tres métodos: con el modelo, con la correlación histórica (`corr_90d`) y al azar. Después se mide la correlación real del período de test dentro de cada canasta. Si las canastas del modelo tienen menos correlación interna, el modelo agrega valor.

## ¿Qué pasa con un umbral θ muy bajo o muy alto?

θ decide cuándo dos acciones "se llevan mal": hay arista si su correlación supera θ. El selector de la app va de -0,2 a 1, y en los extremos el resultado deja de ser útil:

- **θ muy bajo (-0,2):** casi todos los pares superan el umbral, así que el grafo es casi completo y hacen falta casi 30 canastas, una por acción. Se diversifica perfecto, pero no se agrupa nada. El complemento queda casi vacío.
- **θ muy alto (1):** ninguna correlación supera 1, así que no hay aristas y alcanza con una sola canasta con las 30 acciones. No hay diversificación: la correlación real dentro de la canasta es la del mercado entero (unos 0,28, parecido a armar canastas al azar). El complemento es el grafo completo.

Lo útil está en el medio, donde el grafo tiene estructura. Con el modelo y la fecha 2023-09-27: θ = 0,25 da 300 aristas y 15 canastas, θ = 0,39 da 99 aristas y 7 canastas, y θ = 0,5 da 10 aristas y 3 canastas. La pestaña "Canastas según θ" muestra esa curva completa.

Efecto en los demás extras:

- **Árbol mínimo:** no cambia, porque se calcula sobre todos los pares con d = √(2(1-ρ)) y no usa θ.
- **Nodos de quiebre:** casi no aparecen en los extremos. Con θ bajo el grafo es tan denso que sacar un nodo no lo desconecta, y con θ alto casi no hay aristas. Con θ = 0,39 aparecieron JNJ y PG.
- **Polinomio cromático:** con θ bajo la componente tiene cientos de aristas y el cálculo exponencial se rechaza (tope de 20 aristas). Con θ alto es trivial: una acción aislada da P = λ.

Además, el modelo predice correlaciones más comprimidas hacia la media que la histórica, así que su grafo se vacía antes al subir θ: con θ = 0,6 tiene en promedio 9 aristas y la histórica 33. Por eso, a igual θ, el modelo usa menos canastas y la comparación no es del todo justa (ver decisión 26).

## ¿Qué pasa en una fecha de crisis?

En una crisis las acciones se mueven todas juntas y las correlaciones suben. Con el mismo θ, el grafo tiene muchas más aristas y hacen falta más canastas. Datos del período de test con θ = 0,5, separando las fechas por la volatilidad del mercado (se llama "crisis" a la que supera 0,0113, el mismo umbral que usa el análisis por segmento del modelo):

| | Calma | Crisis |
|---|---|---|
| Volatilidad del mercado | 0,008 | 0,015 |
| Correlación promedio histórica (`corr_90d`) | 0,22 | 0,38 |
| Aristas con la histórica | 41 | 124 |
| Canastas con la histórica | 5,4 | 9,2 |
| Aristas con el modelo | 15 | 15 |
| Canastas con el modelo | 3,5 | 3,0 |

En el test las fechas de crisis van de mayo de 2022 a febrero de 2023, y el pico es agosto de 2022 con 134 aristas y 10 canastas con la histórica. Diversificar se vuelve más difícil: hay menos pares que se muevan por separado, y la correlación real dentro de las canastas también sube (hasta unos 0,5 en 2022, incluso con canastas al azar). χ(G) funciona como termómetro del riesgo sistémico.

Hallazgo importante: **el modelo casi no reacciona a la crisis.** Sigue prediciendo unas 15 aristas y 3 canastas, igual que en calma, mientras que la histórica sí detecta el salto. Sus predicciones quedan muy comprimidas hacia la media y no captan el cambio, aunque `volatilidad_mercado` es una de sus features. Coincide con que en la evaluación de canastas la histórica le gana al modelo (ver decisión 26), y en crisis la diferencia es mayor. Hay que decirlo en el informe como un límite del modelo y una línea de mejora.

Límite de los datos: el test empieza en 2021, así que la crisis más fuerte del dataset, la de COVID de marzo de 2020 (volatilidad 0,03 y correlación histórica de 0,68), quedó en entrenamiento y la app no la muestra. Mostrarla no serviría para evaluar, porque ahí el modelo ya vio el resultado.

## ¿Cuáles son los límites del sistema?

- Es un trabajo académico, no asesoramiento financiero.
- Diversificar por correlación reduce el riesgo, no garantiza ganancias.
- Con 30 acciones y datos de Yahoo es una demostración del método, no un producto listo para invertir.
- El aporte práctico depende de que el modelo le gane al baseline de `corr_90d`. Si no le gana, el aporte sería casi nulo, y eso también es un resultado válido para el informe.

## ¿De dónde salen los datos y se puede usar yfinance?

Los precios salen de Yahoo Finance con `yfinance`, una librería de código abierto que usa los endpoints públicos de Yahoo. No es una API oficial ni está afiliada a Yahoo, y su documentación indica uso personal o educativo. La descarga se hizo una sola vez y se guardó en `data/precios.csv`, para que el resultado no dependa de que Yahoo siga disponible. Ver decisiones 2 y 12.

## ¿Cómo se regenera todo?

Desde `backend/` con el entorno virtual activado:

```bash
python scripts/descargar_precios.py     # data/precios.csv
python -m scripts.construir_dataset     # data/dataset_pares.csv
pytest                                   # tests, incluido el de leakage
```
