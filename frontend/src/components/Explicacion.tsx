import { InfoIcon } from 'lucide-react'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible'
import { Button } from '@/components/ui/button'

/** Explicación en lenguaje llano de qué muestra la pantalla. */
export function Explicacion() {
  return (
    <Collapsible defaultOpen>
      <Alert>
        <InfoIcon />
        <AlertTitle className="flex items-center justify-between">
          ¿Qué estoy viendo?
          <CollapsibleTrigger render={<Button variant="ghost" size="xs" />}>Mostrar / ocultar</CollapsibleTrigger>
        </AlertTitle>
        <AlertDescription>
          <CollapsibleContent className="flex flex-col gap-2 pt-1">
            <p>
              Pensalo como repartir <strong>30 invitados en mesas</strong>. Algunos se llevan mal y no pueden compartir mesa:
              acá, dos acciones &quot;se llevan mal&quot; si sus precios suben y bajan juntos (están muy correlacionadas), porque
              tener las dos casi no diversifica. Cada mesa es una <strong>canasta</strong>.
            </p>
            <p>
              El <strong>umbral θ</strong> es qué tan quisquilloso sos: dos acciones pelean si su correlación supera θ. Con θ bajo
              pelean casi todas y hacen falta 30 canastas; con θ alto casi nadie pelea y alcanza con 1. La pestaña{' '}
              <strong>Canastas según θ</strong> muestra esa curva.
            </p>
            <p>
              En el gráfico de precio, la línea punteada es la fecha de corte y la zona sombreada son las 60 ruedas siguientes,
              cuya correlación es lo que el modelo intenta anticipar.
            </p>
          </CollapsibleContent>
        </AlertDescription>
      </Alert>
    </Collapsible>
  )
}
