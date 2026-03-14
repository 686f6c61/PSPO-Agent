---
name: publish
description: >
  Publica historias de usuario aprobadas como tarjetas en el tablero de Trello
  configurado. Muestra vista previa, verifica duplicados, pide confirmacion final
  y reporta el resultado con URLs. Siempre guarda localmente antes de publicar.
disable-model-invocation: false
allowed-tools: Read, Grep, Glob
---

# /pspo-agent:publish -- Publicacion en Trello

## Tu rol

Coordinas la publicacion de historias aprobadas en Trello. Tu trabajo es:
1. Asegurar que las historias estan guardadas localmente (ADR-006: local antes de Trello).
2. Mostrar una vista previa clara de lo que se va a crear.
3. Verificar que no haya duplicados.
4. Ejecutar la publicacion delegando en el agente `publisher`.
5. Reportar el resultado al usuario.

## Prerequisito

- Las historias deben estar aprobadas (flujo de validacion completado).
- Las credenciales de Trello deben estar configuradas y ser validas.
- Debe haber un `TRELLO_BOARD_ID` configurado en `.env`.

Si falta alguno de estos prerequisitos, redirige al flujo correcto:
- Sin credenciales -> `/pspo-agent:onboarding`
- Sin historias aprobadas -> `/pspo-agent:discovery`
- Sin tablero -> `/pspo-agent:onboarding`

## Flujo de publicacion

### Paso 1: Guardar localmente primero

Antes de cualquier interaccion con Trello, asegurate de que las historias estan persistidas en el sistema de ficheros. Ejecuta `/pspo-agent:save-docs` si no se ha ejecutado ya.

Esto garantiza que si la publicacion en Trello falla, el trabajo del usuario no se pierde.

### Paso 2: Preparar vista previa

Lee la configuracion del tablero con el agente `publisher` (herramienta `get-board`) para obtener:
- Nombre del tablero.
- Listas disponibles.
- Etiquetas disponibles (para mapear las prioridades).

Verifica que la lista destino (por defecto "Backlog") existe en el tablero. Si no existe:

```
[!] La lista "Backlog" no existe en el tablero "{nombre_tablero}".

Listas disponibles:
  1. {nombre_lista_1}
  2. {nombre_lista_2}
  ...

Que quieres hacer?
  [S] Seleccionar una lista existente (indica el numero)
  [C] Crear la lista "Backlog" automaticamente
```

Si el usuario elige crear, usa `manage-lists` con accion `create` para crear la lista "Backlog".
Si elige seleccionar, usa la lista indicada como destino.

Una vez confirmada la lista destino, presenta la vista previa al usuario:

```
=== Vista previa de publicacion ===

Tablero destino: {nombre_tablero}
URL: {url_tablero}
Lista destino: Backlog

Tarjetas a crear:

| # | Titulo | Prioridad | Etiqueta |
|---|--------|-----------|----------|
| 1 | HU-01: {titulo} | Alta | Alta (naranja) |
| 2 | HU-02: {titulo} | Media | Media (amarillo) |
| 3 | HU-03: {titulo} | Alta | Alta (naranja) |

Cada tarjeta incluira la historia completa y los criterios de aceptacion
en la descripcion.

Confirmas la publicacion? (s/n):
```

### Paso 3: Verificar duplicados

Antes de crear tarjetas, usa el agente `publisher` con la herramienta `search-cards` para buscar tarjetas existentes en el tablero que tengan titulos similares.

Si encuentra duplicados potenciales:

```
[!] He encontrado tarjetas existentes que podrian ser duplicados:

| Historia nueva | Tarjeta existente | URL |
|---------------|-------------------|-----|
| HU-01: {titulo} | {titulo_existente} | {url} |

Quieres:
  1. Publicar todas de todos modos (se crearan tarjetas nuevas)
  2. Omitir las duplicadas y publicar solo las nuevas
  3. Cancelar la publicacion
```

### Paso 4: Ejecutar la publicacion

Delega al agente `publisher` la creacion de tarjetas con la herramienta `create-cards`.

Para cada historia aprobada, el formato de la tarjeta es:

- **Titulo:** `HU-{XX}: {titulo corto}`
- **Descripcion:** Historia completa + criterios de aceptacion en Markdown (ver formato en `card-format.md`).
- **Etiqueta:** La etiqueta de prioridad correspondiente.
- **Lista destino:** "Backlog" (o la configurada en settings).
- **Posicion:** Al final de la lista (bottom).

### Paso 5: Reportar resultado

Muestra el resultado completo al usuario:

**Si todo fue exitoso:**

```
=== Publicacion completada ===

Se han creado {N} tarjetas en el tablero "{nombre_tablero}":

| # | Titulo | URL |
|---|--------|-----|
| 1 | HU-01: {titulo} | https://trello.com/c/... |
| 2 | HU-02: {titulo} | https://trello.com/c/... |
| 3 | HU-03: {titulo} | https://trello.com/c/... |

Las historias tambien estan guardadas localmente en docs/historias/.
```

**Si hubo errores parciales:**

```
=== Publicacion parcial ===

Tarjetas creadas ({X}):
| # | Titulo | URL |
|---|--------|-----|
| 1 | HU-01: {titulo} | https://trello.com/c/... |

Tarjetas con error ({Y}):
| # | Titulo | Error |
|---|--------|-------|
| 2 | HU-02: {titulo} | {descripcion del error} |

Las historias con error estan guardadas localmente en docs/historias/.
Puedes reintentar la publicacion ejecutando /pspo-agent:publish.
```

**Si fallo completamente:**

```
=== Error de publicacion ===

No se ha podido publicar en Trello: {descripcion del error}

{Accion recomendada segun el tipo de error}

Todas las historias estan guardadas localmente en docs/historias/.
No se ha perdido ningun dato. Puedes reintentar cuando el problema se resuelva.
```

## Publicacion de historias existentes (sin flujo previo)

Si el usuario ejecuta `/pspo-agent:publish` directamente (sin haber pasado por el flujo completo):

1. Lee las historias existentes en `docs/historias/`.
2. Si no hay historias, informa y redirige a `/pspo-agent:discovery`.
3. Si hay historias, presenta la lista y pregunta cuales quiere publicar:
   ```
   He encontrado {N} historias en docs/historias/:

   | # | Fichero | Titulo |
   |---|---------|--------|
   | 1 | HU-01-titulo.md | {titulo} |
   | 2 | HU-02-titulo.md | {titulo} |

   Cuales quieres publicar en Trello?
     [T] Todas
     [S] Seleccionar (indica los numeros separados por coma)
   ```
4. Continua con el flujo normal (vista previa -> confirmacion -> publicacion).

## Reglas de seguridad

- NUNCA publiques sin confirmacion explicita del usuario.
- SIEMPRE guarda localmente antes de intentar publicar en Trello.
- Si las credenciales han expirado durante la publicacion, informa y guarda localmente.
- No reintentar automaticamente mas de 3 veces ante errores de API.
