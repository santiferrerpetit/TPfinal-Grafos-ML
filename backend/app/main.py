from typing import Literal

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from app import servicio
from app.grafos.algoritmos import complemento, es_bipartito, nodos_de_quiebre, prim
from app.grafos.cromatico import MAX_ARISTAS

app = FastAPI(title="Diversificación de carteras")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

Fuente = Literal["modelo", "corr_90d", "azar"]
Fecha = Query(pattern=r"^\d{4}-\d{2}-\d{2}$", description="Fecha de corte (YYYY-MM-DD)")
Umbral = Query(ge=-1, le=1, description="Umbral θ de correlación para crear una arista")


def _resolver(fecha: str, umbral: float, fuente: str):
    res = servicio.resolver(fecha, umbral, fuente)
    if res is None:
        raise HTTPException(404, f"No hay fecha de corte {fecha}")
    return res


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/fechas")
def fechas():
    return servicio.fechas()


@app.get("/acciones")
def acciones(fecha: str = Fecha):
    """Universo de acciones con sector, precio y variacion mensual a la fecha de corte."""
    if fecha not in servicio.fechas():
        raise HTTPException(404, f"No hay fecha de corte {fecha}")
    return servicio.acciones_a_fecha(fecha)


@app.get("/precios/{ticker}")
def precios(ticker: str):
    serie = servicio.serie_de_precios(ticker.upper())
    if serie is None:
        raise HTTPException(404, f"Accion desconocida: {ticker}")
    return {"ticker": ticker.upper(), "puntos": serie}


@app.get("/grafo")
def grafo(fecha: str = Fecha, umbral: float = Umbral, fuente: Fuente = "modelo"):
    _, g, colores, _ = _resolver(fecha, umbral, fuente)
    grado = g.grado()
    return {
        "fecha": fecha,
        "umbral": umbral,
        "fuente": fuente,
        "chi": len(set(colores)),
        "nodos": [
            {"id": n, "canasta": colores[i], "grado": int(grado[i])}
            for i, n in enumerate(g.nodos)
        ],
        "aristas": [
            {"source": u, "target": v, "peso": w} for u, v, w in g.aristas()
        ],
    }


@app.get("/canastas")
def canastas(fecha: str = Fecha, umbral: float = Umbral, fuente: Fuente = "modelo"):
    pares, _, _, lista = _resolver(fecha, umbral, fuente)
    return {
        "fecha": fecha,
        "umbral": umbral,
        "fuente": fuente,
        "canastas": [
            {
                "canasta": i,
                "acciones": acciones,
                "correlacion_promedio_interna": servicio.correlacion_interna(pares, acciones),
            }
            for i, acciones in enumerate(lista)
        ],
    }


def _construir(fecha: str, umbral: float, fuente: str):
    res = servicio.construir(fecha, umbral, fuente)
    if res is None:
        raise HTTPException(404, f"No hay fecha de corte {fecha}")
    return res


@app.get("/complemento")
def complemento_(fecha: str = Fecha, umbral: float = Umbral, fuente: Fuente = "modelo"):
    """Complemento del grafo: arista entre las acciones que NO superan el umbral."""
    _, g = _construir(fecha, umbral, fuente)
    comp = complemento(g.adyacencia)
    aristas = [
        {"source": g.nodos[i], "target": g.nodos[j], "peso": float(g.pesos[i, j])}
        for i in range(len(g.nodos))
        for j in range(i + 1, len(g.nodos))
        if comp[i, j]
    ]
    bipartito, _ = es_bipartito(g.adyacencia)
    return {
        "fecha": fecha, "umbral": umbral, "fuente": fuente,
        "nodos": g.nodos, "aristas": aristas, "grafo_original_bipartito": bipartito,
    }


@app.get("/prim")
def prim_(fecha: str = Fecha, fuente: Fuente = "modelo"):
    """Arbol generador minimo con d = sqrt(2(1 - rho)); no depende del umbral."""
    _, g = _construir(fecha, 0.0, fuente)
    arbol = prim(g.pesos)
    return {
        "fecha": fecha, "fuente": fuente,
        "aristas": [
            {"source": g.nodos[i], "target": g.nodos[j], "peso": float(g.pesos[i, j]), "distancia": d}
            for i, j, d in arbol
        ],
        "distancia_total": sum(d for _, _, d in arbol),
    }


@app.get("/nodos-quiebre")
def nodos_quiebre(fecha: str = Fecha, umbral: float = Umbral, fuente: Fuente = "modelo"):
    _, g = _construir(fecha, umbral, fuente)
    return {
        "fecha": fecha, "umbral": umbral, "fuente": fuente,
        "nodos_de_quiebre": [g.nodos[i] for i in nodos_de_quiebre(g.adyacencia)],
    }


@app.get("/polinomio")
def polinomio(
    fecha: str = Fecha,
    umbral: float = Umbral,
    fuente: Fuente = "modelo",
    acciones: str | None = Query(None, description="Tickers separados por coma (subgrafo inducido)"),
    k: int | None = Query(None, ge=0, le=100, description="Evalua P(G, k)"),
):
    """Polinomio cromatico (costo exponencial): solo subgrafos con pocas aristas."""
    _, g = _construir(fecha, umbral, fuente)
    lista = None if acciones is None else [a.strip() for a in acciones.split(",") if a.strip()]
    try:
        res = servicio.polinomio_de_subgrafo(g, lista, k)
    except ValueError as e:
        raise HTTPException(422, f"{e}. Pasar `acciones` para un subgrafo chico (max {MAX_ARISTAS} aristas)")
    return {"fecha": fecha, "umbral": umbral, "fuente": fuente, **res}


@app.get("/chi-por-umbral")
def chi_por_umbral(fecha: str = Fecha, fuente: Fuente = "modelo"):
    """Curva chi(umbral): colores del greedy y aristas para una grilla de umbrales."""
    puntos = servicio.chi_por_umbral(fecha, fuente)
    if puntos is None:
        raise HTTPException(404, f"No hay fecha de corte {fecha}")
    return {
        "fecha": fecha, "fuente": fuente,
        "puntos": [{"umbral": u, "aristas": a, "chi": c} for u, a, c in puntos],
    }


@app.get("/metricas")
def metricas():
    return servicio.metricas_modelo()
