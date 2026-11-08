import type { Metricas, NombreModelo } from '@/api'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { cn } from '@/lib/utils'

const NOMBRES: Record<NombreModelo, string> = {
  baseline: 'Baseline (corr. 90d)',
  regresion_lineal: 'Regresión lineal',
  knn: 'kNN',
  arbol: 'Árbol de decisión',
}
const ORDEN: NombreModelo[] = ['baseline', 'regresion_lineal', 'knn', 'arbol']
const SEGMENTOS: Record<string, string> = {
  calma: 'Mercado en calma',
  crisis: 'Mercado en crisis',
  mismo_sector: 'Mismo sector',
  distinto_sector: 'Distinto sector',
}

interface Props {
  metricas: Metricas | null
}

/** Métricas del modelo en test contra el baseline, y por segmento. */
export function MetricasModelo({ metricas }: Props) {
  if (!metricas) return <Skeleton className="h-96 w-full" />
  const { test_metricas: t } = metricas
  const mejorMae = Math.min(...ORDEN.map((m) => t[m].mae))

  return (
    <div className="flex flex-col gap-4">
      <p className="text-sm text-muted-foreground">
        Predicción de la correlación futura a 60 ruedas. Se entrena con {metricas.train.filas.toLocaleString('es-AR')} filas (
        {metricas.train.desde} a {metricas.train.hasta}) y se evalúa en test con {metricas.test.filas.toLocaleString('es-AR')}{' '}
        filas ({metricas.test.desde} a {metricas.test.hasta}).
      </p>

      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Modelo</TableHead>
            <TableHead className="text-right">MAE</TableHead>
            <TableHead className="text-right">vs baseline</TableHead>
            <TableHead className="text-right">RMSE</TableHead>
            <TableHead className="text-right">R²</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {ORDEN.map((m) => {
            const delta = (1 - t[m].mae / t.baseline.mae) * 100
            return (
              <TableRow key={m}>
                <TableCell className="font-medium">
                  <span className="flex items-center gap-2">
                    {NOMBRES[m]}
                    {m === metricas.elegido && <Badge variant="secondary">elegido por validación</Badge>}
                  </span>
                </TableCell>
                <TableCell className={cn('text-right tabular-nums', t[m].mae === mejorMae && 'font-semibold text-up')}>{t[m].mae.toFixed(4)}</TableCell>
                <TableCell className={cn('text-right tabular-nums', m !== 'baseline' && (delta > 0 ? 'text-up' : 'text-down'))}>
                  {m === 'baseline' ? '–' : `${delta > 0 ? '+' : ''}${delta.toFixed(1)}%`}
                </TableCell>
                <TableCell className="text-right tabular-nums">{t[m].rmse.toFixed(4)}</TableCell>
                <TableCell className="text-right tabular-nums">{t[m].r2.toFixed(3)}</TableCell>
              </TableRow>
            )
          })}
        </TableBody>
      </Table>
      <p className="text-xs text-muted-foreground">
        MAE y RMSE: error en unidades de correlación (menos es mejor). R²: fracción de la varianza explicada (0 = igual que predecir
        la media). En verde, el mejor MAE. &quot;vs baseline&quot; es la mejora del MAE respecto de usar la correlación de los últimos 90 días.
      </p>

      <h2 className="text-sm font-medium">MAE por segmento</h2>
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Segmento</TableHead>
            <TableHead className="text-right">Filas</TableHead>
            {ORDEN.map((m) => (
              <TableHead key={m} className="text-right">
                {NOMBRES[m].split(' (')[0]}
              </TableHead>
            ))}
          </TableRow>
        </TableHeader>
        <TableBody>
          {Object.entries(SEGMENTOS).map(([clave, nombre]) => {
            const seg = metricas.por_segmento[clave]
            if (!seg) return null
            const mejor = Math.min(...ORDEN.map((m) => seg[m].mae))
            return (
              <TableRow key={clave}>
                <TableCell className="font-medium">{nombre}</TableCell>
                <TableCell className="text-right tabular-nums">{seg.n.toLocaleString('es-AR')}</TableCell>
                {ORDEN.map((m) => (
                  <TableCell key={m} className={cn('text-right tabular-nums', seg[m].mae === mejor && 'font-semibold text-up')}>
                    {seg[m].mae.toFixed(3)}
                  </TableCell>
                ))}
              </TableRow>
            )
          })}
        </TableBody>
      </Table>
    </div>
  )
}
