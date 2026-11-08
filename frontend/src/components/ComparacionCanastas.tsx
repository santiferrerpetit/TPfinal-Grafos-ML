import { useState } from 'react'
import { Bar, BarChart, CartesianGrid, XAxis, YAxis } from 'recharts'
import { InfoIcon } from 'lucide-react'
import type { ComparacionPorUmbral, NombreVariante } from '@/api'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { ChartContainer, ChartLegend, ChartLegendContent, ChartTooltip, ChartTooltipContent, type ChartConfig } from '@/components/ui/chart'
import { Skeleton } from '@/components/ui/skeleton'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { ToggleGroup, ToggleGroupItem } from '@/components/ui/toggle-group'

const ETIQUETAS: Record<NombreVariante, string> = {
  modelo: 'Modelo',
  'modelo + pesos': 'Modelo + pesos',
  corr_90d: 'Histórica (corr. 90d)',
  azar: 'Azar',
}

// Las claves del gráfico no pueden tener espacios ni "+" (se usan como variables CSS).
const CLAVES: Record<NombreVariante, string> = {
  modelo: 'modelo',
  'modelo + pesos': 'modelo_pesos',
  corr_90d: 'historica',
  azar: 'azar',
}

const config = {
  modelo: { label: ETIQUETAS.modelo, color: 'var(--chart-1)' },
  modelo_pesos: { label: ETIQUETAS['modelo + pesos'], color: 'var(--chart-5)' },
  historica: { label: ETIQUETAS.corr_90d, color: 'var(--chart-3)' },
  azar: { label: ETIQUETAS.azar, color: 'var(--chart-4)' },
} satisfies ChartConfig

const numero = (x: number | null, d = 3) => (x === null ? '–' : x.toFixed(d))

interface Props {
  datos: ComparacionPorUmbral | null
}

/** Correlación real dentro de las canastas (test) según cómo se armó el grafo. Menos es mejor. */
export function ComparacionCanastas({ datos }: Props) {
  const [elegido, setElegido] = useState<number | null>(null)
  if (!datos) return <Skeleton className="h-96 w-full" />

  const umbral = elegido ?? datos.umbrales.find((u) => u === 0.5) ?? datos.umbrales[0]
  const actual = datos.porUmbral[umbral]
  const filas = datos.umbrales.map((u) => ({
    umbral: u.toFixed(1),
    ...Object.fromEntries(datos.porUmbral[u].variantes.map((v) => [CLAVES[v.variante], v.corr_media])),
  }))
  const mejor = Math.min(...actual.variantes.filter((v) => v.variante !== 'modelo + pesos').map((v) => v.corr_media ?? Infinity))

  return (
    <div className="flex flex-col gap-4">
      <p className="text-sm text-muted-foreground">
        Correlación <strong className="text-foreground">real</strong> promedio entre las acciones de una misma canasta, medida en
        el período de test ({actual.fechas} fechas). <strong className="text-foreground">Menos es mejor</strong>: significa
        canastas mejor diversificadas.
      </p>

      <ChartContainer config={config} className="aspect-auto h-64 w-full" aria-label="Correlación real dentro de las canastas por método y umbral">
        <BarChart data={filas} margin={{ left: 0, right: 8, top: 8 }}>
          <CartesianGrid vertical={false} />
          <XAxis dataKey="umbral" tickLine={false} axisLine={false} label={{ value: 'umbral θ', position: 'insideBottom', offset: -2, fill: 'var(--muted-foreground)', fontSize: 11 }} height={36} />
          <YAxis domain={[0, 'auto']} tickLine={false} axisLine={false} width={36} tickFormatter={(v: number) => v.toFixed(2)} />
          <ChartTooltip content={<ChartTooltipContent />} />
          <ChartLegend content={<ChartLegendContent />} />
          {Object.values(CLAVES).map((clave) => (
            <Bar key={clave} dataKey={clave} fill={`var(--color-${clave})`} radius={[3, 3, 0, 0]} />
          ))}
        </BarChart>
      </ChartContainer>

      <div className="flex flex-wrap items-center gap-3">
        <span className="text-sm text-muted-foreground">Detalle con θ =</span>
        <ToggleGroup variant="outline" size="sm" spacing={0} value={[String(umbral)]} onValueChange={(v) => v[0] && setElegido(Number(v[0]))} aria-label="Umbral del detalle">
          {datos.umbrales.map((u) => (
            <ToggleGroupItem key={u} value={String(u)}>
              {u.toFixed(1)}
            </ToggleGroupItem>
          ))}
        </ToggleGroup>
      </div>

      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Método</TableHead>
            <TableHead className="text-right">Corr. real media</TableHead>
            <TableHead className="text-right">Pares con ρ real &gt; θ</TableHead>
            <TableHead className="text-right">Canastas</TableHead>
            <TableHead className="text-right">Aristas</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {actual.variantes.map((v) => (
            <TableRow key={v.variante}>
              <TableCell className="font-medium">{ETIQUETAS[v.variante]}</TableCell>
              <TableCell className={`text-right tabular-nums ${v.variante !== 'modelo + pesos' && v.corr_media === mejor ? 'font-semibold text-up' : ''}`}>{numero(v.corr_media)}</TableCell>
              <TableCell className="text-right tabular-nums">{v.conflictos === null ? '–' : `${(v.conflictos * 100).toFixed(1)}%`}</TableCell>
              <TableCell className="text-right tabular-nums">{numero(v.canastas, 1)}</TableCell>
              <TableCell className="text-right tabular-nums">{numero(v.aristas, 0)}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>

      <Alert>
        <InfoIcon />
        <AlertTitle>Cuidado al comparar con el mismo θ</AlertTitle>
        <AlertDescription>
          <p>
            Cada método genera un grafo de distinta densidad, y por eso usa una cantidad distinta de canastas. El modelo predice
            correlaciones más cercanas al promedio, así que supera el umbral menos veces: tiene menos aristas y necesita menos
            canastas. Menos canastas obliga a juntar más acciones y eso sube la correlación. Mirá la columna
            &quot;Canastas&quot; antes de concluir quién gana.
          </p>
          <p>
            Todos le ganan al azar. El desvío del azar entre semillas es de {numero(actual.azar_desvio_corr_media)}: una diferencia
            menor que eso es ruido.
          </p>
        </AlertDescription>
      </Alert>
    </div>
  )
}
