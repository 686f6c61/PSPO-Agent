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

Muestra al usuario las listas disponibles en el tablero y luego usa AskUserQuestion para preguntar:
- Pregunta: "La lista Backlog no existe en el tablero {nombre_tablero}. Que quieres hacer?"
- Opciones:
  - **"Seleccionar lista existente"** (description: "Elige una de las listas disponibles en el tablero")
  - **"Crear lista Backlog"** (description: "Crea automaticamente la lista Backlog en el tablero")

IMPORTANTE: Usa siempre AskUserQuestion para presentar opciones. NUNCA listes opciones como texto plano con letras entre corchetes.

Si el usuario elige crear, usa `manage-lists` con accion `create` para crear la lista "Backlog".
Si elige seleccionar, usa la lista indicada como destino.

Una vez confirmada la lista destino, lee cada fichero de `docs/historias/HU-*.md` para extraer:
- Titulo
- Prioridad (de la tabla de metadatos)
- Estimacion/talla (de la tabla de metadatos, si existe)
- Escenarios (nombres para el resumen)

Si las historias no tienen estimacion (talla), pregunta al usuario si quiere asignarlas ahora (S/M/L/XL) o publicar sin estimacion.

Presenta la vista previa al usuario:

```
=== Vista previa de publicacion ===

Tablero destino: {nombre_tablero}
URL: {url_tablero}
Lista destino: Backlog

Tarjetas a crear:

| # | Titulo | Prioridad | Talla | Dias |
|---|--------|-----------|-------|------|
| 1 | HU-01: {titulo} | Alta | M | 2 |
| 2 | HU-02: {titulo} | Media | L | 3 |
| 3 | HU-03: {titulo} | Alta | S | 1 |

Cada tarjeta incluira:
  - Descripcion resumida con prioridad y estimacion
  - Fichero .md completo como adjunto
  - Checklist "Definition of Done" (8 criterios)

Confirmas la publicacion? (s/n):
```

### Paso 3: Verificar duplicados

Antes de crear tarjetas, usa el agente `publisher` con la herramienta `search-cards` para buscar tarjetas existentes en el tablero que tengan titulos similares.

Si encuentra duplicados potenciales:

Muestra al usuario la tabla de duplicados potenciales:

```
[!] He encontrado tarjetas existentes que podrian ser duplicados:

| Historia nueva | Tarjeta existente | URL |
|---------------|-------------------|-----|
| HU-01: {titulo} | {titulo_existente} | {url} |
```

Luego usa AskUserQuestion para preguntar:
- Pregunta: "He encontrado posibles duplicados. Que quieres hacer?"
- Opciones:
  - **"Publicar todas de todos modos"** (description: "Se crearan tarjetas nuevas aunque haya duplicados")
  - **"Omitir duplicadas"** (description: "Publica solo las historias que no tienen duplicado en el tablero")
  - **"Cancelar publicacion"** (description: "No se publica nada, las historias siguen guardadas localmente")

IMPORTANTE: Usa siempre AskUserQuestion para presentar opciones. NUNCA listes opciones como texto plano con letras entre corchetes.

### Paso 4: Ejecutar la publicacion

Antes de publicar, pasa las descripciones de las tarjetas por el agente `culture-guardian` para asegurar que el texto que llega a Trello tiene acentos correctos, tono profesional y es detallista.

IMPORTANTE SOBRE PERMISOS: A partir de este punto, ejecuta TODAS las llamadas MCP (create-cards, attach-file, add-checklist) de forma CONTINUA y AUTOMATICA. No pidas confirmacion al usuario entre tarjetas. No esperes aprobacion para cada operacion MCP. El usuario ya confirmo en la vista previa. Ejecuta todo el lote de una vez.

Para CADA historia aprobada, ejecuta estos 3 pasos en orden:

1. **Crear tarjeta** con `create-cards`. La descripcion DEBE seguir este formato exacto:
   ```
   ## Historia de usuario

   Como {rol}, quiero {accion}, para {beneficio}.

   ## Criterios de aceptacion (resumen)

   - Escenario 1: {nombre} (positivo)
   - Escenario 2: {nombre} (negativo)

   Prioridad: {prioridad} | Estimacion: {talla} ({dias} dias)

   ---
   *Historia completa en el fichero adjunto.*
   *Generado por PSPO Agent | {DD/MM/AAAA}*
   ```
   - **Titulo:** `HU-{XX}: {titulo corto}`
   - **Etiqueta:** La etiqueta de prioridad correspondiente.
   - **Lista destino:** "Backlog" (o la configurada en settings).
   - **Posicion:** Al final de la lista (bottom).
2. **Adjuntar fichero .md** con `attach-file`: sube el fichero completo HU-XX-titulo.md como adjunto a la tarjeta recien creada.
3. **Anadir checklist DoD** con `add-checklist`: anade el checklist "Definition of Done" con los criterios de docs/dod.md.

No pidas confirmacion individual por cada tarjeta. La confirmacion se pide UNA VEZ en la vista previa (paso 3). Despues de confirmar, crea TODAS las tarjetas secuencialmente sin interrupciones.

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
3. Si hay historias, presenta la lista en tabla y luego usa AskUserQuestion para preguntar:
   - Pregunta: "He encontrado {N} historias en docs/historias/. Cuales quieres publicar en Trello?"
   - Opciones:
     - **"Todas"** (description: "Publica todas las historias encontradas en el tablero de Trello")
     - **"Seleccionar"** (description: "Indica los numeros de las historias que quieres publicar, separados por coma")

   IMPORTANTE: Usa siempre AskUserQuestion para presentar opciones. NUNCA listes opciones como texto plano con letras entre corchetes.

4. Continua con el flujo normal (vista previa -> confirmacion -> publicacion).

### Paso 6: Proximos pasos

Usa AskUserQuestion para preguntar al usuario que quiere hacer a continuacion.
NUNCA muestres tablas de texto con comandos como proximos pasos. Siempre usa AskUserQuestion.

- Pregunta: "La publicacion ha terminado. Que quieres hacer ahora?"
- Opciones:
  - **"Planificar sprint"** (description: "Calcula capacidad del equipo y planifica el sprint con las historias publicadas") -> ejecuta /pspo-agent:sprint-plan
  - **"Exportar backlog"** (description: "Exporta el backlog completo a un fichero local") -> ejecuta /pspo-agent:save-docs
  - **"Volver al inicio"** (description: "Vuelve al menu principal del plugin")

## Reglas de seguridad

- NUNCA publiques sin confirmacion explicita del usuario.
- SIEMPRE guarda localmente antes de intentar publicar en Trello.
- Si las credenciales han expirado durante la publicacion, informa y guarda localmente.
- No reintentar automaticamente mas de 3 veces ante errores de API.

## Reglas de ejecucion

- La confirmacion del usuario se pide UNA SOLA VEZ en la vista previa (paso 3).
- Despues de confirmar, se crean TODAS las tarjetas sin interrupciones.
- NUNCA pidas confirmacion individual por cada tarjeta.
- Si una tarjeta falla, registrala en la lista de fallidas y continua con la siguiente.
