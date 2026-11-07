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


def test_chi_por_umbral_monotono_y_extremos(fecha):
    d = client.get("/chi-por-umbral", params={"fecha": fecha}).json()
    p = d["puntos"]
    assert p[0]["umbral"] == -0.2 and p[-1]["umbral"] == 1.0
    assert p[-1]["aristas"] == 0 and p[-1]["chi"] == 1
    # al subir el umbral solo se pierden aristas
    assert all(a["aristas"] >= b["aristas"] for a, b in zip(p, p[1:]))
    # coincide con /grafo en un umbral de la grilla
    g = client.get("/grafo", params={"fecha": fecha, "umbral": 0.5}).json()
    assert next(x for x in p if x["umbral"] == 0.5)["chi"] == g["chi"]


def test_chi_por_umbral_fecha_inexistente_404():
    assert client.get("/chi-por-umbral", params={"fecha": "1900-01-01"}).status_code == 404


def test_acciones_a_fecha(fecha):
    r = client.get("/acciones", params={"fecha": fecha})
    assert r.status_code == 200
    a = r.json()
    assert len(a) == 30
    assert {"ticker", "sector", "precio", "variacion"} <= set(a[0])
    assert all(x["precio"] > 0 for x in a)
    assert client.get("/acciones", params={"fecha": "1900-01-01"}).status_code == 404


def test_precios_de_una_accion():
    d = client.get("/precios/aapl").json()
    assert d["ticker"] == "AAPL" and len(d["puntos"]) > 2000
    assert d["puntos"][0]["fecha"] < d["puntos"][-1]["fecha"]
    assert client.get("/precios/NOEXISTE").status_code == 404
    assert client.get("/precios/SPY").status_code == 404  # el indice no es del universo


def test_comparacion_coincide_con_la_tabla_del_script():
    d = client.get("/comparacion", params={"umbral": 0.5}).json()
    v = {x["variante"]: x for x in d["variantes"]}
    assert list(v) == ["modelo", "modelo + pesos", "corr_90d", "azar"]
    # valores de documentacion/evaluacion_canastas.md (theta = 0.5)
    assert v["modelo"]["corr_media"] == pytest.approx(0.278, abs=1e-3)
    assert v["corr_90d"]["corr_media"] == pytest.approx(0.259, abs=1e-3)
    assert v["azar"]["corr_media"] == pytest.approx(0.290, abs=1e-3)
    assert v["modelo"]["aristas"] == pytest.approx(15, abs=0.5)
    assert d["azar_desvio_corr_media"] == pytest.approx(0.018, abs=1e-3)
    assert d["fechas"] == 33


def test_comparacion_por_fecha():
    opc = client.get("/comparacion/opciones").json()
    assert opc["umbrales"] == [0.3, 0.4, 0.5, 0.6] and len(opc["fechas"]) == 33
    d = client.get("/comparacion", params={"umbral": 0.4, "fecha": opc["fechas"][0]}).json()
    assert d["fechas"] == 1 and d["fecha"] == opc["fechas"][0]
    assert {x["variante"] for x in d["variantes"]} == {"modelo", "modelo + pesos", "corr_90d", "azar"}


def test_comparacion_umbral_no_evaluado_422(fecha):
    r = client.get("/comparacion", params={"umbral": 0.55})
    assert r.status_code == 422 and "disponibles" in r.json()["detail"]


def test_comparacion_fecha_de_train_404():
    r = client.get("/comparacion", params={"umbral": 0.5, "fecha": "2015-05-26"})
    assert r.status_code == 404
