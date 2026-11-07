import { useEffect, useState } from 'react'

/** Devuelve `valor` recién después de que dejó de cambiar durante `ms`. */
export function useDebouncedValue<T>(valor: T, ms: number): T {
  const [debounced, setDebounced] = useState(valor)
  useEffect(() => {
    const id = setTimeout(() => setDebounced(valor), ms)
    return () => clearTimeout(id)
  }, [valor, ms])
  return debounced
}

export interface Pedido<T> {
  datos: T | null
  error: string | null
  cargando: boolean
}

/**
 * Ejecuta `pedir` cada vez que cambian `deps` y cancela el pedido anterior
 * (evita que una respuesta vieja pise a una más nueva).
 * Si `habilitado` es false no pide nada.
 */
export function usePedido<T>(
  pedir: (signal: AbortSignal) => Promise<T>,
  deps: unknown[],
  habilitado = true,
): Pedido<T> {
  const [estado, setEstado] = useState<Pedido<T>>({ datos: null, error: null, cargando: habilitado })

  useEffect(() => {
    if (!habilitado) return
    const control = new AbortController()
    setEstado((e) => ({ ...e, error: null, cargando: true }))
    pedir(control.signal)
      .then((datos) => setEstado({ datos, error: null, cargando: false }))
      .catch((err: unknown) => {
        if (control.signal.aborted) return
        setEstado((e) => ({ ...e, error: err instanceof Error ? err.message : String(err), cargando: false }))
      })
    return () => control.abort()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...deps, habilitado])

  return estado
}
