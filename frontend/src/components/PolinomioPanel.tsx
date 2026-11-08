import { useMemo } from 'react'
import { getPolinomio, MAX_ARISTAS_POLINOMIO, type Fuente, type Grafo } from '@/api'
import { usePedido } from '@/hooks'

interface Props {
  grafo: Grafo
  fecha: string
  umbral: number
  fuente: Fuente
  seleccionada: string
}

const SUPERINDICES = '⁰¹²³⁴⁵⁶⁷⁸⁹'
const superindice = (n: number) => [...String(n)].map((d) => SUPERINDICES[Number(d)]).join('')

/** Coeficientes (de menor a mayor grado) -> "λ³ − 3λ² + 2λ". */
export function formatearPolinomio(coef: number[]): string {
  const terminos: string[] = []
  for (let i = coef.length - 1; i >= 0; i--) {
    const c = coef[i]
    if (c === 0) continue
    const signo = c < 0 ? '−' : '+'
    const abs = Math.abs(c)
    const variable = i === 0 ? '' : i === 1 ? 'λ' : `λ${superindice(i)}`
    const numero = abs === 1 && i > 0 ? '' : String(abs)
    terminos.push(terminos.length === 0 ? `${c < 0 ? '−' : ''}${numero}${variable}` : `${signo} ${numero}${variable}`)
  }
  return terminos.join(' ') || '0'
}

/** Componente conexa (lista de tickers) del nodo `inicio` en el grafo de conflicto. */
function componenteDe(grafo: Grafo, inicio: string): { nodos: string[]; aristas: number } {
  const vecinos = new Map<string, string[]>()
  for (const a of grafo.aristas) {
    vecinos.set(a.source, [...(vecinos.get(a.source) ?? []), a.target])
    vecinos.set(a.target, [...(vecinos.get(a.target) ?? []), a.source])
  }
  const visto = new Set([inicio])
  const cola = [inicio]
  while (cola.length) {
    const u = cola.shift()!
    for (const v of vecinos.get(u) ?? []) {
      if (!visto.has(v)) {
        visto.add(v)
        cola.push(v)
      }
    }
  }
  const aristas = grafo.aristas.filter((a) => visto.has(a.source)).length
  return { nodos: [...visto].sort(), aristas }
}

/**
 * Polinomio cromático P(G, λ) de la componente conexa de la acción seleccionada.
 * Cuesta tiempo exponencial en las aristas, así que solo se calcula si la componente es chica.
 */
export function PolinomioPanel({ grafo, fecha, umbral, fuente, seleccionada }: Props) {
  const comp = useMemo(() => componenteDe(grafo, seleccionada), [grafo, seleccionada])
  const chico = comp.aristas <= MAX_ARISTAS_POLINOMIO
  const poli = usePedido(
    (s) => getPolinomio(fecha, umbral, fuente, comp.nodos, s),
    [fecha, umbral, fuente, comp.nodos.join(',')],
    chico,
  )
  const coloresGreedy = new Set(
    grafo.nodos.filter((n) => comp.nodos.includes(n.id)).map((n) => n.canasta),
  ).size

  return (
    <div className="rounded-lg border bg-card p-3 text-sm">
      <div className="mb-1 flex flex-wrap items-baseline gap-x-3">
        <strong>Polinomio cromático</strong>
        <span className="text-muted-foreground">
          componente de {seleccionada}: {comp.nodos.length} {comp.nodos.length === 1 ? 'acción' : 'acciones'}, {comp.aristas}{' '}
          {comp.aristas === 1 ? 'arista' : 'aristas'}
        </span>
      </div>
      {!chico ? (
        <p className="text-muted-foreground">
          Es una componente grande (más de {MAX_ARISTAS_POLINOMIO} aristas) y el cálculo crece exponencialmente. Subí θ o
          elegí una acción de una componente más chica.
        </p>
      ) : poli.error ? (
        <p className="text-destructive">{poli.error}</p>
      ) : !poli.datos ? (
        <p className="text-muted-foreground">Calculando…</p>
      ) : (
        <>
          <p className="font-mono text-base">P(G, λ) = {formatearPolinomio(poli.datos.coeficientes)}</p>
          <p className="mt-1 text-muted-foreground">
            χ(G) = <strong className="text-foreground">{poli.datos.chi}</strong> (el menor k con P(G, k) &gt; 0). El greedy usó{' '}
            <strong className="text-foreground">{coloresGreedy}</strong> {coloresGreedy === 1 ? 'color' : 'colores'} en esta
            componente
            {coloresGreedy === poli.datos.chi ? ': coincide con el óptimo.' : ': más que el óptimo.'}
          </p>
        </>
      )}
    </div>
  )
}
