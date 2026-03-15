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
4. Asignar miembros reales a las tarjetas (no solo texto).
5. Ejecutar la publicacion delegando en el agente `publisher`.
6. Verificar que cada tarjeta tiene sus 3 operaciones completadas.
7. Reportar el resultado al usuario.

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

### Paso 2: Preparar vista previa y determinar lista destino

Lee la configuracion del tablero con el agente `publisher` (herramienta `get-board`) para obtener:
- Nombre del tablero.
- Listas disponibles.
- Etiquetas disponibles (para mapear las prioridades).

**Determinar la lista destino para cada HU:**

- Lee `docs/sprint-plan.md` si existe para saber que HUs estan en el sprint actual.
- HUs incluidas en el sprint -> lista **"Sprint actual"** (o "Sprint Backlog" si asi se llama en el tablero).
- HUs NO incluidas en ningun sprint -> lista **"Backlog"**.
- Si la lista destino no existe en el tablero, usa AskUserQuestion:
  - Pregunta: "La lista {nombre} no existe en el tablero. Que quieres hacer?"
  - Opciones:
    - **"Crear la lista"** (description: "Crea automaticamente la lista {nombre} en el tablero")
    - **"Seleccionar lista existente"** (description: "Elige una de las listas disponibles en el tablero")

IMPORTANTE: Usa siempre AskUserQuestion para presentar opciones. NUNCA listes opciones como texto plano.

Una vez confirmada la lista destino, lee cada fichero de `docs/historias/HU-*.md` para extraer:
- Titulo
- Prioridad (de la tabla de metadatos)
- Estimacion/talla (de la tabla de metadatos, si existe)
- Sprint asignado (si existe)
- Asignado a (nombre y email, si existe)
- Escenarios (nombres para el resumen)

Si las historias no tienen estimacion (talla), usa AskUserQuestion:
- Pregunta: "Algunas historias no tienen estimacion. Que quieres hacer?"
- Opciones:
  - **"Asignar tallas ahora"** (description: "Asigna S/M/L/XL a cada historia antes de publicar")
  - **"Publicar sin estimacion"** (description: "Publica las historias tal como estan, sin talla")

IMPORTANTE: Usa siempre AskUserQuestion para presentar opciones. NUNCA uses confirmaciones de texto plano.

Presenta la vista previa al usuario:

```
=== Vista previa de publicacion ===

Tablero destino: {nombre_tablero}
URL: {url_tablero}

Tarjetas a crear:

| # | Titulo | Prioridad | Talla | Lista destino | Asignado a |
|---|--------|-----------|-------|---------------|------------|
| 1 | HU-01: {titulo} | Alta | M | Sprint actual | Ana Garcia |
| 2 | HU-02: {titulo} | Media | L | Sprint actual | Pedro Lopez |
| 3 | HU-03: {titulo} | Alta | S | Backlog | Sin asignar |

Cada tarjeta incluira:
  - Descripcion resumida con prioridad y estimacion
  - Fichero .md completo como adjunto
  - Checklist "Definition of Done" (si configurada)
  - Miembro asignado (si esta en el tablero)
```

Usa AskUserQuestion para confirmar:
- Pregunta: "Confirmas la publicacion de {N} tarjetas en Trello?"
- Opciones:
  - **"Publicar"** (description: "Crea las {N} tarjetas en el tablero con adjuntos, checklists y miembros")
  - **"Cancelar"** (description: "No se publica nada, las historias siguen guardadas localmente")

IMPORTANTE: Usa siempre AskUserQuestion para presentar opciones. NUNCA uses confirmaciones de texto plano.

### Paso 3: Verificar duplicados

Antes de crear tarjetas, usa el agente `publisher` con la herramienta `search-cards` para buscar tarjetas existentes en el tablero que tengan titulos similares.

Si encuentra duplicados potenciales:

Muestra al usuario la tabla de duplicados potenciales y luego usa AskUserQuestion:
- Pregunta: "He encontrado posibles duplicados. Que quieres hacer?"
- Opciones:
  - **"Publicar todas de todos modos"** (description: "Se crearan tarjetas nuevas aunque haya duplicados")
  - **"Omitir duplicadas"** (description: "Publica solo las historias que no tienen duplicado en el tablero")
  - **"Cancelar publicacion"** (description: "No se publica nada, las historias siguen guardadas localmente")

IMPORTANTE: Usa siempre AskUserQuestion para presentar opciones. NUNCA listes opciones como texto plano.

### Paso 3b: Invitar miembros y obtener IDs

