"""Entrena y evalua los modelos de correlacion futura.

Uso (desde backend/, con el venv activado):
    python -m scripts.entrenar_modelo

Genera:
    data/modelo.joblib            modelo elegido (menor MAE en validacion temporal)
    data/metricas.json            metricas en test de baseline y modelos, y por segmento
    informe/figuras/*.png         graficos para el informe
"""

import json
from pathlib import Path

import joblib
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from app.modelo import (
    FEATURES, TARGET, ajustar, candidatos, dividir_temporal, metricas, predecir_baseline,
)

RAIZ = Path(__file__).resolve().parents[2]
DATASET = RAIZ / "data" / "dataset_pares.csv"
MODELO = RAIZ / "data" / "modelo.joblib"
METRICAS = RAIZ / "data" / "metricas.json"
FIGURAS = RAIZ / "informe" / "figuras"


def por_segmento(test: pd.DataFrame, predicciones: dict[str, np.ndarray], umbral_crisis: float) -> dict:
    segmentos = {
        "calma": test["volatilidad_mercado"] <= umbral_crisis,
        "crisis": test["volatilidad_mercado"] > umbral_crisis,
        "mismo_sector": test["mismo_sector"] == 1,
        "distinto_sector": test["mismo_sector"] == 0,
    }
    salida = {}
    for seg, mascara in segmentos.items():
        salida[seg] = {"n": int(mascara.sum())}
        for nombre, pred in predicciones.items():
            salida[seg][nombre] = metricas(test.loc[mascara, TARGET], pred[mascara.to_numpy()])
    return salida


def graficos(test: pd.DataFrame, predicciones: dict[str, np.ndarray], elegido: str) -> None:
    FIGURAS.mkdir(parents=True, exist_ok=True)
    real = test[TARGET].to_numpy()

    fig, ejes = plt.subplots(1, 2, figsize=(10, 4.5), sharex=True, sharey=True)
    for eje, nombre in zip(ejes, ["baseline", elegido]):
        eje.scatter(predicciones[nombre], real, s=3, alpha=0.2)
        eje.plot([-0.2, 1], [-0.2, 1], "r--", lw=1)
        eje.set_title(nombre)
        eje.set_xlabel("correlación predicha")
    ejes[0].set_ylabel("correlación real (60d)")
    fig.tight_layout()
    fig.savefig(FIGURAS / "predicho_vs_real.png", dpi=150)
    plt.close(fig)

    fig, ejes = plt.subplots(1, 2, figsize=(10, 4.5), sharex=True)
    for eje, nombre in zip(ejes, ["baseline", elegido]):
        residuo = real - predicciones[nombre]
        eje.hist(residuo, bins=60)
        eje.axvline(0, color="r", lw=1)
        eje.set_title(f"Residuos: {nombre} (media {residuo.mean():.3f})")
        eje.set_xlabel("real - predicho")
    fig.tight_layout()
    fig.savefig(FIGURAS / "residuos.png", dpi=150)
    plt.close(fig)

    fig, eje = plt.subplots(figsize=(8, 4))
    err = pd.DataFrame({
        "fecha": test["fecha_corte"],
        "baseline": np.abs(real - predicciones["baseline"]),
        elegido: np.abs(real - predicciones[elegido]),
    }).groupby("fecha").mean()
    err.plot(ax=eje)
    eje.set_ylabel("MAE por fecha de corte")
    fig.tight_layout()
    fig.savefig(FIGURAS / "error_por_fecha.png", dpi=150)
    plt.close(fig)


def main() -> None:
    df = pd.read_csv(DATASET, parse_dates=["fecha_corte"])
    train, test = dividir_temporal(df)
    print(f"train: {len(train)} filas, {train['fecha_corte'].min().date()} a {train['fecha_corte'].max().date()}")
    print(f"test:  {len(test)} filas, {test['fecha_corte'].min().date()} a {test['fecha_corte'].max().date()}")

    modelos, info = {}, {}
    for nombre in candidatos():
        modelos[nombre], params, mae_val = ajustar(nombre, train)
        info[nombre] = {"parametros": params, "mae_validacion": mae_val}
        print(f"{nombre}: {params} MAE validacion {mae_val:.4f}")

    predicciones = {"baseline": predecir_baseline(test)}
    predicciones.update({n: m.predict(test[FEATURES]) for n, m in modelos.items()})

    resultados = {n: metricas(test[TARGET], p) for n, p in predicciones.items()}
    elegido = min(modelos, key=lambda n: info[n]["mae_validacion"])  # elige por validacion, no por test
    umbral_crisis = float(train["volatilidad_mercado"].quantile(0.75))

    salida = {
        "elegido": elegido,
        "umbral_crisis_volatilidad_mercado": umbral_crisis,
        "train": {"filas": len(train), "desde": str(train["fecha_corte"].min().date()),
                  "hasta": str(train["fecha_corte"].max().date())},
        "test": {"filas": len(test), "desde": str(test["fecha_corte"].min().date()),
                 "hasta": str(test["fecha_corte"].max().date())},
        "ajuste": info,
        "test_metricas": resultados,
        "por_segmento": por_segmento(test, predicciones, umbral_crisis),
    }
    METRICAS.write_text(json.dumps(salida, indent=2, ensure_ascii=False))
    joblib.dump({"modelo": modelos[elegido], "features": FEATURES, "nombre": elegido}, MODELO)
    graficos(test, predicciones, elegido)

    print("\nTest (MAE / RMSE / R2):")
    for n, m in resultados.items():
        print(f"  {n:18s} {m['mae']:.4f} {m['rmse']:.4f} {m['r2']:.4f}")
    print(f"Elegido por validacion: {elegido}")
    print(f"Guardado {MODELO}, {METRICAS} y figuras en {FIGURAS}")


if __name__ == "__main__":
    main()
