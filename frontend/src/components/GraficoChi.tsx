import { CartesianGrid, Line, LineChart, ReferenceLine, XAxis, YAxis } from 'recharts'
import type { PuntoChi } from '@/api'
import { ChartContainer, ChartTooltip, ChartTooltipContent, type ChartConfig } from '@/components/ui/chart'
import { Skeleton } from '@/components/ui/skeleton'

const config = {
  chi: { label: 'Canastas', color: 'var(--chart-2)' },
  aristas: { label: 'Pares correlacionados', color: 'var(--chart-3)' },
} satisfies ChartConfig

interface Props {
  puntos: PuntoChi[] | null
  umbral: number
}

/** Cantidad de canastas que hacen falta para cada umbral θ. */
export function GraficoChi({ puntos, umbral }: Props) {
  if (!puntos) return <Skeleton className="h-full min-h-72 w-full" />
  const actual = puntos.reduce((m, p) => (Math.abs(p.umbral - umbral) < Math.abs(m.umbral - umbral) ? p : m))

  return (
    <div className="flex h-full min-h-0 flex-col gap-2">
      <p className="text-sm text-muted-foreground">
        Con θ = <strong className="text-foreground">{umbral.toFixed(2)}</strong> hacen falta{' '}
        <strong className="text-foreground">{actual.chi}</strong> canastas.
      </p>
      <ChartContainer config={config} className="aspect-auto min-h-0 flex-1" aria-label="Canastas según el umbral">
        <LineChart data={puntos} margin={{ left: 0, right: 8, top: 8 }}>
          <CartesianGrid vertical={false} />
          <XAxis
            dataKey="umbral"
            type="number"
            domain={['dataMin', 'dataMax']}
            tickLine={false}
            axisLine={false}
            tickFormatter={(v: number) => v.toFixed(1)}
            label={{ value: 'umbral θ', position: 'insideBottom', offset: -2, fill: 'var(--muted-foreground)', fontSize: 11 }}
            height={36}
          />
          <YAxis orientation="right" tickLine={false} axisLine={false} width={32} allowDecimals={false} />
          <ChartTooltip content={<ChartTooltipContent labelFormatter={(_, p) => `θ = ${Number(p?.[0]?.payload?.umbral).toFixed(2)}`} />} />
          <ReferenceLine x={umbral} stroke="var(--primary)" strokeDasharray="4 4" />
          <Line dataKey="chi" type="stepAfter" stroke="var(--color-chi)" strokeWidth={2} dot={false} />
        </LineChart>
      </ChartContainer>
    </div>
  )
}
