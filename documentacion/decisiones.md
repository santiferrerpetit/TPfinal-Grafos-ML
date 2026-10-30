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
