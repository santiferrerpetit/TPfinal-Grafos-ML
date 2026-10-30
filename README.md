# Diversificación de carteras con predicción de correlaciones

TP integrador de Lógica y Teoría de Grafos. Un modelo de regresión predice la correlación futura (60 días) entre pares de acciones y un coloreo de grafos agrupa las acciones en canastas que no se mueven juntas.

Descripción completa del problema y del diseño en [PROPUESTA.md](PROPUESTA.md).

## Estructura

```
backend/     API (FastAPI), modelo (scikit-learn) y algoritmos de grafos
frontend/    Aplicación web (Vite + React + TypeScript)
data/        precios.csv, sectores.csv y dataset por pares
notebooks/   exploración y entrenamiento del modelo
informe/     informe del trabajo
```

## Requisitos

- Python 3.12 o superior (probado con 3.14)
- Node.js 20 o superior (probado con 24)

## Instalación y ejecución

### Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

API en http://localhost:8000 (documentación en `/docs`, chequeo en `/health`).

Tests:

```bash
cd backend && source venv/bin/activate && pytest
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Aplicación en http://localhost:5173. Espera el backend en http://localhost:8000.

## Datos

Precios diarios descargados una sola vez con `yfinance` y guardados en `data/precios.csv`, para que el resultado no dependa de Yahoo Finance. `yfinance` no es una API oficial de Yahoo y su uso es personal o educativo.

`data/precios.csv` tiene el precio de cierre ajustado (`auto_adjust=True`, incluye splits y dividendos) de las 30 acciones de `data/sectores.csv` y de `SPY`, del 2014-01-02 al 2023-12-29. Para regenerarlo:

```bash
cd backend && source venv/bin/activate
python scripts/descargar_precios.py
```

## Uso de IA

Ver la sección correspondiente del informe.
