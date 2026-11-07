import { useMemo, useState } from 'react'
import { Area, AreaChart, CartesianGrid, ReferenceArea, ReferenceLine, XAxis, YAxis } from 'recharts'
import type { PuntoPrecio } from '@/api'
import { ChartContainer, ChartTooltip, ChartTooltipContent, type ChartConfig } from '@/components/ui/chart'
import { Skeleton } from '@/components/ui/skeleton'
import { ToggleGroup, ToggleGroupItem } from '@/components/ui/toggle-group'

const HORIZONTE = 60 // ruedas que predice el modelo (ver backend/app/dataset.py)

const RANGOS = [
  { valor: '1A', etiqueta: '1A', antes: 250 },
  { valor: '3A', etiqueta: '3A', antes: 750 },
  { valor: 'todo', etiqueta: 'Todo', antes: Infinity },
] as const

const config = { precio: { label: 'Precio', color: 'var(--chart-1)' } } satisfies ChartConfig

interface Props {
  ticker: string
  puntos: PuntoPrecio[] | null
  fechaCorte: string
}

/** Precio de la acción con la fecha de corte y la ventana de 60 ruedas que se quiere predecir. */
export function GraficoPrecio({ ticker, puntos, fechaCorte }: Props) {
  const [rango, setRango] = useState<(typeof RANGOS)[number]['valor']>('1A')

  const vista = useMemo(() => {
    if (!puntos) return null
    const corte = puntos.findIndex((p) => p.fecha >= fechaCorte)
    const antes = RANGOS.find((r) => r.valor === rango)!.antes
    const desde = Math.max(0, (corte < 0 ? puntos.length : corte) - antes)
    const hasta = Math.min(puntos.length, (corte < 0 ? puntos.length : corte) + HORIZONTE + 20)
    const datos = puntos.slice(desde, hasta)
    const finVentana = puntos[Math.min(puntos.length - 1, corte + HORIZONTE)]?.fecha
    return { datos, finVentana: corte >= 0 ? finVentana : undefined }
  }, [puntos, fechaCorte, rango])

  if (!vista) return <Skeleton className="h-full min-h-72 w-full" />

  return (
    <div className="flex h-full min-h-0 flex-col gap-2">
      <ToggleGroup
        variant="outline"
        size="sm"
        spacing={0}
        value={[rango]}
        onValueChange={(v) => v[0] && setRango(v[0] as typeof rango)}
        aria-label="Rango de fechas"
      >
        {RANGOS.map((r) => (
          <ToggleGroupItem key={r.valor} value={r.valor}>
            {r.etiqueta}
          </ToggleGroupItem>
        ))}
      </ToggleGroup>

      <ChartContainer config={config} className="aspect-auto min-h-0 flex-1" aria-label={`Precio de ${ticker}`}>
        <AreaChart data={vista.datos} margin={{ left: 0, right: 8, top: 8 }}>
          <defs>
            <linearGradient id="relleno-precio" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="var(--color-precio)" stopOpacity={0.35} />
              <stop offset="100%" stopColor="var(--color-precio)" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid vertical={false} />
          <XAxis dataKey="fecha" tickLine={false} axisLine={false} minTickGap={48} tickFormatter={(f: string) => f.slice(0, 7)} />
          <YAxis orientation="right" domain={['auto', 'auto']} tickLine={false} axisLine={false} width={48} tickFormatter={(v: number) => v.toFixed(0)} />
          <ChartTooltip content={<ChartTooltipContent indicator="line" />} />
          {vista.finVentana && (
            <ReferenceArea
              x1={fechaCorte}
              x2={vista.finVentana}
              fill="var(--primary)"
              fillOpacity={0.1}
              label={{ value: 'a predecir (60 ruedas)', position: 'insideTop', fill: 'var(--muted-foreground)', fontSize: 11 }}
            />
          )}
          <ReferenceLine x={fechaCorte} stroke="var(--primary)" strokeDasharray="4 4" />
          <Area dataKey="precio" type="monotone" stroke="var(--color-precio)" strokeWidth={2} fill="url(#relleno-precio)" dot={false} />
        </AreaChart>
      </ChartContainer>
    </div>
  )
}