Si existe `team.csv`:

1. **Invitar miembros:** Lee los emails del equipo e invita a cada miembro al tablero usando `invite-member`. Este paso se ejecuta UNA VEZ. Si un miembro ya esta en el tablero, no pasa nada.

2. **Obtener IDs de miembros:** Usa `get-board-members` para obtener los miembros del tablero con sus IDs de Trello. Mapea cada miembro del team.csv con su ID de Trello (por nombre o username).

3. Informa brevemente: "Invitaciones enviadas a {N} miembros. {X} miembros mapeados para asignacion a tarjetas."

### Paso 4: Ejecutar la publicacion

Antes de publicar, pasa las descripciones de las tarjetas por el agente `culture-guardian` para asegurar que el texto que llega a Trello tiene acentos correctos, tono profesional y es detallista.

IMPORTANTE SOBRE PERMISOS: A partir de este punto, ejecuta TODAS las llamadas MCP de forma CONTINUA y AUTOMATICA. No pidas confirmacion al usuario entre tarjetas. El usuario ya confirmo en la vista previa.

**Procesamiento en lotes de 5 tarjetas:**

Para evitar perdida de contexto con muchas historias, procesa las tarjetas en lotes de 5:

**Para CADA lote:**

Para CADA historia del lote, ejecuta estos 3 pasos en orden:

1. **Crear tarjeta** con `create-cards`. La descripcion DEBE seguir el formato estandar del agente publisher. Incluir `idMembers` si el miembro asignado tiene ID de Trello mapeado. Enviar a la lista correcta (Sprint actual o Backlog segun sprint-plan.md).
2. **Adjuntar fichero .md** con `attach-file`: sube el fichero completo HU-XX-titulo.md como adjunto a la tarjeta recien creada.
3. **Anadir checklist DoD** con `add-checklist`: anade el checklist "Definition of Done" con los criterios de docs/dod.md (si existe).

Al terminar cada lote, muestra progreso:
```
Lote {N}/{total_lotes}: {X} tarjetas creadas. Continuando...
```

No pidas confirmacion individual por cada tarjeta ni entre lotes. La confirmacion se pide UNA SOLA VEZ en la vista previa. Despues, ejecuta todo sin interrupciones.

### Paso 5: Verificacion post-publicacion

Despues de crear todas las tarjetas, ejecuta una verificacion:

1. Usa `search-cards` con el agente `publisher` para obtener las tarjetas recien creadas.
2. Verifica que CADA tarjeta creada:
   - Existe en el tablero (por titulo HU-XX).
   - Tiene la descripcion correcta.
3. Si alguna tarjeta no se encuentra o falta informacion, incluyela en el reporte como "requiere revision manual".

### Paso 6: Reportar resultado

Muestra el resultado completo al usuario:

**Si todo fue exitoso:**

```
=== Publicacion completada ===

Se han creado {N} tarjetas en el tablero "{nombre_tablero}":

| # | Titulo | Lista | Miembro | URL |
|---|--------|-------|---------|-----|
| 1 | HU-01: {titulo} | Sprint actual | Ana Garcia | https://trello.com/c/... |
| 2 | HU-02: {titulo} | Sprint actual | Pedro Lopez | https://trello.com/c/... |
| 3 | HU-03: {titulo} | Backlog | -- | https://trello.com/c/... |

Cada tarjeta incluye:
  - Descripcion resumida con estimacion y prioridad
  - Fichero .md completo como adjunto
  - Checklist "Definition of Done" (si configurada)
  - Miembro asignado (si disponible en el tablero)

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

Este es el final del flujo. No preguntes que quiere hacer. Si el usuario quiere planificar sprint, exportar o hacer otra cosa, lo dira el.

## Reglas de seguridad

- NUNCA publiques sin confirmacion explicita del usuario (via AskUserQuestion).
- SIEMPRE guarda localmente antes de intentar publicar en Trello.
- Si las credenciales han expirado durante la publicacion, informa y guarda localmente.
- No reintentar automaticamente mas de 3 veces ante errores de API.

## Reglas de ejecucion

- La confirmacion del usuario se pide UNA SOLA VEZ en la vista previa.
- Despues de confirmar, se crean TODAS las tarjetas sin interrupciones.
- NUNCA pidas confirmacion individual por cada tarjeta ni entre lotes.
- Si una tarjeta falla, registrala en la lista de fallidas y continua con la siguiente.
- CADA tarjeta requiere 3 operaciones: create-cards + attach-file + add-checklist. Sin excepciones.
