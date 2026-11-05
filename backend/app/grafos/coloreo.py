"""Coloreo de grafos implementado a mano.

Todas las funciones reciben la matriz de adyacencia (numpy 0/1, simétrica,
diagonal en 0) y devuelven una lista `colores` donde colores[i] es el color
(0, 1, 2, ...) del nodo i. Cada color es una canasta.
"""

import numpy as np


def vecinos(adyacencia, i):
    return np.flatnonzero(adyacencia[i])


def componentes_conexas(adyacencia):
    """Lista de componentes; cada una es una lista de índices de nodos (BFS)."""
    n = len(adyacencia)
    visitado = [False] * n
    componentes = []
    for inicio in range(n):
        if visitado[inicio]:
            continue
        visitado[inicio] = True
        cola, comp = [inicio], []
        while cola:
            u = cola.pop(0)
            comp.append(u)
            for v in vecinos(adyacencia, u):
                if not visitado[v]:
                    visitado[v] = True
                    cola.append(v)
        componentes.append(sorted(comp))
    return componentes


def menor_color_libre(colores, vecinos_de_i):
    """Menor color (desde 0) que no usa ningún vecino ya coloreado."""
    usados = {colores[v] for v in vecinos_de_i if colores[v] is not None}
    c = 0
    while c in usados:
        c += 1
    return c


def greedy_por_grado(adyacencia):
    """Greedy: nodos por grado descendente, cada uno con el menor color libre.

    Se colorea cada componente conexa por separado (chi(G) = máx de las chi de
    las componentes). Desempate entre nodos del mismo grado: menor índice.
    Siempre da un coloreo propio, pero puede usar más de chi(G) colores.
    """
    grado = adyacencia.sum(axis=1)
    colores = [None] * len(adyacencia)
    for comp in componentes_conexas(adyacencia):
        orden = sorted(comp, key=lambda i: (-grado[i], i))
        for i in orden:
            colores[i] = menor_color_libre(colores, vecinos(adyacencia, i))
    return colores


def dsatur(adyacencia):
    """DSATUR (Brélaz): siempre colorea el nodo con más colores distintos en
    sus vecinos (saturación); desempata por grado y luego por índice.
    El orden se decide sobre la marcha, no de antemano. Es exacto en bipartitos.
    """
    n = len(adyacencia)
    grado = adyacencia.sum(axis=1)
    colores = [None] * n
    for _ in range(n):
        def prioridad(i):
            sat = len({colores[v] for v in vecinos(adyacencia, i) if colores[v] is not None})
            return (-sat, -grado[i], i)
        i = min((k for k in range(n) if colores[k] is None), key=prioridad)
        colores[i] = menor_color_libre(colores, vecinos(adyacencia, i))
    return colores


def aristas_monocromaticas(adyacencia, colores):
    """Aristas cuyos dos extremos tienen el mismo color (debería ser vacía)."""
    n = len(adyacencia)
    return [
        (i, j)
        for i in range(n)
        for j in range(i + 1, n)
        if adyacencia[i, j] and colores[i] == colores[j]
    ]


def es_coloreo_propio(adyacencia, colores):
    """True si todos los nodos tienen color y ninguna arista es monocromática."""
    return None not in colores and not aristas_monocromaticas(adyacencia, colores)


def cantidad_de_colores(colores):
    return len(set(colores))


def canastas(nodos, colores):
    """Agrupa los nodos por color: {color: [acciones]}."""
    resultado = {}
    for nodo, c in zip(nodos, colores):
        resultado.setdefault(c, []).append(nodo)
    return resultado
