# Frontend

Aplicación web del TP: React + TypeScript + Vite, con Tailwind v4 y componentes de shadcn/ui (tema oscuro). Consume la API del backend; las instrucciones para levantar todo el proyecto están en el [README principal](../README.md).

## Comandos

```bash
npm install      # dependencias
npm run dev      # servidor de desarrollo en http://localhost:5173
npm run build    # chequeo de tipos (tsc) y build de producción
npm run lint     # oxlint
```

El backend se espera en `http://localhost:8000`; se puede cambiar con la variable de entorno `VITE_API_URL`. El backend solo permite pedidos desde `http://localhost:5173`, por lo que el servidor de desarrollo tiene que usar ese puerto.

## Estructura

```
src/api.ts            cliente tipado de la API
src/hooks.ts          useDebouncedValue y usePedido (cancela pedidos anteriores)
src/App.tsx           pantalla principal: barra superior, watchlist, pestañas y panel de canastas
src/components/       componentes de la aplicación
src/components/ui/    componentes de shadcn/ui (generados con la CLI de shadcn)
src/lib/              utilidades (formato, layout del grafo)
```

Para agregar un componente de shadcn: `npx shadcn@latest add <componente>`.
