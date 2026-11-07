import type { Canasta, Grafo } from '@/api'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Skeleton } from '@/components/ui/skeleton'
import { colorCanasta } from '@/lib/formato'

interface Props {
  grafo: Grafo | null
  canastas: Canasta[] | null
  seleccionada: string
  onSeleccionar: (ticker: string) => void
}

function Dato({ valor, rotulo }: { valor: number | string; rotulo: string }) {
  return (
    <div className="flex flex-col">
      <span className="text-2xl font-semibold tabular-nums">{valor}</span>
      <span className="text-xs text-muted-foreground">{rotulo}</span>
    </div>
  )
}

export function PanelCanastas({ grafo, canastas, seleccionada, onSeleccionar }: Props) {
  return (
    <aside className="flex min-h-0 flex-col border-l bg-card">
      <div className="grid grid-cols-3 gap-2 border-b p-3">
        <Dato valor={grafo?.chi ?? '–'} rotulo="canastas" />
        <Dato valor={grafo?.nodos.length ?? '–'} rotulo="acciones" />
        <Dato valor={grafo?.aristas.length ?? '–'} rotulo="pares unidos" />
      </div>

      <ScrollArea className="min-h-0 flex-1">
        <div className="flex flex-col gap-3 p-3">
          {canastas === null ? (
            Array.from({ length: 3 }, (_, i) => <Skeleton key={i} className="h-24 w-full" />)
          ) : (
            canastas.map((c) => (
              <Card key={c.canasta} size="sm">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <span className="size-2.5 rounded-full" style={{ background: colorCanasta(c.canasta) }} />
                    Canasta {c.canasta + 1}
                  </CardTitle>
                  <CardDescription>
                    {c.acciones.length} {c.acciones.length === 1 ? 'acción' : 'acciones'} · correlación real posterior{' '}
                    <span className="text-foreground tabular-nums">
                      {c.correlacion_promedio_interna === null ? 'n/a' : c.correlacion_promedio_interna.toFixed(2)}
                    </span>
                  </CardDescription>
                </CardHeader>
                <CardContent className="flex flex-wrap gap-1">
                  {c.acciones.map((t) => (
                    <button key={t} type="button" onClick={() => onSeleccionar(t)} aria-label={`Ver ${t}`}>
                      <Badge variant={t === seleccionada ? 'default' : 'secondary'}>{t}</Badge>
                    </button>
                  ))}
                </CardContent>
              </Card>
            ))
          )}
        </div>
      </ScrollArea>
    </aside>
  )
}
