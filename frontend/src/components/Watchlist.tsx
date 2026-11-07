import type { Accion, Nodo } from '@/api'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Skeleton } from '@/components/ui/skeleton'
import { cn } from '@/lib/utils'
import { colorCanasta, porcentaje, precio } from '@/lib/formato'

interface Props {
  acciones: Accion[] | null
  nodos: Nodo[] | null
  seleccionada: string
  onSeleccionar: (ticker: string) => void
}

/** Acciones agrupadas por canasta, con precio y variación mensual como en una watchlist. */
export function Watchlist({ acciones, nodos, seleccionada, onSeleccionar }: Props) {
  const grupos = agrupar(acciones, nodos)

  return (
    <aside className="flex min-h-0 flex-col border-r bg-card">
      <div className="grid grid-cols-[1fr_auto_auto] gap-3 border-b px-3 py-2 text-xs text-muted-foreground">
        <span>Acción</span>
        <span className="w-16 text-right">Precio</span>
        <span className="w-16 text-right">1 mes</span>
      </div>
      <ScrollArea className="min-h-0 flex-1">
        {grupos === null ? (
          <div className="flex flex-col gap-2 p-3">
            {Array.from({ length: 12 }, (_, i) => (
              <Skeleton key={i} className="h-8 w-full" />
            ))}
          </div>
        ) : (
          grupos.map(({ canasta, acciones: lista }) => (
            <section key={canasta} aria-label={`Canasta ${canasta + 1}`}>
              <h2 className="flex items-center gap-2 border-b bg-muted/40 px-3 py-1.5 text-xs font-medium">
                <span className="size-2.5 rounded-full" style={{ background: colorCanasta(canasta) }} />
                Canasta {canasta + 1}
                <span className="text-muted-foreground">
                  · {lista.length} {lista.length === 1 ? 'acción' : 'acciones'}
                </span>
              </h2>
              <ul>
                {lista.map((a) => (
                  <Fila key={a.ticker} accion={a} activa={a.ticker === seleccionada} onSeleccionar={onSeleccionar} />
                ))}
              </ul>
            </section>
          ))
        )}
      </ScrollArea>
    </aside>
  )
}

function Fila({ accion: a, activa, onSeleccionar }: { accion: Accion; activa: boolean; onSeleccionar: (t: string) => void }) {
  return (
    <li>
      <button
        type="button"
        onClick={() => onSeleccionar(a.ticker)}
        aria-current={activa}
        className={cn(
          'grid w-full grid-cols-[1fr_auto_auto] items-center gap-3 border-l-2 border-transparent px-3 py-1.5 text-left text-sm hover:bg-accent',
          activa && 'border-primary bg-accent',
        )}
      >
        <span className="flex min-w-0 flex-col">
          <span className="font-medium">{a.ticker}</span>
          <span className="truncate text-xs text-muted-foreground">{a.sector}</span>
        </span>
        <span className="w-16 text-right tabular-nums">{precio(a.precio)}</span>
        <span
          className={cn('w-16 text-right tabular-nums', a.variacion !== null && (a.variacion >= 0 ? 'text-up' : 'text-down'))}
        >
          {porcentaje(a.variacion)}
        </span>
      </button>
    </li>
  )
}

/** Canastas en orden, con sus acciones ordenadas por ticker. null mientras faltan datos. */
function agrupar(acciones: Accion[] | null, nodos: Nodo[] | null) {
  if (!acciones || !nodos) return null
  const canastaDe = new Map(nodos.map((n) => [n.id, n.canasta]))
  const porCanasta = new Map<number, Accion[]>()
  for (const a of acciones) {
    const c = canastaDe.get(a.ticker)
    if (c === undefined) continue
    porCanasta.set(c, [...(porCanasta.get(c) ?? []), a])
  }
  return [...porCanasta.entries()]
    .sort(([a], [b]) => a - b)
    .map(([canasta, lista]) => ({ canasta, acciones: lista.sort((x, y) => x.ticker.localeCompare(y.ticker)) }))
}
