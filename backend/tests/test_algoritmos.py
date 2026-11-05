import math

import networkx as nx
import numpy as np
import pytest

from app.grafos.algoritmos import (
    complemento, distancia, es_bipartito, nodos_de_quiebre, prim,
)
from app.grafos.coloreo import es_coloreo_propio


def desde_networkx(g):
    return nx.to_numpy_array(g, nodelist=sorted(g.nodes), dtype=int)


def grafos_al_azar(cantidad=40):
    for semilla in range(cantidad):
        yield nx.gnp_random_graph(9, 0.3, seed=semilla)


# --- bipartición -------------------------------------------------------

@pytest.mark.parametrize("g", [nx.path_graph(6), nx.cycle_graph(8), nx.star_graph(5),
                               nx.complete_bipartite_graph(3, 4), nx.empty_graph(4)])
def test_bipartitos(g):
    a = desde_networkx(g)
    ok, lado = es_bipartito(a)
    assert ok and es_coloreo_propio(a, lado)


@pytest.mark.parametrize("g", [nx.cycle_graph(5), nx.complete_graph(3), nx.complete_graph(6)])
def test_no_bipartitos(g):
    assert es_bipartito(desde_networkx(g)) == (False, None)


def test_bipartito_coincide_con_networkx():
    for g in grafos_al_azar():
        assert es_bipartito(desde_networkx(g))[0] == nx.is_bipartite(g)


# --- complemento -------------------------------------------------------

def test_complemento_de_completo_y_vacio():
    k4 = desde_networkx(nx.complete_graph(4))
    assert not complemento(k4).any()
    assert complemento(np.zeros((4, 4), dtype=int)).sum() == 12  # K4: 6 aristas x 2


def test_complemento_coincide_con_networkx():
    for g in grafos_al_azar():
        esperado = desde_networkx(nx.complement(g))
        assert (complemento(desde_networkx(g)) == esperado).all()


def test_complemento_es_involucion():
    a = desde_networkx(nx.gnp_random_graph(8, 0.4, seed=1))
    assert (complemento(complemento(a)) == a).all()


# --- nodos de quiebre --------------------------------------------------

def test_quiebre_en_camino_y_ciclo():
    assert nodos_de_quiebre(desde_networkx(nx.path_graph(5))) == [1, 2, 3]
    assert nodos_de_quiebre(desde_networkx(nx.cycle_graph(5))) == []
    assert nodos_de_quiebre(desde_networkx(nx.complete_graph(5))) == []


def test_quiebre_estrella_es_el_centro():
    assert nodos_de_quiebre(desde_networkx(nx.star_graph(4))) == [0]


def test_quiebre_con_varias_componentes():
    g = nx.disjoint_union(nx.path_graph(3), nx.Graph([(0, 1)]))  # camino + arista aparte
    g.add_node(5)  # aislado
    assert nodos_de_quiebre(desde_networkx(g)) == [1]


def test_quiebre_coincide_con_puntos_de_articulacion_de_networkx():
    # En grafos conexos, k(G-v) > k(G) es lo mismo que ser punto de articulación.
    for g in grafos_al_azar():
        if nx.is_connected(g):
            assert nodos_de_quiebre(desde_networkx(g)) == sorted(nx.articulation_points(g))


# --- Prim --------------------------------------------------------------

def test_distancia():
    assert distancia(1) == 0 and distancia(-1) == 2
    assert distancia(0) == pytest.approx(math.sqrt(2))


def pesos_al_azar(n, semilla):
    rng = np.random.default_rng(semilla)
    m = np.triu(rng.uniform(-1, 1, size=(n, n)), k=1)
    return m + m.T


def test_prim_peso_total_igual_a_networkx():
    for semilla in range(20):
        rho = pesos_al_azar(10, semilla)
        g = nx.Graph()
        for i in range(10):
            for j in range(i + 1, 10):
                g.add_edge(i, j, weight=distancia(rho[i, j]))
        esperado = nx.minimum_spanning_tree(g).size(weight="weight")
        arbol = prim(rho)
        assert len(arbol) == 9
        assert sum(d for _, _, d in arbol) == pytest.approx(esperado)


def test_prim_es_arbol_generador():
    arbol = prim(pesos_al_azar(12, 3))
    g = nx.Graph([(i, j) for i, j, _ in arbol])
    assert g.number_of_nodes() == 12 and nx.is_tree(g)


def test_prim_con_datos_faltantes_da_bosque():
    rho = np.full((4, 4), np.nan)
    rho[0, 1] = rho[1, 0] = 0.9
    rho[2, 3] = rho[3, 2] = 0.5
    assert sorted((i, j) for i, j, _ in prim(rho)) == [(0, 1), (2, 3)]
