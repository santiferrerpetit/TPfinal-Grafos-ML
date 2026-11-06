import networkx as nx
import numpy as np
import pytest

from app.evaluacion import evaluar_canastas, pares_dentro_de_canastas
from app.grafos.coloreo import (
    cantidad_de_colores, es_coloreo_propio, greedy_por_grado, greedy_por_grado_con_pesos,
)


def test_pares_dentro_de_canastas():
    assert pares_dentro_de_canastas([0, 1, 0, 1, 2]) == [(0, 2), (1, 3)]


def test_evaluar_canastas():
    real = np.array([[0, .2, .8], [.2, 0, .4], [.8, .4, 0]])
    m = evaluar_canastas([0, 1, 0], real, umbral=0.5)
    assert m == {"corr_media": pytest.approx(0.8), "conflictos": 1.0, "canastas": 2}
    m = evaluar_canastas([0, 1, 2], real, umbral=0.5)  # todas solas: sin pares
    assert np.isnan(m["corr_media"]) and m["canastas"] == 3


def test_evaluar_ignora_nan():
    real = np.array([[0, np.nan], [np.nan, 0]])
    assert np.isnan(evaluar_canastas([0, 0], real, 0.5)["corr_media"])


def test_greedy_con_pesos_elige_la_canasta_menos_correlacionada():
    # Sin aristas entre b y c: el greedy común los pone junto a "a"; con pesos, "c"
    # (muy correlacionado con a) queda aparte. a-b es arista, a-c también.
    # Nodos: 0=a, 1=b, 2=c, 3=d. Aristas: 0-1, 0-2. d libre elige entre canastas.
    a = np.zeros((4, 4), dtype=int)
    for i, j in [(0, 1), (0, 2)]:
        a[i, j] = a[j, i] = 1
    pesos = np.zeros((4, 4))
    pesos[3, 0] = pesos[0, 3] = 0.9   # d muy correlacionado con a
    pesos[3, 1] = pesos[1, 3] = 0.1
    base = greedy_por_grado(a)
    con_pesos = greedy_por_grado_con_pesos(a, pesos)
    assert base[3] == base[0]                       # sin pesos: d junto a a (color 0)
    assert con_pesos[3] == con_pesos[1] != con_pesos[0]


def test_greedy_con_pesos_siempre_propio():
    rng = np.random.default_rng(0)
    for semilla in range(40):
        g = nx.gnp_random_graph(15, 0.3, seed=semilla)
        a = nx.to_numpy_array(g, dtype=int)
        pesos = rng.uniform(-1, 1, (15, 15))
        pesos = np.triu(pesos, 1) + np.triu(pesos, 1).T
        c = greedy_por_grado_con_pesos(a, pesos)
        assert es_coloreo_propio(a, c)
        assert cantidad_de_colores(c) <= a.sum(axis=1).max() + 1
