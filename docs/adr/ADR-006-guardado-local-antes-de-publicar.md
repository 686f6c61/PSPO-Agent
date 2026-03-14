# ADR-006: Guardar localmente antes de publicar en Trello

| Campo | Valor |
|-------|-------|
| **Estado** | Aceptado |
| **Fecha** | 2026-03-13 |
| **Autor** | El Dibujante de Cajas |

## Contexto

El flujo del plugin termina con dos acciones: guardar artefactos en `docs/` (HU-06) y publicar tarjetas en Trello (HU-05). Estas dos acciones podrian hacerse en cualquier orden o en paralelo.

Si la publicacion en Trello falla (error de red, rate limiting, credenciales expiradas), las historias que el usuario acaba de aprobar podrian perderse si no se han guardado en ningun sitio.

## Opciones consideradas

### Opcion A: Publicar en Trello primero, guardar local despues

- **Pros:** El usuario ve el resultado en Trello inmediatamente.
- **Contras:** Si Trello falla, las historias aprobadas se pierden (solo estan en memoria del LLM). Si la sesion se interrumpe despues de publicar pero antes de guardar, no hay copia local.

### Opcion B: Guardar local primero, publicar en Trello despues

- **Pros:** Las historias aprobadas SIEMPRE se persisten antes de cualquier operacion de red. Si Trello falla, el usuario tiene la copia completa en docs/. Se puede reintentar la publicacion en otra sesion.
- **Contras:** Ligeramente mas lento (escritura en disco antes de HTTP). El usuario ve los ficheros locales antes que las tarjetas en Trello.

### Opcion C: Publicar y guardar en paralelo

- **Pros:** Mas rapido (ambas operaciones concurrentes).
- **Contras:** Si la publicacion falla y el guardado tambien, se pierde todo. Mas dificil de gestionar errores parciales. Complejidad innecesaria.

## Decision

**Opcion B: Guardar local primero.**

El principio es simple: nunca perder datos. Un fichero en disco es mas fiable que una peticion HTTP a un servicio externo. El orden es:

1. El usuario aprueba las historias.
2. Se guardan en `docs/` (HU-06).
3. Se muestra la vista previa de lo que se publicara en Trello.
4. El usuario confirma la publicacion.
5. Se publican las tarjetas en Trello (HU-05).

Si el paso 5 falla, el usuario tiene todo en `docs/` y puede reintentar con `/pspo-agent:publish`.

## Consecuencias

- **Ganancia:** Las historias nunca se pierden, independientemente de fallos de red o Trello.
- **Coste:** El flujo tiene un paso intermedio de escritura en disco antes de publicar.
- **Deuda tecnica:** Ninguna. Este orden es definitivo y no genera problemas futuros.
