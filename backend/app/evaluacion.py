"""Evaluación de las canastas con la correlación REAL del período de test."""

import numpy as np


def pares_dentro_de_canastas(colores):
    """Pares (i, j), i < j, de nodos que quedaron en la misma canasta."""
    n = len(colores)
    return [(i, j) for i in range(n) for j in range(i + 1, n) if colores[i] == colores[j]]


def evaluar_canastas(colores, real, umbral):
    """Métricas de un coloreo contra la matriz de correlaciones reales.

    - corr_media: promedio de la correlación real entre pares de una misma canasta
      (menor = mejor diversificada). NaN si ninguna canasta tiene 2 o más acciones.
    - conflictos: fracción de esos pares cuya correlación real supera `umbral`
      (aristas que el grafo real habría tenido y quedaron adentro de una canasta).
    - canastas: cantidad de colores usados.
    """
    valores = np.array([real[i, j] for i, j in pares_dentro_de_canastas(colores)], dtype=float)
    valores = valores[~np.isnan(valores)]
    return {
        "corr_media": float(valores.mean()) if len(valores) else float("nan"),
        "conflictos": float((valores > umbral).mean()) if len(valores) else float("nan"),
        "canastas": len(set(colores)),
    }
