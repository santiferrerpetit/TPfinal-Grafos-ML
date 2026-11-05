from itertools import product

import networkx as nx
import numpy as np
import pytest

from app.grafos.coloreo import cantidad_de_colores, dsatur, greedy_por_grado
from app.grafos.cromatico import (
    evaluar, numero_cromatico, polinomio_cromatico,
)


def desde_networkx(g):
    return nx.to_numpy_array(g, nodelist=sorted(g.nodes), dtype=int)


def contar_coloreos(g, k):
    """Fuerza bruta: coloreos propios con k colores."""
    nodos = sorted(g.nodes)
    return sum(
        all(c[a] != c[b] for a, b in g.edges)
        for c in (dict(zip(nodos, t)) for t in product(range(k), repeat=len(nodos)))
    )


def test_formulas_conocidas():
    for k in range(0, 6):
        n = 5
        assert evaluar(polinomio_cromatico(desde_networkx(nx.path_graph(n))), k) == k * (k - 1) ** (n - 1)
        assert evaluar(polinomio_cromatico(desde_networkx(nx.cycle_graph(n))), k) == (k - 1) ** n + (-1) ** n * (k - 1)
        completo = 1
        for i in range(n):
            completo *= k - i
        assert evaluar(polinomio_cromatico(desde_networkx(nx.complete_graph(n))), k) == completo
        assert evaluar(polinomio_cromatico(np.zeros((n, n), dtype=int)), k) == k ** n


def test_triangulo_coeficientes():
    # λ(λ-1)(λ-2) = λ³ - 3λ² + 2λ
    assert polinomio_cromatico(desde_networkx(nx.complete_graph(3))) == [0, 2, -3, 1]


def test_producto_por_componentes():
    g = nx.disjoint_union(nx.complete_graph(3), nx.path_graph(2))
    for k in range(5):
        assert evaluar(polinomio_cromatico(desde_networkx(g)), k) == k * (k - 1) * (k - 2) * k * (k - 1)


def test_coincide_con_fuerza_bruta():
    for semilla in range(15):
        g = nx.gnp_random_graph(6, 0.4, seed=semilla)
        p = polinomio_cromatico(desde_networkx(g))
        for k in range(4):
            assert evaluar(p, k) == contar_coloreos(g, k)


def test_numero_cromatico_casos_conocidos():
    assert numero_cromatico(np.zeros((4, 4), dtype=int)) == 1
    assert numero_cromatico(desde_networkx(nx.cycle_graph(6))) == 2
    assert numero_cromatico(desde_networkx(nx.cycle_graph(7))) == 3
    assert numero_cromatico(desde_networkx(nx.complete_graph(5))) == 5


def test_demasiadas_aristas():
    with pytest.raises(ValueError):
        polinomio_cromatico(desde_networkx(nx.complete_graph(9)))  # 36 aristas


# --- greedy vs χ exacto ------------------------------------------------

def test_greedy_nunca_baja_de_chi_y_a_veces_la_supera():
    iguales = peores = 0
    for semilla in range(60):
        a = desde_networkx(nx.gnp_random_graph(8, 0.4, seed=semilla))
        chi = numero_cromatico(a)
        usados = cantidad_de_colores(greedy_por_grado(a))
        assert usados >= chi
        assert cantidad_de_colores(dsatur(a)) >= chi
        iguales += usados == chi
        peores += usados > chi
    print(f"greedy == χ en {iguales}/60, greedy > χ en {peores}/60")
    assert iguales > 0


def test_greedy_no_es_exacto_en_la_corona():
    # Bipartito (χ=2) donde el greedy por grado usa más colores (ver decisión 23).
    g = nx.Graph()
    n = 4
    g.add_edges_from((i, n + j) for i in range(n) for j in range(n) if i != j)
    orden = [0, 4, 1, 5, 2, 6, 3, 7]  # nodos intercalados
    a = nx.to_numpy_array(g, nodelist=orden, dtype=int)
    assert numero_cromatico(a) == 2
    assert cantidad_de_colores(greedy_por_grado(a)) > 2
