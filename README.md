# Diversificación de carteras con predicción de correlaciones

TP integrador de Lógica y Teoría de Grafos. Un modelo de regresión predice la correlación futura (60 días) entre pares de acciones y un coloreo de grafos agrupa las acciones en canastas que no se mueven juntas.

- Descripción completa del problema y del diseño: [PROPUESTA.md](PROPUESTA.md).
- Informe: [informe/informe.md](informe/informe.md).
- Decisiones de diseño y su justificación: [documentacion/decisiones.md](documentacion/decisiones.md).

## Estructura

```
backend/        API (FastAPI), modelo (scikit-learn) y algoritmos de grafos
frontend/       Aplicación web (Vite + React + TypeScript + Tailwind + shadcn/ui)
data/           precios.csv, sectores.csv, dataset por pares y resultados de evaluación
notebooks/      dataset, partición temporal, modelos y análisis de errores
documentacion/  decisiones, explicaciones para el informe y comparaciones
informe/        informe del trabajo y sus figuras
```

## Requisitos

- Python 3.12 o superior (probado con 3.14)
- Node.js 20 o superior (probado con 24)

## Instalación y ejecución

Hay que levantar dos procesos, uno para el backend y otro para el frontend, cada uno en su terminal.

### 1. Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**Antes de levantar la API hay que generar el modelo** (una sola vez, unos 15 segundos). `data/modelo.joblib` no se versiona, y sin él los endpoints que usan el modelo (`/grafo`, `/canastas`, etc.) fallan:

```bash
python -m scripts.entrenar_modelo
```

Después:

```bash
uvicorn app.main:app --reload
```

API en http://localhost:8000 (documentación interactiva en `/docs`, chequeo en `/health`).

Tests (el de la API necesita el modelo generado):

```bash
pytest
```

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Aplicación en http://localhost:5173. Espera el backend en http://localhost:8000 (se puede cambiar con la variable `VITE_API_URL`). La API solo acepta pedidos desde ese origen (CORS), así que el frontend tiene que correr en el puerto 5173.

## API

| Endpoint | Qué devuelve |
|---|---|
| `GET /fechas` | Fechas de corte disponibles |
| `GET /grafo?fecha&umbral&fuente` | Nodos con su canasta, aristas con peso y número de canastas |
| `GET /canastas?fecha&umbral&fuente` | Canastas con sus acciones y su correlación real posterior promedio |
| `GET /chi-por-umbral?fecha&fuente` | Canastas y aristas para una grilla de umbrales |
| `GET /comparacion?umbral[&fecha]` | Modelo vs. `corr_90d` vs. azar, medidos con la correlación real de test |
| `GET /complemento`, `/prim`, `/nodos-quiebre`, `/polinomio` | Herramientas de grafos de la materia |
| `GET /acciones`, `/precios/{ticker}` | Datos de las acciones para el frontend |
| `GET /metricas` | Métricas del modelo en test |

`fuente` puede ser `modelo` (correlación predicha), `corr_90d` (correlación histórica) o `azar`. `/polinomio` pide `acciones=AAPL,MSFT,...` porque su costo es exponencial (máximo 20 aristas).

## Datos y cómo regenerar todo

Precios diarios descargados una sola vez con `yfinance` y guardados en `data/precios.csv`, para que el resultado no dependa de Yahoo Finance. `yfinance` no es una API oficial de Yahoo y su uso es personal o educativo.

`data/precios.csv` tiene el precio de cierre ajustado (`auto_adjust=True`, incluye splits y dividendos) de las 30 acciones de `data/sectores.csv` y de `SPY`, del 2014-01-02 al 2023-12-29.

`data/dataset_pares.csv` tiene una fila por par de acciones y fecha de corte (435 pares, un corte cada 20 días hábiles, 48 285 filas), con las features y el target `corr_futura_60d`.

Todos los archivos del repositorio se pueden regenerar, en este orden, desde `backend/` con el entorno virtual activado:

```bash
python scripts/descargar_precios.py     # data/precios.csv (necesita internet)
python -m scripts.construir_dataset     # data/dataset_pares.csv
python -m scripts.entrenar_modelo       # data/modelo.joblib, data/metricas.json, informe/figuras/
python -m scripts.evaluar_canastas      # data/evaluacion_canastas.csv, documentacion/evaluacion_canastas.md
python -m scripts.comparar_coloreos     # documentacion/comparacion_coloreo.md
```

El entrenamiento es reproducible: volver a correrlo da las mismas métricas. El primer paso es el único que depende de Yahoo Finance; no hace falta repetirlo, porque `data/precios.csv` ya está en el repositorio.

## Notebooks

En `notebooks/` hay cuatro notebooks que reproducen paso a paso el dataset, la partición temporal, los modelos y el análisis de errores. Importan el código de `backend/app`, así que no duplican lógica. Para abrirlos hacen falta `jupyterlab` e `ipykernel`, que no están en `requirements.txt`:

```bash
cd backend && source venv/bin/activate
pip install jupyterlab ipykernel
cd ../notebooks && jupyter lab
```

## Uso de IA

Ver la sección correspondiente del informe.
