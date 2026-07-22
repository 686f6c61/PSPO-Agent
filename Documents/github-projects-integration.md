# Integración GitHub Projects

## Objetivo

Documentar la integración de PSPO Agent con GitHub Projects v2 para publicar las
historias sin plantillas previas, manteniendo el mismo contrato de negocio que
Trello y Notion. El plugin crea un Project v2 privado del usuario y publica cada
historia como draft item con su estado.

Estado actual:

- `product-phase` sigue generando artefactos locales en `docs/`
- `onboarding` y `publish` actúan como routers por proveedor
- GitHub crea la estructura desde cero por la API GraphQL de Projects v2

## Ficheros implicados

- selector de proveedor:
  [`../hooks/scripts/publish-provider.py`](../hooks/scripts/publish-provider.py)
- fallback oficial:
  [`../servers/github-fallback.py`](../servers/github-fallback.py)
- estado autónomo:
  [`../hooks/scripts/autopilot-guard.py`](../hooks/scripts/autopilot-guard.py)
- configuración global:
  [`../settings.json`](../settings.json)
- ejemplo de credenciales:
  [`../.env.example`](../.env.example)
- skill de onboarding:
  [`../skills/onboarding/SKILL.md`](../skills/onboarding/SKILL.md)
- skill de publicación:
  [`../skills/publish/SKILL.md`](../skills/publish/SKILL.md)

## Autenticación

Backend primario: la CLI `gh` autenticada (`gh auth login`). El fallback usa
`gh api graphql`. Si `gh` no está disponible, cae a GraphQL directo con `urllib`
usando `GITHUB_TOKEN` o `GH_TOKEN`.

Projects v2 requiere el scope `project`. Si falta:

```bash
gh auth refresh -s project
```

o genera un token personal con el scope `project` (control total). `read:project`
es solo lectura y no basta para crear proyectos ni escribir items.

## Contrato `.env`

Variables (todas opcionales; `gh` autenticado con scope `project` basta para
crear el proyecto):

- `GITHUB_TOKEN` / `GH_TOKEN`: token personal como fallback sin `gh`
- `GITHUB_PROJECT_NUMBER`: número del Project v2 del usuario
- `GITHUB_PROJECT_ID`: node id del Project v2
- `GITHUB_PROJECT_OWNER`: login del propietario
- `GITHUB_PROJECT_URL`: URL del Project v2

Interpretación en `publish-provider.py`:

- GitHub se considera configurado si hay un token propio en `.env` o si ya hay
  targets persistidos (`GITHUB_PROJECT_ID`/`GITHUB_PROJECT_NUMBER`)
- la autenticación global de `gh` no reconfigura por sí sola cada proyecto: la
  resuelve el fallback y la superficie el `env-status` para que el onboarding
  pueda ofrecer GitHub

## Estructura zero-template

`create-project` hace:

1. resuelve el usuario autenticado (`viewer`)
2. crea el Project v2 con título `PSPO · {nombre_proyecto}`
3. lo marca como privado y le pone `shortDescription` y `readme`
   (`updateProjectV2` con `public: false`, `shortDescription`, `readme`)
4. materializa el esquema de campos completo (ver abajo)

## Esquema de campos

Cada metadato de la HU va a su propio campo, igual que en Trello y Notion:

| Campo | Tipo | Origen en la HU |
|---|---|---|
| `Status` | single-select (nativo) | Estado de la HU o derivado del sprint |
| `Prioridad` | single-select | Prioridad (Critica/Alta/Media/Baja) |
| `Talla` | single-select | Estimacion t-shirt (XS/S/M/L/XL) |
| `Horas` | número | Horas efectivas de la estimacion |
| `Sprint` | single-select | Sprint (creado bajo demanda por HU) |
| `Responsable` | texto | `Nombre (email)` de la persona asignada |

Detalles:

- El campo **Status** es el nativo del proyecto. Sus opciones se editan por API
  con `updateProjectV2Field` (`singleSelectOptions` admite `name`, `color` y
  `description`), dejando las 6 opciones estándar con descripcion semántica:
  Backlog, Sprint activo, Bloqueada, En progreso, En revision, Hecho.
- **Prioridad** y **Talla** se crean con `createProjectV2Field` (single-select).
- **Horas** (NUMBER) y **Responsable** (TEXT) se crean con `createProjectV2Field`.
- **Sprint** se crea bajo demanda: la primera HU con sprint materializa el campo,
  y cada sprint nuevo se añade como opción.
