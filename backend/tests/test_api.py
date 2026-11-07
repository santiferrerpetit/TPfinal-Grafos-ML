import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


@pytest.fixture(scope="module")
def fecha():
    return client.get("/fechas").json()[-1]


def test_fechas_ordenadas():
    r = client.get("/fechas")
    assert r.status_code == 200
    f = r.json()
    assert len(f) > 1 and f == sorted(f)


@pytest.mark.parametrize("fuente", ["modelo", "corr_90d", "azar"])
def test_grafo_coloreo_propio_y_chi(fecha, fuente):
    r = client.get("/grafo", params={"fecha": fecha, "umbral": 0.5, "fuente": fuente})
    assert r.status_code == 200
    d = r.json()
    color = {n["id"]: n["canasta"] for n in d["nodos"]}
    assert all(color[a["source"]] != color[a["target"]] for a in d["aristas"])
    assert d["chi"] == len(set(color.values()))
    assert all(a["peso"] > 0.5 for a in d["aristas"])


def test_umbral_extremos(fecha):
    alto = client.get("/grafo", params={"fecha": fecha, "umbral": 1}).json()
    assert alto["chi"] == 1 and alto["aristas"] == []
    bajo = client.get("/grafo", params={"fecha": fecha, "umbral": -1}).json()
    n = len(bajo["nodos"])
    assert len(bajo["aristas"]) == n * (n - 1) // 2
    assert bajo["chi"] == n


def test_canastas_particionan_las_acciones(fecha):
    g = client.get("/grafo", params={"fecha": fecha, "umbral": 0.4}).json()
    c = client.get("/canastas", params={"fecha": fecha, "umbral": 0.4}).json()
    acciones = [a for cn in c["canastas"] for a in cn["acciones"]]
    assert sorted(acciones) == sorted(n["id"] for n in g["nodos"])
    assert len(c["canastas"]) == g["chi"]


def test_fecha_inexistente_404():
    r = client.get("/grafo", params={"fecha": "1900-01-01", "umbral": 0.5})
    assert r.status_code == 404


@pytest.mark.parametrize(
    "params",
    [
        {"fecha": "2020-01-01", "umbral": 2},
        {"fecha": "no-fecha", "umbral": 0.5},
        {"fecha": "2020-01-01", "umbral": 0.5, "fuente": "otra"},
        {"umbral": 0.5},
    ],
)
def test_params_invalidos_422(params):
    assert client.get("/grafo", params=params).status_code == 422


def test_metricas():
    d = client.get("/metricas").json()
    assert "test_metricas" in d and "baseline" in d["test_metricas"]


def test_cors_permite_el_frontend():
    r = client.options(
        "/fechas",
        headers={"Origin": "http://localhost:5173", "Access-Control-Request-Method": "GET"},
    )
    assert r.headers["access-control-allow-origin"] == "http://localhost:5173"


def test_complemento_es_el_complemento(fecha):
    g = client.get("/grafo", params={"fecha": fecha, "umbral": 0.4}).json()
    c = client.get("/complemento", params={"fecha": fecha, "umbral": 0.4}).json()
    n = len(g["nodos"])
    original = {frozenset((a["source"], a["target"])) for a in g["aristas"]}
    comp = {frozenset((a["source"], a["target"])) for a in c["aristas"]}
    assert not original & comp
    assert len(original) + len(comp) == n * (n - 1) // 2


def test_prim_es_arbol_generador(fecha):
    d = client.get("/prim", params={"fecha": fecha}).json()
    nodos = {n["id"] for n in client.get("/grafo", params={"fecha": fecha, "umbral": 0}).json()["nodos"]}
    assert len(d["aristas"]) == len(nodos) - 1
    assert {x for a in d["aristas"] for x in (a["source"], a["target"])} == nodos
    assert d["distancia_total"] == pytest.approx(sum(a["distancia"] for a in d["aristas"]))


def test_nodos_de_quiebre_son_nodos_del_grafo(fecha):
    g = client.get("/grafo", params={"fecha": fecha, "umbral": 0.5}).json()
    q = client.get("/nodos-quiebre", params={"fecha": fecha, "umbral": 0.5}).json()
    assert set(q["nodos_de_quiebre"]) <= {n["id"] for n in g["nodos"]}


def test_polinomio_de_clique_chica(fecha):
    # umbral -1: todos conectados, el subgrafo de 4 acciones es K4 -> P = l(l-1)(l-2)(l-3)
    acciones = "AAPL,MSFT,KO,PG"
    d = client.get("/polinomio", params={"fecha": fecha, "umbral": -1, "acciones": acciones, "k": 4}).json()
    assert d["coeficientes"] == [0, -6, 11, -6, 1]
    assert d["chi"] == 4 and d["aristas"] == 6
    assert d["evaluado"] == {"k": 4, "valor": 24}


def test_polinomio_grafo_completo_demasiado_grande_422(fecha):
    r = client.get("/polinomio", params={"fecha": fecha, "umbral": -1})
    assert r.status_code == 422


def test_polinomio_accion_desconocida_422(fecha):
    r = client.get("/polinomio", params={"fecha": fecha, "umbral": 0, "acciones": "AAPL,NOEXISTE"})
    assert r.status_code == 422
