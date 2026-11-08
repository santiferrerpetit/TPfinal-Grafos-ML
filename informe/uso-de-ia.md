# Uso de inteligencia artificial en el TP

> Este documento es el detalle de la sección 10 del informe (`informe.md`), que lo integra junto con el resto del trabajo.

## 1. Herramientas usadas

- **Claude Code** (CLI de Anthropic, modelos Claude), corriendo dentro del repo. Leía y editaba archivos, ejecutaba `pytest` y los scripts, y hacía los commits cuando se lo pedíamos.
- **Archivo `CLAUDE.md`** con las reglas del dominio (sin fuga de información, split temporal, algoritmos de grafos a mano, librerías permitidas), para que respetara las restricciones del TP en cada sesión. Está en `.gitignore` (decisión 9).
- **Memoria de Claude Code**: quedó guardada la regla de usar solo numpy, pandas, matplotlib y sklearn.
- **Gemini** (Google), para investigar el tema base y qué proyectos parecidos existían en la red, antes de trabajarlo con Claude.

## 2. Para qué partes sí y para cuáles no

**Sí se usó (código, tests y documentación):**

| Parte | Qué hizo Claude |
|---|---|
| Descarga y dataset por pares | Script de `yfinance`, features rodantes y el test anti-fuga (decisión 14) |
| Modelos | Split temporal, validación con gap, comparación contra el baseline `corr_90d` |
| Grafo de conflicto | Clase `GrafoConflicto` con matriz de adyacencia y fuentes de pesos intercambiables (decisión 22) |
| Algoritmos de grafos | Coloreo greedy por grado, DSATUR, bipartito, complemento, nodos de quiebre, Prim y polinomio cromático, con sus tests (decisiones 23 a 25) |
| Evaluación de canastas | Modelo vs `corr_90d` vs azar con varias semillas (decisión 26) |
| API y frontend | Endpoints FastAPI, interfaz React con grafo animado estilo Obsidian, MST, quiebre y polinomio |
| Documentación | `decisiones.md`, `preguntas-informe.md`, `ACCIONES.md`, y este documento |
**Lo decidimos nosotros, sin delegarlo:**

- El tema del proyecto, que después trabajamos con Claude hasta llegar a una propuesta bien planteada (`PROPUESTA.md`, 20/10), y su aprobación por parte de los docentes.
- La elección final de las acciones y de los sectores (editamos `sectores.csv` a mano) y el cambio de `^GSPC` a `SPY` por confianza en el instrumento (decisión 11).
- Qué features implementar y en qué orden: pegábamos cada ítem de la lista de tareas como prompt.
- Las librerías permitidas (numpy, pandas, matplotlib, sklearn). Esto hizo que se reemplazara `networkx` en `app/` por `matplotlib` (decisión 27).
- Cómo trabajar entre los dos: como ya trabajamos mucho juntos, definimos pautas para facilitar la cooperación, como documentar cada decisión y pedirle a la IA cosas que ya conocemos, por ejemplo la estética de grafo de Obsidian.
- Reducir lo desconocido y movernos dentro del entorno que nos dieron los profes en las materias: hicimos notebooks como los del curso de ML para que se comprenda mejor el código, y una interfaz parecida a los ejercicios de coloreo que resolvimos en clase, pero más linda.
- Tener las suites de tests necesarias para detectar errores de código.
- La revisión de cada cambio y los commits atómicos.

## 3. Ejemplos concretos de prompts útiles

1. **Pasar el enunciado de la tarea tal cual y pedir preguntas antes de hacer nada**: *"Tenemos que implementar esto ahora, haceme todas las preguntas que necesites, explicame qué hiciste: [lista de la tarea de coloreo greedy]"*. Evitó suposiciones sobre el diseño.
2. **Pedir una verificación del trabajo contra lo pedido**: *"¿Cumpliste con todo lo que te pedí en el prompt anterior? Haceme una lista de cómo lo resolviste"*. Sirvió para detectar faltantes.
3. **Pedir que compare con alternativas**: *"Armá la tabla comparativa, quiero saber más sobre el test de bipartito, ¿qué significa que no se cumpla en general?"*. Salió `comparacion_coloreo.md` (greedy vs DSATUR).
4. **Pedir una explicación antes de aceptar el código**: *"Explicame en qué consiste la implementación tuya de esta feature"* y *"¿Qué es el d de Prim?"*. Necesario para poder defender el TP oralmente.
5. **Preguntar por el comportamiento esperado**: *"¿Qué tendría que pasar cuando tengo un theta muy bajo o muy alto? ¿Y cuando tengo una fecha de crisis?"*. De ahí salió un hallazgo para el informe (ver «Controles» al final de la sección 4).
6. **Fijar restricciones**: *"Usemos siempre numpy, pandas y matplotlib"* y *"Hacé la estética del grafo oscilante como los grafos de bóvedas en Obsidian"*.
7. **Registrar mientras se trabaja**: *"Anotá lo que hiciste"* y *"anotalo en preguntas-informe"*. Así las decisiones quedaron documentadas con la fecha.

