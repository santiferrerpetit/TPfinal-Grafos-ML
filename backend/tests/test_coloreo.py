import networkx as nx
import numpy as np
import pytest

from app.grafos.coloreo import (
    aristas_monocromaticas, cantidad_de_colores, canastas, componentes_conexas,
    dsatur, es_coloreo_propio, greedy_por_grado,
)


def matriz(n, aristas):
    a = np.zeros((n, n), dtype=int)
    for i, j in aristas:
        a[i, j] = a[j, i] = 1
    return a


def desde_networkx(g):
    return nx.to_numpy_array(g, nodelist=sorted(g.nodes), dtype=int)


# --- casos pedidos por la consigna -------------------------------------

def test_sin_aristas_un_color():
    a = matriz(5, [])
    c = greedy_por_grado(a)
    assert cantidad_de_colores(c) == 1 and es_coloreo_propio(a, c)


@pytest.mark.parametrize("n", [1, 2, 3, 5, 8, 30])
def test_completo_n_colores(n):
    a = desde_networkx(nx.complete_graph(n))
    c = greedy_por_grado(a)
    assert cantidad_de_colores(c) == n and es_coloreo_propio(a, c)


@pytest.mark.parametrize("g", [
    nx.path_graph(7),
    nx.cycle_graph(6),
    nx.complete_bipartite_graph(3, 4),
    nx.star_graph(6),
])
def test_bipartito_dos_colores(g):
    a = desde_networkx(g)
    assert nx.is_bipartite(g)
    c = greedy_por_grado(a)
    assert cantidad_de_colores(c) == 2 and es_coloreo_propio(a, c)


def test_ciclo_impar_tres_colores():
    a = desde_networkx(nx.cycle_graph(5))
    assert cantidad_de_colores(greedy_por_grado(a)) == 3


# --- componentes conexas -----------------------------------------------

def test_componentes_conexas():
    a = matriz(6, [(0, 1), (1, 2), (3, 4)])  # {0,1,2}, {3,4}, {5}
    assert componentes_conexas(a) == [[0, 1, 2], [3, 4], [5]]


def test_numero_cromatico_es_el_maximo_de_las_componentes():
    # triángulo (3 colores) + arista (2) + nodo aislado (1)
    a = matriz(6, [(0, 1), (1, 2), (0, 2), (3, 4)])
    assert cantidad_de_colores(greedy_por_grado(a)) == 3


# --- validación --------------------------------------------------------

def test_validador_detecta_aristas_monocromaticas():
    a = matriz(3, [(0, 1), (1, 2)])
    assert es_coloreo_propio(a, [0, 1, 0])
    assert aristas_monocromaticas(a, [0, 0, 1]) == [(0, 1)]
    assert not es_coloreo_propio(a, [0, 0, 1])
    assert not es_coloreo_propio(a, [0, None, 0])


def test_grafos_al_azar_coloreo_propio_y_cota_grado_maximo():
    for semilla in range(30):
        g = nx.gnp_random_graph(25, 0.3, seed=semilla)
        a = desde_networkx(g)
        delta = a.sum(axis=1).max()
        for algoritmo in (greedy_por_grado, dsatur):
            c = algoritmo(a)
            assert es_coloreo_propio(a, c)
            assert cantidad_de_colores(c) <= delta + 1  # cota del greedy


def test_contra_networkx_cota_inferior_por_clique():
    # chi(G) >= tamaño de la clique máxima: ningún coloreo propio usa menos.
    for semilla in range(20):
        g = nx.gnp_random_graph(20, 0.4, seed=semilla)
        omega = max(len(c) for c in nx.find_cliques(g))
        c = greedy_por_grado(desde_networkx(g))
        assert cantidad_de_colores(c) >= omega


def test_canastas():
    assert canastas(["A", "B", "C"], [0, 1, 0]) == {0: ["A", "C"], 1: ["B"]}


# --- variantes ---------------------------------------------------------

def welsh_powell_por_clases(adyacencia):
    """Versión clásica: arma el color 0 entero, después el 1, etc."""
    n = len(adyacencia)
    grado = adyacencia.sum(axis=1)
    orden = sorted(range(n), key=lambda i: (-grado[i], i))
    colores = [None] * n
    color = 0
    while None in colores:
        for i in orden:
            if colores[i] is None and all(colores[v] != color for v in np.flatnonzero(adyacencia[i])):
                colores[i] = color
        color += 1
    return colores


def test_welsh_powell_es_el_mismo_coloreo_que_el_greedy_por_grado():
    for semilla in range(30):
        a = desde_networkx(nx.gnp_random_graph(20, 0.3, seed=semilla))
        assert welsh_powell_por_clases(a) == greedy_por_grado(a)


def test_dsatur_exacto_en_bipartitos():
    for semilla in range(20):
        g = nx.bipartite.random_graph(8, 8, 0.4, seed=semilla)
        if g.number_of_edges() == 0:
            continue
        assert cantidad_de_colores(dsatur(desde_networkx(g))) == 2


def test_greedy_por_grado_puede_fallar_en_bipartitos_y_dsatur_no():
    # Grafo corona (K_{4,4} sin el matching perfecto), nodos intercalados
    # a0,b0,a1,b1,...: es bipartito, todos tienen grado 3 y el desempate por
    # índice hace que el greedy use 4 colores (n). DSATUR usa 2.
    n = 4
    a = np.zeros((2 * n, 2 * n), dtype=int)
    for i in range(n):
        for j in range(n):
            if i != j:
                a[2 * i, 2 * j + 1] = a[2 * j + 1, 2 * i] = 1
    assert cantidad_de_colores(greedy_por_grado(a)) == 4
    assert cantidad_de_colores(dsatur(a)) == 2
