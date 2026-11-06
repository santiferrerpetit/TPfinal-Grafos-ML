"""Compara las canastas armadas con modelo, corr_90d y azar en el período de test.

Uso (desde backend/, con el venv activado, después de entrenar_modelo):
    python -m scripts.evaluar_canastas

Para cada fecha de test y cada θ arma el grafo con cada fuente, colorea y mide la
correlación REAL (corr_futura_60d) dentro de las canastas. Genera:
    documentacion/evaluacion_canastas.md   tablas
    data/evaluacion_canastas.csv           resultados por fecha
    informe/figuras/evaluacion_canastas.png
"""

from pathlib import Path

import joblib
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from app.evaluacion import evaluar_canastas
from app.grafos.coloreo import es_coloreo_propio, greedy_por_grado, greedy_por_grado_con_pesos
from app.grafos.construccion import construir_grafo, matriz_desde_columna
from app.modelo import TARGET, dividir_temporal

RAIZ = Path(__file__).resolve().parents[2]
UMBRALES = (0.3, 0.4, 0.5, 0.6)
UMBRAL_FIGURA = 0.5
SEMILLAS_AZAR = range(20)


def tabla_md(df):
    columnas = list(df.columns)
    texto = "| " + " | ".join(columnas) + " |\n|" + "---|" * len(columnas) + "\n"
    for fila in df.itertuples(index=False):
        texto += "| " + " | ".join(f"{x:.3f}" if isinstance(x, float) else str(x) for x in fila) + " |\n"
    return texto


def resultados_por_fecha(test):
    filas = []
    for fecha in sorted(test["fecha_corte"].unique()):
        pares = test[test["fecha_corte"] == fecha]
        nodos = sorted(set(pares["accion_id_1"]) | set(pares["accion_id_2"]))
        real = matriz_desde_columna(pares, nodos, TARGET)
        for theta in UMBRALES:
            def medir(variante, g, colores, semilla=0):
                assert es_coloreo_propio(g.adyacencia, colores)
                filas.append({"fecha": fecha, "theta": theta, "variante": variante, "semilla": semilla,
                              "aristas": len(g.aristas()), **evaluar_canastas(colores, real, theta)})

            for fuente in ("modelo", "corr_90d"):
                g = construir_grafo(pares, fecha, theta, fuente, nodos)
                medir(fuente, g, greedy_por_grado(g.adyacencia))
                if fuente == "modelo":  # idea extra: ρ̂ elige entre colores válidos
                    medir("modelo + pesos", g, greedy_por_grado_con_pesos(g.adyacencia, g.pesos))
            for semilla in SEMILLAS_AZAR:
                g = construir_grafo(pares, fecha, theta, "azar", nodos, semilla=semilla)
                medir("azar", g, greedy_por_grado(g.adyacencia), semilla)
    return pd.DataFrame(filas)


def resumen(res):
    # Azar: primero se promedian las semillas de cada fecha, así pesa igual que las demás.
    por_fecha = res.groupby(["theta", "variante", "fecha"], as_index=False)[
        ["corr_media", "conflictos", "canastas", "aristas"]].mean()
    r = por_fecha.groupby(["theta", "variante"]).agg(
        corr_media=("corr_media", "mean"), conflictos=("conflictos", "mean"),
        canastas=("canastas", "mean"), aristas=("aristas", "mean")).reset_index()
    # Dispersión del azar entre semillas (media por semilla sobre las fechas).
    azar = res[res["variante"] == "azar"].groupby(["theta", "semilla"])["corr_media"].mean()
    sd = azar.groupby("theta").std()
    return r, sd


def figura(res, r, sd):
    orden = ["modelo", "modelo + pesos", "corr_90d", "azar"]
    fig, (e1, e2) = plt.subplots(1, 2, figsize=(11, 4.2))
    ancho = 0.2
    for k, v in enumerate(orden):
        sub = r[r["variante"] == v].set_index("theta").reindex(UMBRALES)
        err = [sd[t] for t in UMBRALES] if v == "azar" else None
        e1.bar(np.arange(len(UMBRALES)) + k * ancho, sub["corr_media"], ancho, yerr=err, label=v, capsize=2)
    e1.set_xticks(np.arange(len(UMBRALES)) + 1.5 * ancho, [f"θ={t}" for t in UMBRALES])
    e1.set_ylabel("correlación real media dentro de canastas")
    e1.set_title("Menor es mejor")
    e1.set_ylim(0, 0.38)
    e1.legend(loc="upper left", ncol=2, fontsize=8)
    sub = res[(res["theta"] == UMBRAL_FIGURA) & (res["variante"].isin(orden))]
    por_fecha = sub.groupby(["variante", "fecha"])["corr_media"].mean().unstack(0)
    por_fecha[orden].plot(ax=e2, legend=False)
    e2.set_title(f"Por fecha de test (θ={UMBRAL_FIGURA})")
    e2.set_xlabel("")
    fig.tight_layout()
    destino = RAIZ / "informe" / "figuras" / "evaluacion_canastas.png"
    destino.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(destino, dpi=150)


def main():
    df = pd.read_csv(RAIZ / "data" / "dataset_pares.csv", parse_dates=["fecha_corte"])
    _, test = dividir_temporal(df)
    guardado = joblib.load(RAIZ / "data" / "modelo.joblib")
    test["corr_predicha"] = guardado["modelo"].predict(test[guardado["features"]])
    print(f"Test: {test['fecha_corte'].nunique()} fechas, modelo {guardado['nombre']}")

    res = resultados_por_fecha(test)
    res.to_csv(RAIZ / "data" / "evaluacion_canastas.csv", index=False)
    r, sd = resumen(res)
    figura(res, r, sd)

    tabla = r.rename(columns={"corr_media": "corr. real media en canastas",
                              "conflictos": "pares con ρ real > θ", "canastas": "canastas (media)",
                              "aristas": "aristas (media)"})
    tabla["aristas (media)"] = tabla["aristas (media)"].round(0).astype(int)
    texto = (
        "# Evaluación de las canastas en test\n\n"
        "Generado con `python -m scripts.evaluar_canastas` (desde `backend/`). Para cada fecha de test se arma "
        "el grafo de conflicto con cada fuente de ρ, se colorea y se mide la correlación **real** "
        "(`corr_futura_60d`) entre las acciones de una misma canasta. Menos es mejor. "
        f"El azar usa {len(SEMILLAS_AZAR)} semillas por fecha (se promedian primero por fecha).\n\n"
        "- *pares con ρ real > θ*: fracción de pares dentro de una canasta que en la realidad habrían sido arista.\n"
        "- *modelo + pesos*: la variante extra que usa ρ̂ para elegir entre colores válidos.\n"
        "- Cuidado al comparar: a igual θ, cada fuente genera grafos de distinta densidad y por eso distinta "
        "cantidad de canastas; menos canastas obliga a juntar más acciones.\n\n"
        f"{tabla_md(tabla)}\n"
        "Desvío estándar entre semillas del azar (corr. media): "
        + ", ".join(f"θ={t}: {sd[t]:.3f}" for t in UMBRALES) + "\n\n"
        "![evaluación](../informe/figuras/evaluacion_canastas.png)\n"
    )
    (RAIZ / "documentacion" / "evaluacion_canastas.md").write_text(texto, encoding="utf-8")
    print(texto)


if __name__ == "__main__":
    main()