## 4. Casos donde la IA se equivocó y cómo nos dimos cuenta

1. **Test con valor esperado equivocado (5/11).** Claude armó los tests de la construcción del grafo y uno falló: esperaba una arista A-C con ρ = 0,5 y θ = 0,5, pero la arista exige ρ > θ estricto, así que no existe. Lo detectó `pytest` al correrlo, Claude reconoció que el error estaba en el test y no en el código, y corrigió lo esperado. Se anotó la regla de la desigualdad estricta en la decisión 22.
2. **Documentación en el lugar equivocado (8/11).** Al registrar la estética del grafo, Claude escribió el texto fuera de la decisión que correspondía. Lo vio al releer el archivo y lo movió. Lección: revisar los `.md` igual que el código.
3. **Se implementó sin la lista completa (6/11).** Claude implementó una feature a partir de un pedido incompleto (nos habíamos olvidado de pegar la lista). Lo notamos al leer el resumen y pedimos *"borrá los cambios que hiciste después del commit"*. Fue un error nuestro de prompt, pero muestra que Claude avanza con lo que tiene en vez de frenar. Después pegamos siempre la lista completa.
4. **Interfaces iniciales difíciles de entender.** Las primeras interfaces que generó la IA eran confusas para nosotros, y hubo que corregirlas hasta que fueran legibles, aunque quedaran más pesadas para la computadora. Lo notamos al probarlas a mano y tratar de explicarlas, algo que tenemos que poder hacer en la defensa oral.
5. **Archivo de prueba que no corría (5/11).** Nuestro script `probar_grafo.py` fallaba. Claude creó una versión corregida y dejó el original, porque el sistema bloqueó el borrado de un archivo nuestro, así que quedaron dos copias. Se limpió después: hoy ya no queda ninguna en el repositorio.
6. **README incompleto (8/11).** Al levantar el frontend y el backend siguiendo solo el README, vimos que faltaba el paso de entrenar el modelo en la secuencia de comandos. Sin ese paso la app no iba a funcionar cuando la probaran los profes. Lo corregimos en el README.

**Controles que evitaron conclusiones falsas** (no son errores de la IA, pero conviene registrarlos):

- El test de fuga (decisión 14) se verificó metiendo una fuga a propósito para comprobar que el test falla. Un test que nunca falla no prueba nada.
- La comparación modelo vs `corr_90d` a igual θ **no es justa**: el modelo predice correlaciones comprimidas hacia la media, genera grafos más ralos y usa menos canastas (3,3 vs 6,9 con θ = 0,5), lo que empeora su métrica (decisión 26). Y en una fecha de crisis el modelo casi no reacciona, mientras que la histórica sí. Esto salió al preguntarle a Claude qué debería pasar y contrastarlo con los datos.

## 5. Reflexión breve

Claude nos permitió llegar a un TP más completo del que habríamos hecho solos en el tiempo disponible: además de lo obligatorio, quedaron DSATUR, el polinomio cromático, Prim, la API y una interfaz interactiva. Nosotros nos ocupamos de planear, testear y revisar; la IA implementaba. Para no perder el control, pedimos explicaciones, hicimos que los algoritmos de grafos se implementaran a mano (los pide la materia) y los contrastamos con `networkx` en los tests.

Los errores que aparecieron fueron de criterio más que de sintaxis: un caso borde mal calculado, una interfaz confusa, un pedido incompleto que se ejecutó igual. Los atajaron los tests y la lectura crítica. Lo más difícil al trabajar con una IA no es la implementación, sino explicar bien el problema y la solución como los necesita el usuario. La IA no reemplaza saber qué se está midiendo ni poder defenderlo oralmente.
