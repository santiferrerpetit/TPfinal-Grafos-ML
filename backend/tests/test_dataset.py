import numpy as np
import pandas as pd
import pytest

from app.dataset import COLUMNAS, construir_dataset

SECTORES = pd.Series({"AAA": "Tec", "BBB": "Tec", "CCC": "Salud", "DDD": "Energia"})
FEATURES = [
    "corr_30d", "corr_90d", "corr_250d", "mismo_sector",
    "dif_volatilidad", "dif_beta", "volatilidad_mercado",
]


@pytest.fixture
def precios():
    rng = np.random.default_rng(0)
    fechas = pd.bdate_range("2020-01-01", periods=450)
    retornos = rng.normal(0.0005, 0.01, size=(450, 5))
    # AAA y BBB comparten un componente para que haya correlaciones distintas
    retornos[:, 1] += retornos[:, 0]
    datos = 100 * np.cumprod(1 + retornos, axis=0)
    return pd.DataFrame(datos, index=fechas, columns=["AAA", "BBB", "CCC", "DDD", "SPY"])


def test_columnas_y_pares(precios):
    df = construir_dataset(precios, SECTORES)
    assert list(df.columns) == COLUMNAS
    # 4 acciones -> 6 pares, sin duplicados y con accion_id_1 < accion_id_2
    assert df.groupby("fecha_corte").size().eq(6).all()
    assert (df["accion_id_1"] < df["accion_id_2"]).all()
    assert not df.duplicated(["accion_id_1", "accion_id_2", "fecha_corte"]).any()


def test_cortes_cada_20_dias_con_historia_y_futuro(precios):
    df = construir_dataset(precios, SECTORES)
    retornos_idx = precios.index[1:]  # el primer día no tiene retorno
    posiciones = sorted(retornos_idx.get_indexer(df["fecha_corte"].unique()))
    assert posiciones[0] == 249  # 250 retornos de historia
    assert np.diff(posiciones).tolist() == [20] * (len(posiciones) - 1)
    assert posiciones[-1] + 60 <= len(retornos_idx) - 1  # 60 retornos de futuro
    assert df.notna().all().all()


def test_mismo_sector_y_diferencias_no_negativas(precios):
    df = construir_dataset(precios, SECTORES)
    par = df[(df.accion_id_1 == "AAA") & (df.accion_id_2 == "BBB")]
    assert par["mismo_sector"].eq(1).all()
    otro = df[(df.accion_id_1 == "AAA") & (df.accion_id_2 == "CCC")]
    assert otro["mismo_sector"].eq(0).all()
    assert (df["dif_volatilidad"] >= 0).all()
    assert (df["dif_beta"] >= 0).all()


def test_valores_contra_calculo_manual(precios):
    df = construir_dataset(precios, SECTORES)
    fila = df[(df.accion_id_1 == "AAA") & (df.accion_id_2 == "BBB")].iloc[2]
    r = precios.pct_change().dropna()
    i = r.index.get_loc(fila["fecha_corte"])

    def corr(ventana, desde=0):
        tramo = r.iloc[i - ventana + 1 + desde : i + 1 + desde]
        return tramo["AAA"].corr(tramo["BBB"])

    assert fila["corr_30d"] == pytest.approx(corr(30))
    assert fila["corr_90d"] == pytest.approx(corr(90))
    assert fila["corr_250d"] == pytest.approx(corr(250))
    futuro = r.iloc[i + 1 : i + 61]
    assert fila["corr_futura_60d"] == pytest.approx(futuro["AAA"].corr(futuro["BBB"]))

    v = r.iloc[i - 89 : i + 1]
    beta = lambda c: v[c].cov(v["SPY"]) / v["SPY"].var()
    assert fila["dif_beta"] == pytest.approx(abs(beta("AAA") - beta("BBB")))
    assert fila["dif_volatilidad"] == pytest.approx(abs(v["AAA"].std() - v["BBB"].std()))
    assert fila["volatilidad_mercado"] == pytest.approx(v["SPY"].std())


def test_features_no_usan_datos_posteriores_al_corte(precios):
    base = construir_dataset(precios, SECTORES)
    corte = base["fecha_corte"].unique()[3]

    # Alteramos todos los precios posteriores al corte
    alterados = precios.copy()
    posteriores = alterados.index > corte
    rng = np.random.default_rng(1)
    alterados.loc[posteriores] *= rng.uniform(0.5, 2.0, size=(posteriores.sum(), 5))
    nuevo = construir_dataset(alterados, SECTORES)

    claves = ["accion_id_1", "accion_id_2", "fecha_corte"]
    unido = base.merge(nuevo, on=claves, suffixes=("_a", "_b"))
    hasta_corte = unido[unido["fecha_corte"] <= corte]
    for col in FEATURES:
        assert hasta_corte[col + "_a"].equals(hasta_corte[col + "_b"]), col

    # El target del propio corte sí mira al futuro, así que cambia
    en_corte = unido[unido["fecha_corte"] == corte]
    assert not np.allclose(en_corte["corr_futura_60d_a"], en_corte["corr_futura_60d_b"])
