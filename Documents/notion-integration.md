# Integración Notion

## Objetivo

Documentar la integracion actual de PSPO Agent con Notion para publicar sin
plantillas previas, manteniendo el mismo contrato de negocio que Trello.

Estado actual:

- `product-phase` sigue generando artefactos locales en `docs/`
- `onboarding` y `publish` se convierten en routers por proveedor
- Notion crea la estructura desde cero por API

## Ficheros implicados

- selector de proveedor:
  [`../hooks/scripts/publish-provider.py`](../hooks/scripts/publish-provider.py)
- fallback oficial inicial:
  [`../servers/notion-fallback.py`](../servers/notion-fallback.py)
- estado autónomo:
  [`../hooks/scripts/autopilot-guard.py`](../hooks/scripts/autopilot-guard.py)
- configuración global:
  [`../settings.json`](../settings.json)
- ejemplo de credenciales:
  [`../.env.example`](../.env.example)
- skill de onboarding actual:
  [`../skills/onboarding/SKILL.md`](../skills/onboarding/SKILL.md)
- skill de publicación actual:
  [`../skills/publish/SKILL.md`](../skills/publish/SKILL.md)

## Contrato `.env`

Variables mínimas para Notion:

- `NOTION_TOKEN`
- `NOTION_PARENT_PAGE_ID`

Variables opcionales:

- `NOTION_DATABASE_ID`
- `NOTION_PROJECT_PAGE_ID`
- `NOTION_VISION_PAGE_ID`

Interpretación:

- con `NOTION_TOKEN` + `NOTION_PARENT_PAGE_ID`, el plugin puede crear el
  proyecto desde cero
- con `NOTION_DATABASE_ID`, el plugin puede reutilizar un backlog ya existente
- con `NOTION_PROJECT_PAGE_ID`, el plugin puede reanclar publicaciones
  posteriores a una página raíz ya creada
- con `NOTION_VISION_PAGE_ID`, el plugin puede resincronizar `HU-00` sin crear otra página

## Estructura zero-template

La API de Notion sí permite crear la estructura base desde cero:

1. página raíz del proyecto: `PSPO · {nombre_proyecto}`
2. página `HU-00 · Vision`
3. database/data source `Backlog`
4. páginas de historia dentro del backlog

## Modelo mínimo del backlog

Propiedades propuestas:

| Propiedad | Tipo | Uso |
|---|---|---|
| `ID` | `rich_text` | `HU-01`, `HU-02`, etc. |
| `Titulo` | `title` | nombre corto de la historia |
| `Resumen` | `rich_text` | resumen ejecutivo corto |
| `Estado` | `select` | backlog, sprint, bloqueada, etc. |
| `Prioridad` | `select` | crítica, alta, media, baja |
| `Estimacion_h` | `number` | horas efectivas con agentes |
| `Sprint` | `rich_text` | sprint actual o futuro |
| `Asignado_a` | `people` | usuario resuelto del workspace |
| `Bloqueada_por` | `relation` | dependencias entrantes |
| `Bloquea` | `relation` | dependencias salientes |

## Contrato de publicación en Notion

Cada HU publicada debe conservar el mismo contrato de negocio que Trello:

1. resumen corto
2. contenido completo en largo
3. persona asignada si puede resolverse
4. dependencia visible
5. `.md` real adjunto o referenciado

Aplicación práctica:

- `Resumen` va en propiedad corta de la página
- el cuerpo largo se envía en bloques Markdown
- el `.md` se sube como archivo
- `Asignado_a` usa `people`
- dependencias usan `relation`
- si la HU ya existe, la sync incremental debe actualizar propiedades y adjuntos sin duplicar página

## Herramientas runtime de Notion

El fallback oficial de [`../servers/notion-fallback.py`](../servers/notion-fallback.py)
expone ya estas operaciones clave para el carril productivo:

- `sync-vision-from-markdown`
- `parse-story-markdown`
- `find-story-page`
- `create-story-page`
- `update-story-page`
- `sync-story-from-markdown`
- `ensure-dependency-relations`
- `set-story-dependencies`
- `sync-story-dependencies-from-markdown`
- `sync-stories-from-folder`
- `upload-and-attach-markdown`

Secuencia recomendada de publicación:

1. asegurar `env-status`, credenciales y targets
2. resincronizar `HU-00` con `sync-vision-from-markdown`
3. asegurar esquema dual `Bloqueada_por` / `Bloquea`
4. primera pasada:
   - parsear `docs/historias/HU-*.md`
   - sincronizar página, propiedades, cuerpo largo y `.md` adjunto con `sync-story-from-markdown`
5. segunda pasada:
   - resolver dependencias `HU-XX`
   - sincronizar relaciones reales con `sync-story-dependencies-from-markdown`

Atajo operativo:

- `sync-stories-from-folder` ejecuta `HU-00` opcional + primera pasada + segunda pasada sobre `docs/historias/`
- si una HU ya tiene el mismo `.md` adjunto, el sync debe reutilizarlo y reportarlo en `attachmentSkips`
- si el email no se resuelve contra `people`, el lote debe devolverlo en `unresolvedAssignments`
- el lote debe dejar `docs/publish-report.md` con el resumen local de visión, historias, errores y revisiones manuales

## Límites reales de la API

Sí soporta:

- crear páginas
- crear la database inicial
- subir archivos
- escribir contenido largo
- asignar usuarios existentes
- relacionar páginas

No hay equivalencia limpia con Trello para:

- invitar miembros por email al proyecto desde la Public API
- construir vistas de board completamente curadas por REST

Conclusión:

- el modelo de datos sí puede ser zero-template
- la capa visual del board en Notion será funcional antes que perfecta

## Regla de selección de proveedor

El runtime sigue estas reglas:

1. si solo hay un proveedor configurado, se usa automáticamente
2. si hay Trello y Notion configurados, se pregunta una sola vez
3. la selección persiste en `.pspo-agent/runtime/publish-provider.json`
4. `local` sigue existiendo como salida sin publicación remota

## Estrategia segura de evolución

Orden recomendado:

1. mantener `publish-provider.py` como única fuente de verdad del proveedor activo
2. conservar `onboarding` y `publish` como routers por proveedor
3. ampliar `servers/notion-fallback.py` sin rebajar el contrato de publicación
4. cubrir cada cambio con smoke tests:
   - solo Trello
   - solo Notion
   - Trello + Notion

## Criterios de aceptación para Notion MVP

- crea proyecto desde cero sin plantilla manual
- genera `HU-00` separada
- publica cada HU con contenido largo
- adjunta el `.md`
- intenta asignar por usuario existente del workspace
- no miente cuando no puede resolver la asignación
- no rompe el flujo actual de Trello
