"""Construye data/dataset_pares.csv a partir de data/precios.csv y data/sectores.csv.

Uso (desde backend/, con el venv activado):
    python -m scripts.construir_dataset
"""

from pathlib import Path

import pandas as pd

from app.dataset import construir_dataset

RAIZ = Path(__file__).resolve().parents[2]
PRECIOS = RAIZ / "data" / "precios.csv"
SECTORES = RAIZ / "data" / "sectores.csv"
SALIDA = RAIZ / "data" / "dataset_pares.csv"


def main() -> None:
    precios = pd.read_csv(PRECIOS, index_col="fecha", parse_dates=True)
    sectores = pd.read_csv(SECTORES).set_index("ticker")["sector"]

    dataset = construir_dataset(precios, sectores)
    dataset.to_csv(SALIDA, index=False)

    print(f"{len(dataset)} filas, {dataset['fecha_corte'].nunique()} fechas de corte, "
          f"{dataset['fecha_corte'].min().date()} a {dataset['fecha_corte'].max().date()}")
    print(dataset.describe().T[["mean", "std", "min", "max"]].round(3).to_string())
    print(f"Guardado en {SALIDA}")


if __name__ == "__main__":
    main()
