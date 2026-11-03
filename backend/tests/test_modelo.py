import numpy as np
import pandas as pd
import pytest

from app.modelo import (
    FEATURES, GAP_CORTES, TARGET, ajustar, dividir_temporal, metricas,
    predecir_baseline, splits_temporales,
)


@pytest.fixture
def df():
    rng = np.random.default_rng(0)
    fechas = pd.bdate_range("2015-01-01", periods=40, freq="20B")
    filas = []
    for f in fechas:
        for _ in range(100):
            x = rng.uniform(-0.5, 1, size=len(FEATURES))
            fila = dict(zip(FEATURES, x))
            fila["mismo_sector"] = int(fila["mismo_sector"] > 0.5)
            fila[TARGET] = 0.8 * fila["corr_90d"] + rng.normal(0, 0.05)
            fila["fecha_corte"] = f
            filas.append(fila)
    return pd.DataFrame(filas)


def test_split_train_pasado_test_futuro_con_gap(df):
    train, test = dividir_temporal(df, frac_test=0.25)
    assert train["fecha_corte"].max() < test["fecha_corte"].min()
    fechas = np.sort(df["fecha_corte"].unique())
    pos_train = np.searchsorted(fechas, train["fecha_corte"].max())
    pos_test = np.searchsorted(fechas, test["fecha_corte"].min())
    assert pos_test - pos_train == GAP_CORTES + 1
    assert len(test["fecha_corte"].unique()) == 10
    assert len(train) + len(test) < len(df)


def test_split_falla_si_no_hay_fechas(df):
    chico = df[df["fecha_corte"] < df["fecha_corte"].unique()[4]]
    with pytest.raises(ValueError):
        dividir_temporal(chico, frac_test=0.5)


def test_folds_de_validacion_respetan_el_orden(df):
    for tr, va in splits_temporales(df["fecha_corte"].unique(), n_splits=3):
        assert tr.max() < va.min()


def test_baseline_es_corr_90d(df):
    assert np.array_equal(predecir_baseline(df), df["corr_90d"].to_numpy())


@pytest.mark.parametrize("nombre", ["regresion_lineal", "knn", "arbol"])
def test_ajustar_devuelve_modelo_que_predice(df, nombre):
    train, test = dividir_temporal(df, frac_test=0.25)
    modelo, params, mae_val = ajustar(nombre, train, n_splits=3)
    pred = modelo.predict(test[FEATURES])
    assert pred.shape == (len(test),)
    assert mae_val < 0.3


def test_metricas_prediccion_perfecta():
    m = metricas([0.1, 0.5, 0.9], [0.1, 0.5, 0.9])
    assert m == {"mae": 0.0, "rmse": 0.0, "r2": 1.0}
