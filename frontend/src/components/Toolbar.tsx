import type { ReactNode } from 'react'
import { ChevronLeftIcon, ChevronRightIcon, LayersIcon } from 'lucide-react'
import { FUENTES, UMBRAL_MAX, UMBRAL_MIN, type Fuente } from '@/api'
import { Button } from '@/components/ui/button'
import { Select, SelectContent, SelectGroup, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Separator } from '@/components/ui/separator'
import { Slider } from '@/components/ui/slider'
import { ToggleGroup, ToggleGroupItem } from '@/components/ui/toggle-group'

interface Props {
  fechas: string[]
  fecha: string
  onFecha: (fecha: string) => void
  umbral: number
  onUmbral: (umbral: number) => void
  fuente: Fuente
  onFuente: (fuente: Fuente) => void
}

export function Toolbar({ fechas, fecha, onFecha, umbral, onUmbral, fuente, onFuente }: Props) {
  const i = fechas.indexOf(fecha)

  return (
    <header className="flex flex-wrap items-center gap-x-8 gap-y-3 border-b bg-card px-5 py-3">
      <div className="flex shrink-0 items-center gap-2 text-lg font-semibold">
        <LayersIcon className="size-6 text-primary" />
        Canastas
      </div>

      <Separator orientation="vertical" className="hidden h-10 md:block" />

      <Campo etiqueta="Fecha de corte">
        <div className="flex items-center gap-1">
          <Button variant="ghost" size="icon-sm" onClick={() => onFecha(fechas[i - 1])} disabled={i <= 0} aria-label="Fecha anterior">
            <ChevronLeftIcon />
          </Button>
          <Select value={fecha} onValueChange={(v) => v && onFecha(v)}>
            <SelectTrigger size="sm" className="w-36 tabular-nums">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectGroup>
                {fechas.map((f) => (
                  <SelectItem key={f} value={f}>
                    {f}
                  </SelectItem>
                ))}
              </SelectGroup>
            </SelectContent>
          </Select>
          <Button
            variant="ghost"
            size="icon-sm"
            onClick={() => onFecha(fechas[i + 1])}
            disabled={i < 0 || i >= fechas.length - 1}
            aria-label="Fecha siguiente"
          >
            <ChevronRightIcon />
          </Button>
        </div>
      </Campo>

      <Separator orientation="vertical" className="hidden h-10 md:block" />

      <Campo etiqueta="Umbral θ">
        <div className="flex h-7 items-center gap-3">
          <div className="w-48 shrink-0 px-1">
            <Slider
              min={UMBRAL_MIN}
              max={UMBRAL_MAX}
              step={0.01}
              value={[umbral]}
              onValueChange={(v) => onUmbral(Array.isArray(v) ? v[0] : v)}
              aria-label="Umbral θ"
            />
          </div>
          <span className="w-12 shrink-0 text-right text-sm font-semibold tabular-nums">{umbral.toFixed(2)}</span>
        </div>
      </Campo>

      <Separator orientation="vertical" className="hidden h-10 md:block" />

      <Campo etiqueta="Correlaciones">
        <ToggleGroup
          variant="outline"
          size="sm"
          spacing={0}
          value={[fuente]}
          onValueChange={(v) => v[0] && onFuente(v[0] as Fuente)}
          aria-label="Fuente de correlaciones"
        >
          {FUENTES.map((f) => (
            <ToggleGroupItem key={f.valor} value={f.valor}>
              {f.etiqueta}
            </ToggleGroupItem>
          ))}
        </ToggleGroup>
      </Campo>
    </header>
  )
}

/** Un control de la barra con su etiqueta arriba. */
function Campo({ etiqueta, children }: { etiqueta: string; children: ReactNode }) {
  return (
    <div className="flex shrink-0 flex-col gap-1">
      <span className="text-xs whitespace-nowrap text-muted-foreground">{etiqueta}</span>
      {children}
    </div>
  )
}
