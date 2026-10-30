"""Descarga única de precios diarios con yfinance y guardado en data/precios.csv.

Uso (desde backend/, con el venv activado):
    python scripts/descargar_precios.py

yfinance no es una API oficial de Yahoo y su uso es personal o educativo.
Con auto_adjust=True los precios ya incluyen splits y dividendos.
"""

from pathlib import Path

import pandas as pd
import yfinance as yf

RAIZ = Path(__file__).resolve().parents[2]
SECTORES = RAIZ / "data" / "sectores.csv"
SALIDA = RAIZ / "data" / "precios.csv"

INICIO = "2014-01-01"
FIN = "2024-01-01"
REFERENCIA = "SPY"


def main() -> None:
    tickers = pd.read_csv(SECTORES)["ticker"].tolist() + [REFERENCIA]

    datos = yf.download(tickers, start=INICIO, end=FIN, auto_adjust=True, progress=False)
    cierres = datos["Close"][tickers]

    print(f"Descargadas {len(cierres)} filas, {cierres.index.min().date()} a {cierres.index.max().date()}")

    faltantes = cierres.isna().sum()
    faltantes = faltantes[faltantes > 0]
    if faltantes.empty:
        print("Sin NaN")
    else:
        print("NaN por ticker:")
        print(faltantes.to_string())

    cierres.to_csv(SALIDA, index_label="fecha")
    print(f"Guardado en {SALIDA}")


if __name__ == "__main__":
    main()
