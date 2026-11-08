import { forceCollide, forceLink, forceManyBody, forceSimulation, forceX, forceY, type Simulation, type SimulationNodeDatum } from 'd3-force'
import type { Arista, Nodo } from '@/api'

export const ANCHO = 800
export const ALTO = 520

export interface NodoSim extends SimulationNodeDatum {
  id: string
  canasta: number
  grado: number
  radio: number
}

interface Enlace {
  source: string | NodoSim
  target: string | NodoSim
}

export type VistaLayout = 'conflicto' | 'complemento'

/** Nodos más grandes cuanto más conflictos tienen (como en Obsidian, donde pesan los más conectados). */
export const radioDe = (grado: number) => 5 + Math.min(6, Math.sqrt(grado) * 1.8)

/** Centro de cada canasta, repartidos en una elipse. */
function centroCanasta(c: number, cantidad: number) {
  if (cantidad === 1) return { x: ANCHO / 2, y: ALTO / 2 }
  const ang = (2 * Math.PI * c) / cantidad - Math.PI / 2
  return { x: ANCHO / 2 + 250 * Math.cos(ang), y: ALTO / 2 + 150 * Math.sin(ang) }
}

/**
 * Simulación de fuerzas "viva": no se resuelve de una vez, el componente la deja correr y los
 * nodos se mueven solos hasta acomodarse (y siguen flotando un poco si `alphaTarget` > 0).
 * `previas` conserva dónde estaban los nodos, para que al cambiar de vista se muevan desde ahí.
 * `arbol` (opcional): uniones del árbol mínimo; en la vista de conflicto también actúan como resortes,
 * más suaves, para que el árbol se vea como árbol en vez de líneas cruzadas.
 */
export function crearSimulacion(
  nodos: Nodo[],
  aristas: Arista[],
  vista: VistaLayout,
  previas: Map<string, { x: number; y: number }>,
  arbol: Arista[] = [],
): Simulation<NodoSim, undefined> {
  const cantidad = Math.max(1, ...nodos.map((n) => n.canasta + 1))
  const sim_nodos: NodoSim[] = nodos.map((n, i) => {
    const prev = previas.get(n.id)
    const ang = (2 * Math.PI * i) / nodos.length
    return {
      id: n.id,
      canasta: n.canasta,
      grado: n.grado,
      radio: radioDe(n.grado),
      x: prev?.x ?? ANCHO / 2 + 140 * Math.cos(ang),
      y: prev?.y ?? ALTO / 2 + 140 * Math.sin(ang),
    }
  })

  const sim = forceSimulation<NodoSim>(sim_nodos)
    .velocityDecay(0.35) // poca fricción: se mueven con un vaivén suave en vez de clavarse
    .force('choque', forceCollide<NodoSim>((n) => n.radio + 4))

  if (vista === 'conflicto') {
    const enlaces: Enlace[] = aristas.map((a) => ({ source: a.source, target: a.target }))
    // Con muchas aristas los resortes juntarían todo en un punto: se aflojan y se repele más.
    const densidad = aristas.length / Math.max(1, nodos.length)
    const enlacesArbol: Enlace[] = arbol.map((a) => ({ source: a.source, target: a.target }))
    sim
      .force('enlaces', forceLink<NodoSim, Enlace>(enlaces).id((n) => n.id).distance(70).strength(Math.min(0.6, 1.2 / (densidad + 1))))
      .force('arbol', forceLink<NodoSim, Enlace>(enlacesArbol).id((n) => n.id).distance(55).strength(0.25))
      .force('carga', forceManyBody().strength(-140 - 25 * densidad))
      .force('x', forceX(ANCHO / 2).strength(0.05))
      .force('y', forceY(ALTO / 2).strength(0.08))
  } else {
    // Cada canasta es un racimo (clique en el complemento): se atraen hacia el centro de su canasta.
    sim
      .force('carga', forceManyBody().strength(-60))
      .force('x', forceX<NodoSim>((n) => centroCanasta(n.canasta, cantidad).x).strength(0.12))
      .force('y', forceY<NodoSim>((n) => centroCanasta(n.canasta, cantidad).y).strength(0.12))
  }
  return sim
}
