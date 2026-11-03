import math

import numpy as np
import pandas as pd
from sklearn.neighbors import KNeighborsRegressor
from sklearn.linear_model import LinearRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeRegressor

from app.dataset import HORIZONTE, PASO

FEATURES = [
    "corr_30d", "corr_90d", "corr_250d", "mismo_sector",
    "dif_volatilidad", "dif_beta", "volatilidad_mercado",
]
TARGET = "corr_futura_60d"
BASELINE = "corr_90d"
# Cortes que hay que saltear para que el target del ultimo corte de train
# (que mira HORIZONTE dias adelante) no llegue al primer corte de test.
GAP_CORTES = math.ceil(HORIZONTE / PASO)


def dividir_temporal(
    df: pd.DataFrame, frac_test: float = 0.3, gap_cortes: int = GAP_CORTES
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Split por fecha de corte: train = pasado, test = futuro, con un gap en el medio.

    Los ultimos `frac_test` de las fechas de corte van a test. Las `gap_cortes`
    fechas previas se descartan: con PASO=20 y HORIZONTE=60, 3 cortes equivalen a
    60 dias habiles, asi que el target de train no se solapa con el de test.
    """
    fechas = np.sort(df["fecha_corte"].unique())
    n_test = max(1, round(len(fechas) * frac_test))
    n_train = len(fechas) - n_test - gap_cortes
    if n_train < 1:
        raise ValueError("No alcanzan fechas de corte para train, gap y test")
    train = df[df["fecha_corte"].isin(fechas[:n_train])]
    test = df[df["fecha_corte"].isin(fechas[n_train + gap_cortes :])]
    return train.copy(), test.copy()


def splits_temporales(fechas: np.ndarray, n_splits: int = 4, gap_cortes: int = GAP_CORTES):
    """Folds de validacion temporal (ventana expansiva) sobre fechas de corte ordenadas.

    Devuelve listas de fechas (train, validacion) por fold, con gap entre ambas.
    """
    fechas = np.sort(fechas)
    tam = len(fechas) // (n_splits + 1)
    folds = []
    for k in range(1, n_splits + 1):
        fin_train = k * tam - gap_cortes
        if fin_train < 1:
            continue
        folds.append((fechas[:fin_train], fechas[k * tam : (k + 1) * tam]))
    return folds


def predecir_baseline(df: pd.DataFrame) -> np.ndarray:
    """El baseline predice que la correlacion futura es la de los ultimos 90 dias."""
    return df[BASELINE].to_numpy()


def candidatos() -> dict[str, dict]:
    """Modelo -> {estimador, grilla} con la grilla de hiperparametros a probar."""
    return {
        "regresion_lineal": {
            "estimador": make_pipeline(StandardScaler(), LinearRegression()),
            "grilla": {},
        },
        "knn": {
            "estimador": make_pipeline(StandardScaler(), KNeighborsRegressor()),
            "grilla": {"kneighborsregressor__n_neighbors": [15, 50, 150, 400, 1000]},
        },
        "arbol": {
            "estimador": DecisionTreeRegressor(random_state=0),
            "grilla": {"max_depth": [2, 3, 5, 8], "min_samples_leaf": [5, 20, 100, 400]},
        },
    }


def _grillas(grilla: dict[str, list]) -> list[dict]:
    combos = [{}]
    for nombre, valores in grilla.items():
        combos = [{**c, nombre: v} for c in combos for v in valores]
    return combos


def ajustar(nombre: str, train: pd.DataFrame, n_splits: int = 4):
    """Elige hiperparametros por validacion temporal (menor MAE) y reentrena con todo train.

    Devuelve (modelo entrenado, mejores parametros, MAE de validacion).
    """
    from sklearn.base import clone
    from sklearn.metrics import mean_absolute_error

    cand = candidatos()[nombre]
    folds = splits_temporales(train["fecha_corte"].unique(), n_splits)
    mejor = (math.inf, {})
    filas_min_train = min(train["fecha_corte"].isin(f_train).sum() for f_train, _ in folds)
    for params in _grillas(cand["grilla"]):
        if params.get("kneighborsregressor__n_neighbors", 0) > filas_min_train:
            continue  # KNN no puede usar mas vecinos que filas de entrenamiento
        errores = []
        for f_train, f_val in folds:
            tr = train[train["fecha_corte"].isin(f_train)]
            va = train[train["fecha_corte"].isin(f_val)]
            m = clone(cand["estimador"]).set_params(**params).fit(tr[FEATURES], tr[TARGET])
            errores.append(mean_absolute_error(va[TARGET], m.predict(va[FEATURES])))
        mae = float(np.mean(errores))
        if mae < mejor[0]:
            mejor = (mae, params)
    modelo = clone(cand["estimador"]).set_params(**mejor[1]).fit(train[FEATURES], train[TARGET])
    return modelo, mejor[1], mejor[0]


def metricas(real, predicho) -> dict[str, float]:
    from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

    return {
        "mae": float(mean_absolute_error(real, predicho)),
        "rmse": float(math.sqrt(mean_squared_error(real, predicho))),
        "r2": float(r2_score(real, predicho)),
    }
