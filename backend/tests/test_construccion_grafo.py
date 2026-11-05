import numpy as np
import pandas as pd
import pytest

from app.grafos.construccion import construir_grafo

FECHA = "2024-01-31"


def pares_de_ejemplo():
    # 4 acciones. Triángulo A-B-C con correlaciones altas, D casi independiente.
    filas = [
        ("A", "B", 0.8, 0.7), ("A", "C", 0.6, 0.5), ("B", "C", 0.9, 0.2),
        ("A", "D", 0.1, 0.1), ("B", "D", 0.2, 0.6), ("C", "D", -0.3, 0.0),
    ]
    df = pd.DataFrame(filas, columns=["accion_id_1", "accion_id_2", "corr_predicha", "corr_90d"])
    df["fecha_corte"] = pd.Timestamp(FECHA)
    return df


def test_arista_si_supera_umbral_y_peso_es_rho():
    g = construir_grafo(pares_de_ejemplo(), FECHA, umbral=0.5, fuente="modelo")
    assert sorted((a, b) for a, b, _ in g.aristas()) == [("A", "B"), ("A", "C"), ("B", "C")]
    assert dict(((a, b), w) for a, b, w in g.aristas())[("B", "C")] == 0.9


def test_umbral_es_estricto():
    # A-C vale exactamente 0.6: con θ = 0.6 no hay arista.
    g = construir_grafo(pares_de_ejemplo(), FECHA, umbral=0.6, fuente="modelo")
    assert ("A", "C") not in [(a, b) for a, b, _ in g.aristas()]


def test_matriz_simetrica_sin_lazos_y_grado():
    g = construir_grafo(pares_de_ejemplo(), FECHA, umbral=0.5)
    assert (g.adyacencia == g.adyacencia.T).all()
    assert (np.diag(g.adyacencia) == 0).all()
    assert list(g.grado()) == [2, 2, 2, 0]  # A, B, C, D


def test_sin_aristas_y_grafo_completo():
    vacio = construir_grafo(pares_de_ejemplo(), FECHA, umbral=0.99)
    assert vacio.adyacencia.sum() == 0 and len(vacio.nodos) == 4
    completo = construir_grafo(pares_de_ejemplo(), FECHA, umbral=-1)
    assert len(completo.aristas()) == 6  # K_4


def test_fuentes_dan_grafos_distintos():
    pares = pares_de_ejemplo()
    modelo = construir_grafo(pares, FECHA, 0.5, "modelo")
    historica = construir_grafo(pares, FECHA, 0.5, "corr_90d")
    assert {(a, b) for a, b, _ in historica.aristas()} == {("A", "B"), ("B", "D")}
    assert not (modelo.adyacencia == historica.adyacencia).all()


def test_azar_reproducible_e_independiente_de_los_datos():
    pares = pares_de_ejemplo()
    g1 = construir_grafo(pares, FECHA, 0.0, "azar", semilla=7)
    g2 = construir_grafo(pares, FECHA, 0.0, "azar", semilla=7)
    g3 = construir_grafo(pares, FECHA, 0.0, "azar", semilla=8)
    assert (g1.pesos == g2.pesos).all()
    assert not (g1.pesos == g3.pesos).all()
    assert (g1.pesos == g1.pesos.T).all()
    assert (np.abs(g1.pesos) <= 1).all()


def test_par_faltante_o_nan_no_es_arista():
    pares = pares_de_ejemplo().iloc[:-1]  # falta C-D
    pares.loc[0, "corr_predicha"] = np.nan  # A-B sin dato
    g = construir_grafo(pares, FECHA, umbral=-1, fuente="modelo")
    assert sorted((a, b) for a, b, _ in g.aristas()) == [("A", "C"), ("A", "D"), ("B", "C"), ("B", "D")]


def test_a_networkx_conserva_nodos_aristas_y_pesos():
    g = construir_grafo(pares_de_ejemplo(), FECHA, umbral=0.5)
    nx_g = g.a_networkx()
    assert set(nx_g.nodes) == {"A", "B", "C", "D"}  # D aislado igual está
    assert nx_g.number_of_edges() == 3
    assert nx_g["B"]["C"]["weight"] == 0.9


def test_errores():
    with pytest.raises(ValueError):
        construir_grafo(pares_de_ejemplo(), FECHA, 0.5, "inventada")
    with pytest.raises(ValueError):
        construir_grafo(pares_de_ejemplo(), "2020-01-01", 0.5)
    with pytest.raises(ValueError):
        construir_grafo(pares_de_ejemplo().drop(columns="corr_predicha"), FECHA, 0.5, "modelo")
