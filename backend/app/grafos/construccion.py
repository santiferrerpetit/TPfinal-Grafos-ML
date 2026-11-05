"""Construcción del grafo de conflicto a partir de correlaciones por par.

Dada una fecha de corte y un umbral θ:
  - nodos = acciones
  - arista entre i y j si ρ(i,j) > θ
  - peso de la arista = ρ(i,j)

El valor ρ sale de una "fuente de pesos" intercambiable: el modelo, la
corr_90d histórica o el azar. Así se arma el mismo grafo con las tres y se
pueden comparar los coloreos.
"""

import numpy as np
import pandas as pd
import networkx as nx

# Columna del dataset de la que sale ρ en cada fuente.
# "modelo" espera una columna `corr_predicha` que agrega el paso del modelo.
COLUMNA_POR_FUENTE = {"modelo": "corr_predicha", "corr_90d": "corr_90d"}
FUENTES = ("modelo", "corr_90d", "azar")


class GrafoConflicto:
    """Grafo simple, no dirigido y con pesos, guardado como matrices n×n.

    - `adyacencia`: 0/1, simétrica, diagonal en 0 (sin lazos ni aristas múltiples).
    - `pesos`: ρ de TODOS los pares (no solo de las aristas), diagonal en 0.
      Se guarda completa porque después se evalúa con ella (p. ej. correlación
      dentro de una canasta) y porque cambiar θ solo cambia `adyacencia`.
    """

    def __init__(self, nodos, pesos, umbral, fuente, fecha_corte):
        self.nodos = list(nodos)
        self.pesos = pesos
        self.umbral = umbral
        self.fuente = fuente
        self.fecha_corte = fecha_corte
        # NaN > umbral da False, así que un par sin dato nunca es arista.
        self.adyacencia = (pesos > umbral).astype(int)
        np.fill_diagonal(self.adyacencia, 0)

    def grado(self):
        """Grado de cada nodo = suma de su fila de la matriz de adyacencia."""
        return self.adyacencia.sum(axis=1)

    def aristas(self):
        """Lista de (accion_i, accion_j, peso) con i antes que j."""
        i_idx, j_idx = np.triu_indices(len(self.nodos), k=1)
        return [
            (self.nodos[i], self.nodos[j], float(self.pesos[i, j]))
            for i, j in zip(i_idx, j_idx)
            if self.adyacencia[i, j]
        ]

    def a_networkx(self):
        """Mismo grafo como nx.Graph (para dibujar y para contrastar en tests)."""
        g = nx.Graph()
        g.add_nodes_from(self.nodos)  # incluye nodos aislados
        g.add_weighted_edges_from(self.aristas())
        return g


def matriz_de_pesos(pares, nodos, fuente, semilla=0):
    """Matriz simétrica n×n con ρ de cada par según la fuente elegida."""
    n = len(nodos)
    if fuente == "azar":
        # Uniforme en [-1, 1], ignora los datos. Se genera el triángulo
        # superior y se espeja para que la matriz sea simétrica.
        rng = np.random.default_rng(semilla)
        pesos = np.triu(rng.uniform(-1, 1, size=(n, n)), k=1)
        return pesos + pesos.T

    columna = COLUMNA_POR_FUENTE[fuente]
    if columna not in pares.columns:
        raise ValueError(f"Falta la columna '{columna}' para la fuente '{fuente}'")

    indice = {accion: k for k, accion in enumerate(nodos)}
    pesos = np.full((n, n), np.nan)
    for a1, a2, rho in zip(pares["accion_id_1"], pares["accion_id_2"], pares[columna]):
        if a1 in indice and a2 in indice:
            pesos[indice[a1], indice[a2]] = rho
            pesos[indice[a2], indice[a1]] = rho
    np.fill_diagonal(pesos, 0)
    return pesos


def construir_grafo(pares, fecha_corte, umbral, fuente="modelo", nodos=None, semilla=0):
    """Arma el GrafoConflicto de una fecha de corte.

    pares: DataFrame con una fila por par y fecha (formato de PROPUESTA.md).
    nodos: acciones del grafo; si no se pasa, las que aparecen en esa fecha.
    semilla: solo se usa con la fuente "azar".
    """
    if fuente not in FUENTES:
        raise ValueError(f"Fuente desconocida '{fuente}'. Opciones: {FUENTES}")

    pares_fecha = pares[pares["fecha_corte"] == pd.Timestamp(fecha_corte)]
    if pares_fecha.empty:
        raise ValueError(f"No hay pares para la fecha de corte {fecha_corte}")

    if nodos is None:
        nodos = sorted(set(pares_fecha["accion_id_1"]) | set(pares_fecha["accion_id_2"]))

    pesos = matriz_de_pesos(pares_fecha, list(nodos), fuente, semilla)
    return GrafoConflicto(nodos, pesos, umbral, fuente, pd.Timestamp(fecha_corte))
