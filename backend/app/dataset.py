from itertools import combinations

import pandas as pd

MERCADO = "SPY"
PASO = 20
VENTANAS_CORR = (30, 90, 250)
VENTANA_RIESGO = 90
HORIZONTE = 60

COLUMNAS = [
    "accion_id_1", "accion_id_2", "fecha_corte",
    "corr_30d", "corr_90d", "corr_250d",
    "mismo_sector", "dif_volatilidad", "dif_beta", "volatilidad_mercado",
    "corr_futura_60d",
]


def construir_dataset(precios: pd.DataFrame, sectores: pd.Series, mercado: str = MERCADO) -> pd.DataFrame:
    """Dataset por par de acciones y fecha de corte.

    `precios`: fecha x ticker (incluye `mercado`). `sectores`: ticker -> sector.
    Las features usan solo retornos con fecha <= fecha_corte; `corr_futura_60d`
    usa los HORIZONTE retornos siguientes.
    """
    retornos = precios.pct_change().dropna()
    acciones = sorted(sectores.index)
    pares = list(combinations(acciones, 2))
    n = len(retornos)

    filas = []
    for i in range(max(VENTANAS_CORR) - 1, n - HORIZONTE, PASO):
        corr = {v: retornos[acciones].iloc[i - v + 1 : i + 1].corr() for v in VENTANAS_CORR}
        futuro = retornos[acciones].iloc[i + 1 : i + HORIZONTE + 1].corr()

        riesgo = retornos.iloc[i - VENTANA_RIESGO + 1 : i + 1]
        volatilidad = riesgo.std()
        beta = riesgo.cov()[mercado] / riesgo[mercado].var()

        for a, b in pares:
            filas.append((
                a, b, retornos.index[i],
                corr[30].loc[a, b], corr[90].loc[a, b], corr[250].loc[a, b],
                int(sectores[a] == sectores[b]),
                abs(volatilidad[a] - volatilidad[b]),
                abs(beta[a] - beta[b]),
                volatilidad[mercado],
                futuro.loc[a, b],
            ))

    return pd.DataFrame(filas, columns=COLUMNAS)
