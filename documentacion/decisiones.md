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

- **Decisión:** 30 acciones del S&P 500 más `^GSPC` como índice de mercado. Lista y criterio en [../ACCIONES.md](../ACCIONES.md).
- **Por qué:** cubre los 11 sectores y mezcla pares muy correlacionados con pares casi independientes, para que el modelo vea todo el rango de correlaciones.

## 4. Sectores

- **Decisión:** tabla propia `data/sectores.csv` armada a mano.
- **Por qué:** `yf.Ticker(t).info["sector"]` es lento y a veces falla; fijar la tabla da reproducibilidad.

## 5. Cálculo de features

- **Decisión:** beta con regresión rodante contra `^GSPC`; todas las features usan solo retornos con fecha ≤ `fecha_corte`. Solo `corr_futura_60d` usa los 60 días siguientes.
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
