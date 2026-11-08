import { useState } from 'react'
import { AlertCircleIcon } from 'lucide-react'
import {
  getAcciones,
  getCanastas,
  getChiPorUmbral,
  getComparaciones,
  getComplemento,
  getFechas,
  getGrafo,
  getMetricas,
  getPrecios,
  type Fuente,
} from '@/api'
import { ComparacionCanastas } from '@/components/ComparacionCanastas'
import { Explicacion } from '@/components/Explicacion'
import { GrafoCanastas, type VistaGrafo } from '@/components/GrafoCanastas'
import { MetricasModelo } from '@/components/MetricasModelo'
import { GraficoChi } from '@/components/GraficoChi'
import { GraficoPrecio } from '@/components/GraficoPrecio'
import { PanelCanastas } from '@/components/PanelCanastas'
import { Toolbar } from '@/components/Toolbar'
import { Watchlist } from '@/components/Watchlist'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { useDebouncedValue, usePedido } from '@/hooks'
import { colorCanasta, porcentaje, precio } from '@/lib/formato'
import { cn } from '@/lib/utils'

const DEBOUNCE_MS = 300

function App() {
  const [fecha, setFecha] = useState<string | null>(null)
  const [umbral, setUmbral] = useState(0.5)
  const [fuente, setFuente] = useState<Fuente>('modelo')
  const [ticker, setTicker] = useState('AAPL')
  const [vista, setVista] = useState('precio')
  const [vistaGrafo, setVistaGrafo] = useState<VistaGrafo>('conflicto')

  // El slider se mueve fluido, pero la API se consulta recién cuando se detiene.
  const umbralConsulta = useDebouncedValue(umbral, DEBOUNCE_MS)

  const fechas = usePedido((s) => getFechas(s), [])
  const fechaActiva = fecha ?? fechas.datos?.at(-1) ?? null
  const listo = fechaActiva !== null

  const acciones = usePedido((s) => getAcciones(fechaActiva!, s), [fechaActiva], listo)
  const grafo = usePedido((s) => getGrafo(fechaActiva!, umbralConsulta, fuente, s), [fechaActiva, umbralConsulta, fuente], listo)
  const canastas = usePedido((s) => getCanastas(fechaActiva!, umbralConsulta, fuente, s), [fechaActiva, umbralConsulta, fuente], listo)
  const complemento = usePedido(
    (s) => getComplemento(fechaActiva!, umbralConsulta, fuente, s),
    [fechaActiva, umbralConsulta, fuente],
    listo && vistaGrafo === 'complemento',
  )
  const curva = usePedido((s) => getChiPorUmbral(fechaActiva!, fuente, s), [fechaActiva, fuente], listo)
  const precios = usePedido((s) => getPrecios(ticker, s), [ticker])
  const comparacion = usePedido((s) => getComparaciones(s), [])
  const metricas = usePedido((s) => getMetricas(s), [])

  const error = fechas.error ?? acciones.error ?? grafo.error ?? complemento.error ?? canastas.error ?? curva.error ?? precios.error ?? comparacion.error ?? metricas.error
  const accion = acciones.datos?.find((a) => a.ticker === ticker)
  const canastaDeTicker = grafo.datos?.nodos.find((n) => n.id === ticker)?.canasta

  return (
    <div className="flex min-h-svh flex-col bg-background text-foreground lg:h-svh">
      {fechas.datos && fechaActiva && (
        <Toolbar
          fechas={fechas.datos}
          fecha={fechaActiva}
          onFecha={setFecha}
          umbral={umbral}
          onUmbral={setUmbral}
          fuente={fuente}
          onFuente={setFuente}
        />
      )}

      {error && (
        <Alert variant="destructive" className="m-3 w-auto">
          <AlertCircleIcon />
          <AlertTitle>No se pudo cargar</AlertTitle>
          <AlertDescription>
            {error}. ¿Está corriendo el backend en <code>localhost:8000</code>?
          </AlertDescription>
        </Alert>
      )}

      <div className="grid min-h-0 flex-1 grid-cols-1 lg:grid-cols-[17rem_minmax(0,1fr)_21rem]">
        <Watchlist acciones={acciones.datos} nodos={grafo.datos?.nodos ?? null} seleccionada={ticker} onSeleccionar={setTicker} />

        <main className="flex min-h-0 flex-col gap-3 overflow-y-auto p-4">
          <div className="flex flex-wrap items-baseline gap-x-4 gap-y-1">
            <h1 className="text-2xl font-semibold">{ticker}</h1>
            <span className="text-sm text-muted-foreground">{accion?.sector}</span>
            {accion && (
              <>
                <span className="text-2xl tabular-nums">{precio(accion.precio)}</span>
                <span className={cn('tabular-nums', accion.variacion !== null && (accion.variacion >= 0 ? 'text-up' : 'text-down'))}>
                  {porcentaje(accion.variacion)} en 1 mes
                </span>
              </>
            )}
            {canastaDeTicker !== undefined && (
              <span className="flex items-center gap-1.5 text-sm text-muted-foreground">
                <span className="size-2.5 rounded-full" style={{ background: colorCanasta(canastaDeTicker) }} />
                Canasta {canastaDeTicker + 1}
              </span>
            )}
          </div>

          <Tabs value={vista} onValueChange={(v) => setVista(String(v))} className={cn('min-h-80 flex-1', vista === 'grafo' && 'min-h-[36rem]', (vista === 'comparacion' || vista === 'modelo') && 'flex-none')}>
            <TabsList variant="line">
              <TabsTrigger value="precio">Precio</TabsTrigger>
              <TabsTrigger value="chi">Canastas según θ</TabsTrigger>
              <TabsTrigger value="grafo">Grafo</TabsTrigger>
              <TabsTrigger value="comparacion">Modelo vs histórica</TabsTrigger>
              <TabsTrigger value="modelo">Métricas del modelo</TabsTrigger>
            </TabsList>
            <TabsContent value="precio" className="min-h-0 flex-1">
              <GraficoPrecio ticker={ticker} puntos={precios.datos?.puntos ?? null} fechaCorte={fechaActiva ?? ''} />
            </TabsContent>
            <TabsContent value="chi" className="min-h-0 flex-1">
              <GraficoChi puntos={curva.datos?.puntos ?? null} umbral={umbral} />
            </TabsContent>
            <TabsContent value="grafo" className="min-h-0 flex-1">
              <GrafoCanastas
                grafo={grafo.datos}
                complemento={complemento.datos}
                vista={vistaGrafo}
                onVista={setVistaGrafo}
                umbral={umbralConsulta}
                seleccionada={ticker}
                onSeleccionar={setTicker}
              />
            </TabsContent>
            <TabsContent value="comparacion" className="shrink-0">
              <ComparacionCanastas datos={comparacion.datos} />
            </TabsContent>
            <TabsContent value="modelo" className="shrink-0">
              <MetricasModelo metricas={metricas.datos} />
            </TabsContent>
          </Tabs>

          <Explicacion />
        </main>

        <PanelCanastas grafo={grafo.datos} canastas={canastas.datos?.canastas ?? null} seleccionada={ticker} onSeleccionar={setTicker} />
      </div>
    </div>
  )
}

export default App
