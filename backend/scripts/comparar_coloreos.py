"""Compara greedy por grado y DSATUR: cantidad de colores usados.

Uso (desde backend/, con el venv activado):
    python -m scripts.comparar_coloreos

Imprime tablas en markdown y las guarda en documentacion/comparacion_coloreo.md.
"""

from pathlib import Path

import networkx as nx
import numpy as np
import pandas as pd

from app.grafos.coloreo import cantidad_de_colores, dsatur, es_coloreo_propio, greedy_por_grado
from app.grafos.construccion import construir_grafo

RAIZ = Path(__file__).resolve().parents[2]
N_GRAFOS = 200  # grafos al azar por fila


def matriz(g):
    return nx.to_numpy_array(g, nodelist=sorted(g.nodes), dtype=int)


def tabla_md(filas, columnas):
    texto = "| " + " | ".join(columnas) + " |\n|" + "---|" * len(columnas) + "\n"
    for f in filas:
        texto += "| " + " | ".join(str(x) for x in f) + " |\n"
    return texto


def grafos_al_azar():
    """30 nodos, probabilidad de arista p. Cota inferior = clique máxima."""
    filas = []
    for p in (0.1, 0.2, 0.3, 0.5, 0.7, 0.9):
        v = {"omega": [], "greedy": [], "dsatur": []}
        gana_dsatur = pierde_dsatur = 0
        for semilla in range(N_GRAFOS):
            g = nx.gnp_random_graph(30, p, seed=semilla)
            a = matriz(g)
            cg, cd = greedy_por_grado(a), dsatur(a)
            assert es_coloreo_propio(a, cg) and es_coloreo_propio(a, cd)
            v["omega"].append(max(len(c) for c in nx.find_cliques(g)))
            v["greedy"].append(cantidad_de_colores(cg))
            v["dsatur"].append(cantidad_de_colores(cd))
            gana_dsatur += v["dsatur"][-1] < v["greedy"][-1]
            pierde_dsatur += v["dsatur"][-1] > v["greedy"][-1]
        filas.append([p, f"{np.mean(v['omega']):.2f}", f"{np.mean(v['greedy']):.2f}",
                      f"{np.mean(v['dsatur']):.2f}", gana_dsatur, pierde_dsatur])
    return tabla_md(filas, ["p", "clique máx. (cota inferior)", "greedy (media)", "DSATUR (media)",
                            "DSATUR usa menos", "DSATUR usa más"])


def bipartitos_al_azar():
    """Bipartitos conexos o no, 15+15 nodos con los nodos mezclados al azar."""
    filas = []
    for p in (0.1, 0.2, 0.3, 0.5):
        mal_greedy = mal_dsatur = 0
        peor_greedy = 0
        for semilla in range(N_GRAFOS):
            g = nx.bipartite.random_graph(15, 15, p, seed=semilla)
            if g.number_of_edges() == 0:
                continue
            rng = np.random.default_rng(semilla)
            g = nx.relabel_nodes(g, dict(zip(g.nodes, rng.permutation(30))))  # mezcla el orden de los índices
            a = matriz(g)
            kg, kd = cantidad_de_colores(greedy_por_grado(a)), cantidad_de_colores(dsatur(a))
            mal_greedy += kg > 2
            mal_dsatur += kd > 2
            peor_greedy = max(peor_greedy, kg)
        filas.append([p, f"{mal_greedy}/{N_GRAFOS}", f"{mal_dsatur}/{N_GRAFOS}", peor_greedy])
    return tabla_md(filas, ["p", "greedy usa más de 2", "DSATUR usa más de 2", "máx. colores del greedy"])


def datos_reales():
    """Grafos del dataset real en todas las fechas de corte (30 acciones)."""
    pares = pd.read_csv(RAIZ / "data" / "dataset_pares.csv", parse_dates=["fecha_corte"])
    fechas = sorted(pares["fecha_corte"].unique())
    filas = []
    for fuente in ("corr_90d", "azar"):
        for theta in (0.3, 0.5, 0.7):
            kg, kd, aristas = [], [], []
            for f in fechas:
                g = construir_grafo(pares, f, theta, fuente, semilla=int(pd.Timestamp(f).strftime("%Y%m%d")))
                a = g.adyacencia
                cg, cd = greedy_por_grado(a), dsatur(a)
                assert es_coloreo_propio(a, cg) and es_coloreo_propio(a, cd)
                kg.append(cantidad_de_colores(cg))
                kd.append(cantidad_de_colores(cd))
                aristas.append(len(g.aristas()))
            filas.append([fuente, theta, f"{np.mean(aristas):.0f}", f"{np.mean(kg):.2f}", f"{np.mean(kd):.2f}",
                          sum(d < g_ for g_, d in zip(kg, kd)), sum(d > g_ for g_, d in zip(kg, kd))])
    return len(fechas), tabla_md(filas, ["fuente", "θ", "aristas (media)", "greedy (media)", "DSATUR (media)",
                                          "fechas donde DSATUR usa menos", "fechas donde usa más"])


if __name__ == "__main__":
    n_fechas, reales = datos_reales()
    salida = (
        "# Comparación de coloreos: greedy por grado vs DSATUR\n\n"
        "Generado con `python -m scripts.comparar_coloreos` (desde `backend/`). "
        "Se muestra la cantidad de colores (canastas) usados; menos es mejor. "
        "Welsh-Powell no figura porque da exactamente el mismo coloreo que el greedy por grado.\n\n"
        f"## Grafos al azar de 30 nodos ({N_GRAFOS} por fila)\n\n{grafos_al_azar()}\n"
        f"## Grafos bipartitos al azar de 15+15 nodos ({N_GRAFOS} por fila)\n\n"
        f"Un coloreo óptimo usa siempre 2 colores.\n\n{bipartitos_al_azar()}\n"
        f"## Datos reales ({n_fechas} fechas de corte, 30 acciones)\n\n"
        "Con la fuente `corr_90d` (la del modelo todavía no está lista) y con `azar`.\n\n"
        f"{reales}"
    )
    print(salida)
    (RAIZ / "documentacion" / "comparacion_coloreo.md").write_text(salida, encoding="utf-8")