- Cada valor de item se fija con `updateProjectV2ItemFieldValue`
  (`ProjectV2FieldValue` admite `text`, `number` y `singleSelectOptionId`).
- Además del `Responsable` (texto), el item recibe el **assignee real** de GitHub
  cuando el CSV de equipo aporta el login (`assigneeIds` en el draft issue).

## Autodocumentación del kanban

`create-project` deja el proyecto autodocumentado:

- `shortDescription`: una línea que resume el backlog.
- `readme` (campo `readme` de `updateProjectV2`): tabla de estados del kanban con
  su significado y regla de transición, glosario de campos y las vistas
  recomendadas.

## Comandos del fallback

- `env-status`: estado local de autenticación (`gh`/token) y targets persistidos
- `verify-credentials`: usuario autenticado y comprobación del scope `project`
- `create-project`: crea el Project v2 privado y el campo `Estado`
- `setup-targets`: crea el proyecto y persiste los targets en un paso
- `save-project-targets`: persiste `GITHUB_PROJECT_*` en `.env`
- `sync-vision-from-markdown`: crea o actualiza el item `HU-00 · Vision`
- `parse-story-markdown`: parsea una HU local (metadatos y dependencias)
- `find-story-item`: localiza un item por `HU-XX` (diagnóstico y dedupe)
- `set-story-status`: fija el `Estado` de un item (diagnóstico)
- `sync-story-from-markdown`: crea o actualiza el draft item de una HU
- `sync-stories-from-folder`: lote en dos pasadas + `docs/publish-report.md`

## Contrato de publicación en GitHub

Cada HU publicada conserva el mismo contrato de negocio:

1. el cuerpo del draft item lleva el markdown EN BRUTO de la HU (GitHub lo
   renderiza nativamente, incluidos los diagramas Mermaid), con la DoD como task
   list markdown (`- [ ]`) al final, que GitHub muestra como progreso de tareas
2. cada metadato se mapea a su campo: Status, Prioridad, Talla, Horas, Sprint,
   Responsable
3. el `Status` refleja el estado de la HU (o se deriva del sprint)
4. dedupe por título `HU-XX`: no se crean items duplicados
5. la segunda pasada resuelve dependencias `HU-XX` a item ids como trazabilidad

## Límites reales de la API

Sí soporta:

- crear un Project v2 privado del usuario
- editar las opciones del campo Status nativo (`updateProjectV2Field`)
- crear campos single-select, número y texto (`createProjectV2Field`)
- crear y actualizar draft items con cuerpo markdown y assignees reales
- fijar text/number/single-select de cada item (`updateProjectV2ItemFieldValue`)
- `readme` y `shortDescription` del proyecto (`updateProjectV2`)

No hay equivalencia limpia con Trello/Notion para:

- **crear vistas** de Project v2: la API pública no expone mutaciones de vistas
  (`ProjectV2View`), así que el README del proyecto documenta las dos vistas
  recomendadas para crearlas a mano en 30 segundos: tablero agrupado por Status y
  tabla agrupada por Sprint.
- adjuntar ficheros a un draft item (por eso el markdown completo va en el cuerpo)
- asignar por email: GitHub necesita el login de GitHub; si el CSV de equipo
  compatible trae una columna opcional `github` con el login, se usa; si no, la
  HU se reporta como asignación pendiente en `unresolvedAssignments`
- relaciones nativas entre draft items: las dependencias se resuelven a item ids
  como trazabilidad, no como relación de proyecto

## Regla de selección de proveedor

1. si solo hay un proveedor configurado, se usa automáticamente
2. si hay varios configurados, se pregunta una sola vez
3. la selección persiste en `.pspo-agent/runtime/publish-provider.json`
4. `local` sigue existiendo como salida sin publicación remota

## Criterios de aceptación para GitHub MVP

- crea un Project v2 privado desde cero sin plantilla manual
- garantiza el campo `Status` con las opciones estándar y descripciones
- crea los campos Prioridad, Talla, Horas, Sprint y Responsable
- deja el proyecto autodocumentado con `shortDescription` y `readme`
- genera `HU-00 · Vision` como item separado
- publica cada HU como draft item con el markdown en bruto en el cuerpo y cada
  metadato en su campo
- resuelve la asignación por login de GitHub cuando el CSV lo aporta
- no miente cuando no puede resolver la asignación
- no rompe el flujo actual de Trello ni de Notion
