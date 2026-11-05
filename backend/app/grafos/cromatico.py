"""Polinomio cromático P(G, λ) por deleción-contracción.

P(G, k) = cantidad de coloreos propios de G con k colores. Se usa:
  - P(G) = P(G - e) - P(G / e)   (e una arista cualquiera)
  - sin aristas: P = λ^n
  - componentes: P(G) = producto de los P de cada componente

Costo exponencial en la cantidad de aristas: solo para grafos chicos.
Un polinomio se guarda como lista de coeficientes: p[i] es el de λ^i.
"""

import numpy as np

from app.grafos.coloreo import componentes_conexas

MAX_ARISTAS = 20  # tope para no colgar el programa sin querer


def _multiplicar(p, q):
    r = [0] * (len(p) + len(q) - 1)
    for i, a in enumerate(p):
        for j, b in enumerate(q):
            r[i + j] += a * b
    return r


def _restar(p, q):
    n = max(len(p), len(q))
    p, q = p + [0] * (n - len(p)), q + [0] * (n - len(q))
    return [a - b for a, b in zip(p, q)]


def _polinomio(a):
    n = len(a)
    if n == 0:
        return [1]
    comps = componentes_conexas(a)
    if len(comps) > 1:  # producto por componentes
        resultado = [1]
        for comp in comps:
            resultado = _multiplicar(resultado, _polinomio(a[np.ix_(comp, comp)]))
        return resultado
    if not a.any():  # un solo nodo (conexo y sin aristas): λ
        return [0, 1]
    # Conexo con aristas: deleción-contracción sobre la primera arista (u, v).
    u, v = np.argwhere(np.triu(a, k=1))[0]
    eliminada = a.copy()
    eliminada[u, v] = eliminada[v, u] = 0
    # Contraer: v se funde en u (u hereda los vecinos de v) y se borra v.
    contraida = a.copy()
    contraida[u] = contraida[v] = contraida[u] | contraida[v]
    contraida[:, u] = contraida[:, v] = contraida[u]
    contraida[u, u] = 0
    resto = [i for i in range(n) if i != v]
    contraida = contraida[np.ix_(resto, resto)]
    return _restar(_polinomio(eliminada), _polinomio(contraida))


def polinomio_cromatico(adyacencia):
    """Coeficientes de P(G, λ), de menor a mayor grado."""
    aristas = int(adyacencia.sum()) // 2
    if aristas > MAX_ARISTAS:
        raise ValueError(f"{aristas} aristas: demasiado para deleción-contracción (máx {MAX_ARISTAS})")
    return _polinomio(np.asarray(adyacencia, dtype=int))


def evaluar(polinomio, k):
    """P(G, k) por Horner."""
    resultado = 0
    for c in reversed(polinomio):
        resultado = resultado * k + c
    return resultado


def numero_cromatico(adyacencia):
    """χ(G) = menor k con P(G, k) > 0 (para k = 0, 1, ..., n)."""
    p = polinomio_cromatico(adyacencia)
    n = len(adyacencia)
    return next((k for k in range(n + 1) if evaluar(p, k) > 0), 0)
