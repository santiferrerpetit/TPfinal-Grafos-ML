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

export type NombreVariante = 'modelo' | 'modelo + pesos' | 'corr_90d' | 'azar'

export interface VarianteComparada {
  variante: NombreVariante
  corr_media: number | null
  conflictos: number | null
  canastas: number | null
  aristas: number | null
}

export interface Comparacion {
  umbral: number
  fecha: string | null
  variantes: VarianteComparada[]
  azar_desvio_corr_media: number | null
  fechas: number
}

export interface ComparacionPorUmbral {
  umbrales: number[]
  porUmbral: Record<number, Comparacion>
}

/** Comparación en todos los umbrales evaluados (promedio de las fechas de test). */
export async function getComparaciones(signal: AbortSignal): Promise<ComparacionPorUmbral> {
  const { umbrales } = await pedir<{ umbrales: number[] }>('/comparacion/opciones', {}, signal)
  const lista = await Promise.all(umbrales.map((umbral) => pedir<Comparacion>('/comparacion', { umbral }, signal)))
  return { umbrales, porUmbral: Object.fromEntries(umbrales.map((u, i) => [u, lista[i]])) }
}

export type NombreModelo = 'baseline' | 'regresion_lineal' | 'knn' | 'arbol'

export interface MetricasModelo {
  mae: number
  rmse: number
  r2: number
}

export interface Metricas {
  elegido: NombreModelo
  train: { filas: number; desde: string; hasta: string }
  test: { filas: number; desde: string; hasta: string }
  ajuste: Record<string, { parametros: Record<string, number>; mae_validacion: number }>
  test_metricas: Record<NombreModelo, MetricasModelo>
  por_segmento: Record<string, { n: number } & Record<NombreModelo, MetricasModelo>>
}

export const getMetricas = (signal: AbortSignal) => pedir<Metricas>('/metricas', {}, signal)
