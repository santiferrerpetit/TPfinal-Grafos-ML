import pandas as pd
from app.grafos.construccion import construir_grafo

pares = pd.DataFrame(
    [("A","B",0.8,0.7), ("A","C",0.6,0.5), ("B","C",0.9,0.2),
     ("A","D",0.1,0.1), ("B","D",0.2,0.6), ("C","D",-0.3,0.0)],
    columns=["accion_id_1","accion_id_2","corr_predicha","corr_90d"],
)
pares["fecha_corte"] = pd.Timestamp("2024-01-31")

g = construir_grafo(pares, "2024-01-31", umbral=0.5, fuente="modelo")
print("aristas modelo:", g.aristas())
print("adyacencia:\n", g.adyacencia)
print("grado:", g.grado())

print("aristas corr_90d:", construir_grafo(pares, "2024-01-31", 0.5, "corr_90d").aristas())
print("aristas azar:", construir_grafo(pares, "2024-01-31", 0.0, "azar", semilla=1).aristas())
print("networkx:", list(g.a_networkx().edges(data=True)))
