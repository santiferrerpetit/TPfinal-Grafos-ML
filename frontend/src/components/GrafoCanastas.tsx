import { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState } from 'react'
import type { Simulation } from 'd3-force'
import type { Arista, Complemento, Grafo } from '@/api'
import { Skeleton } from '@/components/ui/skeleton'
import { ToggleGroup, ToggleGroupItem } from '@/components/ui/toggle-group'
import { colorCanasta } from '@/lib/formato'
import { ALTO, ANCHO, crearSimulacion, type NodoSim } from '@/lib/layout'

export type VistaGrafo = 'conflicto' | 'complemento'

interface Props {
  grafo: Grafo | null
  complemento: Complemento | null
  vista: VistaGrafo
  onVista: (v: VistaGrafo) => void
  umbral: number
  seleccionada: string
  onSeleccionar: (ticker: string) => void
}

/** Cuánto se mueve la simulación en reposo: lo justo para que el grafo "respire". */
const ALPHA_REPOSO = 0.012
const clave = (a: Arista) => `${a.source}|${a.target}`
const limitar = (t: number) => Math.min(1, Math.max(0, t))
const reducirMovimiento = () => window.matchMedia?.('(prefers-reduced-motion: reduce)').matches ?? false

/**
 * Grafo de acciones al estilo del grafo de Obsidian: simulación física viva, nodos que se pueden
 * arrastrar (y arrastran a sus vecinos), zoom con la rueda, y al pasar el mouse por un nodo se
 * resaltan sus vecinos y el resto se atenúa. Cada nodo va pintado por canasta.
 * - Conflicto: arista si ρ > θ; más gruesa y opaca cuanto mayor es la correlación.
 * - Complemento: arista si ρ ≤ θ; más gruesa cuanto MENOR es la correlación. Cada canasta es un racimo.
 */
