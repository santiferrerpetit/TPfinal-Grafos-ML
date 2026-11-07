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
PRECIOS = RAIZ / "data" / "precios.csv"
SECTORES = RAIZ / "data" / "sectores.csv"
EVALUACION = RAIZ / "data" / "evaluacion_canastas.csv"
VENTANA_VARIACION = 20  # ruedas (~1 mes) para la variacion de la watchlist


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


UMBRAL_MIN, UMBRAL_MAX, UMBRAL_PASO = -0.2, 1.0, 0.05


def chi_por_umbral(fecha: str, fuente: str):
    """[(umbral, aristas, chi)] para una grilla de umbrales, o None si la fecha no existe.

    chi es la cantidad de colores del greedy (cota superior de chi(G)).
    """
    pares = pares_de_fecha(fecha)
    if pares is None:
        return None
    n = round((UMBRAL_MAX - UMBRAL_MIN) / UMBRAL_PASO)
    salida = []
    for k in range(n + 1):
        umbral = round(UMBRAL_MIN + k * UMBRAL_PASO, 2)
        g = construir_grafo(pares, fecha, umbral, fuente)
        colores = greedy_por_grado(g.adyacencia)
        salida.append((umbral, int(g.adyacencia.sum()) // 2, len(set(colores))))
    return salida


@lru_cache
def precios() -> pd.DataFrame:
    return pd.read_csv(PRECIOS, index_col="fecha", parse_dates=True)


@lru_cache
def sectores() -> pd.Series:
    return pd.read_csv(SECTORES).set_index("ticker")["sector"]


def acciones_a_fecha(fecha: str) -> list[dict]:
    """Por accion: sector, precio de la ultima rueda <= fecha y variacion de ~1 mes."""
    px = precios()
    i = px.index.searchsorted(pd.Timestamp(fecha), side="right") - 1
    if i < 0:
        return []
    salida = []
    for ticker, sector in sectores().items():
        precio = float(px[ticker].iloc[i])
        previo = float(px[ticker].iloc[i - VENTANA_VARIACION]) if i >= VENTANA_VARIACION else None
        salida.append({
            "ticker": ticker,
            "sector": sector,
            "precio": precio,
            "variacion": None if previo is None else precio / previo - 1,
        })
    return salida


def serie_de_precios(ticker: str) -> list[dict] | None:
    """[{fecha, precio}] de una accion, o None si no esta en el universo."""
    if ticker not in sectores().index:
        return None
    serie = precios()[ticker]
    return [{"fecha": f.strftime("%Y-%m-%d"), "precio": round(float(v), 4)} for f, v in serie.items()]


COLUMNAS_EVALUACION = ["corr_media", "conflictos", "canastas", "aristas"]
ORDEN_VARIANTES = ["modelo", "modelo + pesos", "corr_90d", "azar"]


@lru_cache
def evaluacion() -> pd.DataFrame:
    """Resultados precalculados por scripts/evaluar_canastas.py (solo fechas de test)."""
    return pd.read_csv(EVALUACION, parse_dates=["fecha"])


def umbrales_evaluados() -> list[float]:
    return sorted(float(t) for t in evaluacion()["theta"].unique())


def fechas_evaluadas() -> list[str]:
    return [f.strftime("%Y-%m-%d") for f in sorted(evaluacion()["fecha"].unique())]


def _numero(x: float) -> float | None:
    return None if pd.isna(x) else float(x)


def comparar(umbral: float, fecha: str | None = None) -> dict | None:
    """Canastas del modelo vs corr_90d vs azar, medidas con la correlacion real de test.

    Sin `fecha` promedia las fechas de test; con `fecha` devuelve solo esa. Para el azar
    primero se promedian las semillas de cada fecha, igual que en el script. Devuelve None
    si la fecha no esta en test; levanta ValueError si el umbral no fue evaluado.
    """
    df = evaluacion()
    sel = df[df["theta"].round(6) == round(umbral, 6)]
    if sel.empty:
        raise ValueError(f"umbral {umbral} no evaluado; disponibles: {umbrales_evaluados()}")
    if fecha is not None:
        sel = sel[sel["fecha"] == pd.Timestamp(fecha)]
        if sel.empty:
            return None

    por_fecha = sel.groupby(["variante", "fecha"])[COLUMNAS_EVALUACION].mean()
    medias = por_fecha.groupby("variante").mean()
    variantes = [v for v in ORDEN_VARIANTES if v in medias.index]

    # dispersion del azar entre semillas (media por semilla sobre las fechas elegidas)
    azar = sel[sel["variante"] == "azar"].groupby("semilla")["corr_media"].mean()
    return {
        "variantes": [
            {"variante": v, **{c: _numero(medias.loc[v, c]) for c in COLUMNAS_EVALUACION}}
            for v in variantes
        ],
        "azar_desvio_corr_media": _numero(azar.std()),
        "fechas": int(sel["fecha"].nunique()),
    }
