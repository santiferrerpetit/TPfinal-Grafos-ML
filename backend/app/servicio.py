"""Carga de datos/modelo y armado del grafo de una fecha de corte para la API."""
import json
from functools import lru_cache
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from app.grafos.coloreo import canastas, greedy_por_grado
from app.grafos.cromatico import evaluar, numero_cromatico, polinomio_cromatico
from app.grafos.construccion import FUENTES, construir_grafo  # noqa: F401
from app.modelo import FEATURES, TARGET

RAIZ = Path(__file__).resolve().parents[2]
DATASET = RAIZ / "data" / "dataset_pares.csv"
MODELO = RAIZ / "data" / "modelo.joblib"
METRICAS = RAIZ / "data" / "metricas.json"


@lru_cache
def dataset() -> pd.DataFrame:
    return pd.read_csv(DATASET, parse_dates=["fecha_corte"])


@lru_cache
def modelo():
    return joblib.load(MODELO)["modelo"]


@lru_cache
def metricas_modelo() -> dict:
    return json.loads(METRICAS.read_text())


def fechas() -> list[str]:
    return [f.strftime("%Y-%m-%d") for f in sorted(dataset()["fecha_corte"].unique())]


def pares_de_fecha(fecha: str) -> pd.DataFrame | None:
    """Pares de la fecha de corte con la correlacion predicha, o None si no existe."""
    df = dataset()
    sel = df[df["fecha_corte"] == pd.Timestamp(fecha)].copy()
    if sel.empty:
        return None
    sel["corr_predicha"] = modelo().predict(sel[FEATURES])
    return sel


def correlacion_interna(pares: pd.DataFrame, canasta: list[str]) -> float | None:
    """Correlacion futura real promedio entre pares de acciones de la misma canasta."""
    s = set(canasta)
    dentro = pares[pares["accion_id_1"].isin(s) & pares["accion_id_2"].isin(s)]
    if dentro.empty:
        return None
    return float(np.nanmean(dentro[TARGET]))


def construir(fecha: str, umbral: float, fuente: str):
    """(pares, grafo) o None si la fecha no existe."""
    pares = pares_de_fecha(fecha)
    if pares is None:
        return None
    return pares, construir_grafo(pares, fecha, umbral, fuente)


def resolver(fecha: str, umbral: float, fuente: str):
    """(pares, grafo, colores, canastas) o None si la fecha no existe."""
    res = construir(fecha, umbral, fuente)
    if res is None:
        return None
    pares, g = res
    colores = greedy_por_grado(g.adyacencia)
    por_color = canastas(g.nodos, colores)
    lista = [sorted(por_color[c]) for c in sorted(por_color)]
    return pares, g, colores, lista


def polinomio_de_subgrafo(g, acciones: list[str] | None, k: int | None):
    """Polinomio cromatico del subgrafo inducido por `acciones` (o de todo g).

    Levanta ValueError si hay acciones desconocidas o demasiadas aristas.
    """
    if acciones is None:
        idx = list(range(len(g.nodos)))
    else:
        desconocidas = [a for a in acciones if a not in g.nodos]
        if desconocidas or not acciones:
            raise ValueError(f"acciones desconocidas o vacias: {desconocidas}")
        idx = sorted({g.nodos.index(a) for a in acciones})
    sub = g.adyacencia[np.ix_(idx, idx)]
    poly = polinomio_cromatico(sub)  # ValueError si supera MAX_ARISTAS
    return {
        "acciones": [g.nodos[i] for i in idx],
        "aristas": int(sub.sum()) // 2,
        "coeficientes": poly,  # coeficientes[i] es el de lambda^i
        "chi": numero_cromatico(sub),
        "evaluado": None if k is None else {"k": k, "valor": evaluar(poly, k)},
    }
