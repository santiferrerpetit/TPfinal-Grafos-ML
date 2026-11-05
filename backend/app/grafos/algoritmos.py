"""Otros algoritmos de grafos implementados a mano (extras de la propuesta).

Igual que en coloreo.py, trabajan sobre la matriz de adyacencia (numpy 0/1,
simétrica, diagonal en 0). Prim recibe la matriz de pesos ρ.
"""

import math

import numpy as np

from app.grafos.coloreo import componentes_conexas, vecinos


def es_bipartito(adyacencia):
    """Test de bipartición (algoritmo de clase): BFS pintando con 2 colores.

    Se pinta cada nodo con el color opuesto al de quien lo descubre; si una
    arista une dos nodos del mismo color, hay un ciclo impar y no es bipartito.
    Devuelve (True, lados) con lados[i] en {0, 1}, o (False, None).
    """
    n = len(adyacencia)
    lado = [None] * n
    for inicio in range(n):
        if lado[inicio] is not None:
            continue
        lado[inicio] = 0
        cola = [inicio]
        while cola:
            u = cola.pop(0)
            for v in vecinos(adyacencia, u):
                if lado[v] is None:
                    lado[v] = 1 - lado[u]
                    cola.append(v)
                elif lado[v] == lado[u]:
                    return False, None
    return True, lado


def complemento(adyacencia):
    """Grafo complemento: arista donde el original no tiene (sin lazos)."""
    comp = 1 - adyacencia
    np.fill_diagonal(comp, 0)
    return comp


def nodos_de_quiebre(adyacencia):
    """Nodos v tales que k(G - v) > k(G), con k = cantidad de componentes.

    Se prueba sacando cada nodo y contando componentes de nuevo. Un nodo
    aislado no es de quiebre (al sacarlo, k baja).
    """
    n = len(adyacencia)
    k = len(componentes_conexas(adyacencia))
    quiebre = []
    for v in range(n):
        resto = [i for i in range(n) if i != v]
        sin_v = adyacencia[np.ix_(resto, resto)]
        if len(componentes_conexas(sin_v)) > k:
            quiebre.append(v)
    return quiebre


def distancia(rho):
    """d = sqrt(2(1 - ρ)): distancia entre acciones (0 si ρ=1, 2 si ρ=-1)."""
    return math.sqrt(2 * (1 - min(max(rho, -1.0), 1.0)))


def prim(pesos):
    """Árbol generador mínimo (Prim) sobre d = sqrt(2(1 - ρ)).

    pesos: matriz n×n de ρ de todos los pares (NaN = sin dato, no se usa).
    Devuelve una lista de (i, j, d) con i, j índices de nodo. Si faltan datos
    y el grafo no es conexo, queda un bosque (se reinicia en cada componente).
    """
    n = len(pesos)
    en_arbol = [False] * n
    mejor = [math.inf] * n   # menor distancia conocida hacia el árbol
    padre = [None] * n
    aristas = []
    for _ in range(n):
        # Nodo fuera del árbol más cerca de él (o de inicio si no hay ninguno alcanzable).
        candidatos = [i for i in range(n) if not en_arbol[i]]
        u = min(candidatos, key=lambda i: (mejor[i], i))
        en_arbol[u] = True
        if padre[u] is not None:
            aristas.append((padre[u], u, mejor[u]))
        for v in range(n):
            if not en_arbol[v] and not np.isnan(pesos[u, v]):
                d = distancia(pesos[u, v])
                if d < mejor[v]:
                    mejor[v], padre[v] = d, u
    return aristas
