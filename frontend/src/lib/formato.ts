/** Color de una canasta: reparte los tonos para que canastas vecinas se distingan. */
export function colorCanasta(i: number): string {
  return `oklch(0.74 0.14 ${(i * 137.5) % 360})`
}

export const porcentaje = (x: number | null, signo = true) =>
  x === null ? '–' : `${signo && x > 0 ? '+' : ''}${(x * 100).toFixed(2)}%`

export const precio = (x: number) => x.toLocaleString('es-AR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