export function GrafoCanastas({ grafo, complemento, vista, onVista, umbral, seleccionada, onSeleccionar }: Props) {
  const [hover, setHover] = useState<string | null>(null)
  const [camara, setCamara] = useState({ k: 1, x: 0, y: 0 })

  const svgRef = useRef<SVGSVGElement>(null)
  const contenidoRef = useRef<SVGGElement>(null)
  const simRef = useRef<Simulation<NodoSim, undefined> | null>(null)
  const nodosRef = useRef<Map<string, NodoSim>>(new Map())
  const elNodos = useRef(new Map<string, SVGGElement>())
  const elAristas = useRef(new Map<string, SVGLineElement>())
  const arrastre = useRef<{ id: string; x0: number; y0: number; movido: boolean } | null>(null)
  const paneo = useRef<{ x: number; y: number } | null>(null)

  const aristas: Arista[] | null = vista === 'conflicto' ? (grafo?.aristas ?? null) : (complemento?.aristas ?? null)
  const canastaDe = useMemo(() => new Map(grafo?.nodos.map((n) => [n.id, n.canasta]) ?? []), [grafo])

  const vecinos = useMemo(() => {
    const m = new Map<string, Set<string>>()
    for (const a of aristas ?? []) {
      if (!m.has(a.source)) m.set(a.source, new Set())
      if (!m.has(a.target)) m.set(a.target, new Set())
      m.get(a.source)!.add(a.target)
      m.get(a.target)!.add(a.source)
    }
    return m
  }, [aristas])

  // Escribe las posiciones de la simulación directo en el SVG (sin re-renderizar React en cada cuadro).
  const pintar = useCallback(() => {
    for (const n of nodosRef.current.values()) {
      elNodos.current.get(n.id)?.setAttribute('transform', `translate(${n.x ?? 0},${n.y ?? 0})`)
    }
    for (const a of aristas ?? []) {
      const el = elAristas.current.get(clave(a))
      const p = nodosRef.current.get(a.source)
      const q = nodosRef.current.get(a.target)
      if (!el || !p || !q) continue
      el.setAttribute('x1', String(p.x ?? 0))
      el.setAttribute('y1', String(p.y ?? 0))
      el.setAttribute('x2', String(q.x ?? 0))
      el.setAttribute('y2', String(q.y ?? 0))
    }
  }, [aristas])
  const pintarRef = useRef(pintar)
  pintarRef.current = pintar
  useLayoutEffect(pintar, [pintar, vista])

  // (Re)crea la simulación cuando cambian los nodos, las aristas de conflicto o la vista.
  // Los nodos arrancan donde estaban, así que al cambiar θ o de vista se acomodan moviéndose.
  useEffect(() => {
    if (!grafo) return
    const previas = new Map([...nodosRef.current].map(([id, n]) => [id, { x: n.x ?? 0, y: n.y ?? 0 }]))
    const sim = crearSimulacion(grafo.nodos, grafo.aristas, vista, previas)
    nodosRef.current = new Map(sim.nodes().map((n) => [n.id, n]))
    simRef.current = sim
    const reposo = reducirMovimiento() ? 0 : ALPHA_REPOSO
    sim.alphaTarget(reposo).alpha(0.7).on('tick', () => pintarRef.current())
    return () => {
      sim.stop()
    }
  }, [grafo, vista])

  // Rueda = zoom hacia el cursor. Listener nativo porque React registra la rueda como pasiva.
  useEffect(() => {
    const svg = svgRef.current
    if (!svg) return
    const alRodar = (e: WheelEvent) => {
      e.preventDefault()
      const pt = new DOMPoint(e.clientX, e.clientY).matrixTransform(svg.getScreenCTM()!.inverse())
      setCamara((c) => {
        const k = Math.min(4, Math.max(0.4, c.k * Math.exp(-e.deltaY * 0.0015)))
        return { k, x: pt.x - ((pt.x - c.x) * k) / c.k, y: pt.y - ((pt.y - c.y) * k) / c.k }
      })
    }
    svg.addEventListener('wheel', alRodar, { passive: false })
    return () => svg.removeEventListener('wheel', alRodar)
  }, [grafo])

  const puntoEnSvg = (e: React.PointerEvent) => new DOMPoint(e.clientX, e.clientY).matrixTransform(svgRef.current!.getScreenCTM()!.inverse())
  const puntoEnGrafo = (e: React.PointerEvent) =>
    new DOMPoint(e.clientX, e.clientY).matrixTransform(contenidoRef.current!.getScreenCTM()!.inverse())

  const alBajarNodo = (e: React.PointerEvent, id: string) => {
    e.stopPropagation()
    svgRef.current?.setPointerCapture(e.pointerId)
    const p = puntoEnGrafo(e)
    const n = nodosRef.current.get(id)!
    arrastre.current = { id, x0: e.clientX, y0: e.clientY, movido: false }
    n.fx = p.x
    n.fy = p.y
    simRef.current?.alphaTarget(0.3).restart() // el resto reacciona al arrastre
  }

  const alMover = (e: React.PointerEvent) => {
    const a = arrastre.current
    if (a) {
      if (Math.hypot(e.clientX - a.x0, e.clientY - a.y0) > 3) a.movido = true
      const p = puntoEnGrafo(e)
      const n = nodosRef.current.get(a.id)!
      n.fx = p.x
      n.fy = p.y
    } else if (paneo.current) {
      const p = puntoEnSvg(e)
      const origen = paneo.current
      setCamara((c) => ({ ...c, x: c.x + p.x - origen.x, y: c.y + p.y - origen.y }))
      paneo.current = p
    }
  }

  const alSoltar = () => {
    const a = arrastre.current
    if (a) {
      const n = nodosRef.current.get(a.id)!
      n.fx = null
      n.fy = null
      simRef.current?.alphaTarget(reducirMovimiento() ? 0 : ALPHA_REPOSO)
      if (!a.movido) onSeleccionar(a.id) // un click sin arrastrar selecciona la acción
    }
    arrastre.current = null
    paneo.current = null
  }

  const vecinosDelFoco = hover ? vecinos.get(hover) : undefined
  const resaltado = (id: string) => hover === null || id === hover || (vecinosDelFoco?.has(id) ?? false)

  const estilo = (a: Arista) => {
    // t en [0, 1]: qué tan "fuerte" es la arista en esta vista.
    const t = limitar(vista === 'conflicto' ? (a.peso - umbral) / (1 - umbral) : (umbral - a.peso) / (umbral + 1))
    const mismaCanasta = canastaDe.get(a.source) === canastaDe.get(a.target)
    let opacidad = 0.18 + 0.55 * t
    if (vista === 'complemento' && !mismaCanasta) opacidad *= 0.3 // lo que une racimos distintos queda de fondo
    const incidente = hover !== null ? a.source === hover || a.target === hover : a.source === seleccionada || a.target === seleccionada
    if (hover !== null && !incidente) opacidad = 0.04
    else if (incidente) opacidad = Math.min(1, opacidad + 0.35)
    return {
      ancho: 0.5 + 2.6 * t + (incidente ? 0.7 : 0),
      opacidad,
      color: vista === 'complemento' && mismaCanasta ? colorCanasta(canastaDe.get(a.source)!) : 'var(--muted-foreground)',
    }
  }

  return (
    <div className="flex h-full min-h-0 flex-col gap-2">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <p className="text-sm text-muted-foreground">
          {vista === 'conflicto' ? (
            <>
              Se unen las acciones con correlación mayor a θ = <strong className="text-foreground">{umbral.toFixed(2)}</strong>;
              más grueso = más correlacionadas. Mismo color = misma canasta. Arrastrá un nodo, rodá para hacer zoom.
            </>
          ) : (
            <>
              Se unen las acciones que <strong className="text-foreground">sí</strong> pueden ir juntas (correlación ≤ θ);
              más grueso = menos correlacionadas. Cada canasta queda como un grupo donde todas se unen con todas.
            </>
          )}
        </p>
        <ToggleGroup
          variant="outline"
          size="sm"
          spacing={0}
          value={[vista]}
          onValueChange={(v) => v[0] && onVista(v[0] as VistaGrafo)}
          aria-label="Vista del grafo"
        >
          <ToggleGroupItem value="conflicto">Conflicto</ToggleGroupItem>
          <ToggleGroupItem value="complemento">Complemento</ToggleGroupItem>
        </ToggleGroup>
      </div>

      {!grafo || !aristas ? (
        <Skeleton className="h-full min-h-72 w-full" />
      ) : (
        <svg
          ref={svgRef}
          viewBox={`0 0 ${ANCHO} ${ALTO}`}
          className="min-h-0 w-full flex-1 cursor-grab touch-none rounded-lg border bg-card active:cursor-grabbing"
          role="img"
          aria-label="Grafo de acciones coloreado por canasta"
          onPointerDown={(e) => {
            if (e.target !== e.currentTarget) return
            svgRef.current?.setPointerCapture(e.pointerId)
            paneo.current = puntoEnSvg(e)
          }}
          onPointerMove={alMover}
          onPointerUp={alSoltar}
          onPointerCancel={alSoltar}
        >
          <g ref={contenidoRef} transform={`translate(${camara.x} ${camara.y}) scale(${camara.k})`}>
            <g>
              {aristas.map((a) => {
                const e = estilo(a)
                return (
                  <line
                    key={clave(a)}
                    ref={(el) => {
                      if (el) elAristas.current.set(clave(a), el)
                      else elAristas.current.delete(clave(a))
                    }}
                    stroke={e.color}
                    strokeWidth={e.ancho}
                    strokeOpacity={e.opacidad}
                    strokeLinecap="round"
                    className="transition-[stroke-opacity] duration-200"
                  >
                    <title>{`${a.source} – ${a.target}: ρ = ${a.peso.toFixed(2)}`}</title>
                  </line>
                )
              })}
            </g>
            <g>
              {grafo.nodos.map((n) => {
                const activo = n.id === seleccionada
                const visible = resaltado(n.id)
                const radio = nodosRef.current.get(n.id)?.radio ?? 6
                return (
                  <g
                    key={n.id}
                    ref={(el) => {
                      if (el) elNodos.current.set(n.id, el)
                      else elNodos.current.delete(n.id)
                    }}
                    className="cursor-pointer transition-opacity duration-200"
                    opacity={visible ? 1 : 0.15}
                    onPointerDown={(e) => alBajarNodo(e, n.id)}
                    onPointerEnter={() => setHover(n.id)}
                    onPointerLeave={() => setHover(null)}
                  >
                    <circle r={radio} fill={colorCanasta(n.canasta)} stroke={activo ? 'var(--foreground)' : 'none'} strokeWidth={2} />
                    <text
                      y={radio + 11}
                      textAnchor="middle"
                      fontSize={9}
                      fill="var(--foreground)"
                      opacity={hover === n.id || activo ? 1 : 0.55}
                      className="pointer-events-none select-none"
                    >
                      {n.id}
                    </text>
                    <title>{`${n.id} · canasta ${n.canasta + 1} · ${n.grado} conflictos`}</title>
                  </g>
                )
              })}
            </g>
          </g>
        </svg>
      )}
    </div>
  )
}
