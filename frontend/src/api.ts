export const API_URL: string = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

export type Fuente = 'modelo' | 'corr_90d' | 'azar'

export const FUENTES: { valor: Fuente; etiqueta: string }[] = [
  { valor: 'modelo', etiqueta: 'Modelo' },
  { valor: 'corr_90d', etiqueta: 'Histórica' },
  { valor: 'azar', etiqueta: 'Azar' },
]

export const UMBRAL_MIN = -0.2
export const UMBRAL_MAX = 1

export interface Nodo {
  id: string
  canasta: number
  grado: number
}

export interface Arista {
  source: string
  target: string
  peso: number
}

export interface Grafo {
  fecha: string
  umbral: number
  fuente: Fuente
  chi: number
  nodos: Nodo[]
  aristas: Arista[]
}

export interface Complemento {
  fecha: string
  umbral: number
  fuente: Fuente
  nodos: string[]
  aristas: Arista[]
  grafo_original_bipartito: boolean
}

export interface PuntoChi {
  umbral: number
  aristas: number
  chi: number
}

export interface ChiPorUmbral {
  fecha: string
  fuente: Fuente
  puntos: PuntoChi[]
}

export interface Accion {
  ticker: string
  sector: string
  precio: number
  variacion: number | null
}

export interface PuntoPrecio {
  fecha: string
  precio: number
}

export interface Canasta {
  canasta: number
  acciones: string[]
  correlacion_promedio_interna: number | null
}

export interface Canastas {
  fecha: string
  umbral: number
  fuente: Fuente
  canastas: Canasta[]
}

async function pedir<T>(ruta: string, params: Record<string, string | number>, signal: AbortSignal): Promise<T> {
  const query = new URLSearchParams(Object.entries(params).map(([k, v]) => [k, String(v)]))
  const respuesta = await fetch(`${API_URL}${ruta}?${query}`, { signal })
  if (!respuesta.ok) {
    const detalle = await respuesta.json().catch(() => null)
    throw new Error(typeof detalle?.detail === 'string' ? detalle.detail : `Error ${respuesta.status} en ${ruta}`)
  }
  return respuesta.json() as Promise<T>
}

export const getFechas = (signal: AbortSignal) => pedir<string[]>('/fechas', {}, signal)

export const getGrafo = (fecha: string, umbral: number, fuente: Fuente, signal: AbortSignal) =>
  pedir<Grafo>('/grafo', { fecha, umbral, fuente }, signal)

export const getChiPorUmbral = (fecha: string, fuente: Fuente, signal: AbortSignal) =>
  pedir<ChiPorUmbral>('/chi-por-umbral', { fecha, fuente }, signal)

export const getAcciones = (fecha: string, signal: AbortSignal) => pedir<Accion[]>('/acciones', { fecha }, signal)

export const getPrecios = (ticker: string, signal: AbortSignal) =>
  pedir<{ ticker: string; puntos: PuntoPrecio[] }>(`/precios/${ticker}`, {}, signal)

export const getCanastas = (fecha: string, umbral: number, fuente: Fuente, signal: AbortSignal) =>
  pedir<Canastas>('/canastas', { fecha, umbral, fuente }, signal)

export const getComplemento = (fecha: string, umbral: number, fuente: Fuente, signal: AbortSignal) =>
  pedir<Complemento>('/complemento', { fecha, umbral, fuente }, signal)
