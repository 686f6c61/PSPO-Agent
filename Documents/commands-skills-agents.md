# Comandos, Skills y Agentes

## Comandos

Fuente:

- [`../commands/`](../commands/)

| Comando | Archivo | Skill invocada | Propósito |
|---|---|---|---|
| `/pspo-agent:start` | [`../commands/start.md`](../commands/start.md) | `start` | punto de entrada recomendado |
| `/pspo-agent:pspo` | [`../commands/pspo.md`](../commands/pspo.md) | `start` | alias de entrada |
| `/pspo-agent:autopilot` | [`../commands/autopilot.md`](../commands/autopilot.md) | `autopilot` | modo carpeta autónomo |
| `/pspo-agent:onboarding` | [`../commands/onboarding.md`](../commands/onboarding.md) | `onboarding` | credenciales y destino de publicación |
| `/pspo-agent:discovery` | [`../commands/discovery.md`](../commands/discovery.md) | `discovery` | descubrimiento desde cero |
| `/pspo-agent:analyze` | [`../commands/analyze.md`](../commands/analyze.md) | `analyze` | análisis desde documento |
| `/pspo-agent:generate-stories` | [`../commands/generate-stories.md`](../commands/generate-stories.md) | `generate-stories` | generación de HUs |
| `/pspo-agent:validate` | [`../commands/validate.md`](../commands/validate.md) | `validate` | validación |
| `/pspo-agent:publish` | [`../commands/publish.md`](../commands/publish.md) | `publish` | publicación en el proveedor activo |
| `/pspo-agent:save-docs` | [`../commands/save-docs.md`](../commands/save-docs.md) | `save-docs` | persistencia local |
| `/pspo-agent:team` | [`../commands/team.md`](../commands/team.md) | `team` | gestión de equipo |
| `/pspo-agent:assign` | [`../commands/assign.md`](../commands/assign.md) | `assign` | ownership por HU |
| `/pspo-agent:dependencies` | [`../commands/dependencies.md`](../commands/dependencies.md) | `dependencies` | mapa de dependencias |
| `/pspo-agent:sprint-plan` | [`../commands/sprint-plan.md`](../commands/sprint-plan.md) | `sprint-plan` | planificación |
| `/pspo-agent:sprint-review` | [`../commands/sprint-review.md`](../commands/sprint-review.md) | `sprint-review` | cierre de sprint |
| `/pspo-agent:export` | [`../commands/export.md`](../commands/export.md) | `export` | exportación |
| `/pspo-agent:update` | [`../commands/update.md`](../commands/update.md) | `update` | actualización |
| `/pspo-agent:audit` | [`../commands/audit.md`](../commands/audit.md) | `audit` | auditoría senior |
| `/pspo-agent:help` | [`../commands/help.md`](../commands/help.md) | ayuda estática | catálogo de comandos |

## Skills

Fuente:

- [`../skills/`](../skills/)

| Skill | Archivo | Herramientas | Rol en el flujo |
|---|---|---|---|
| `start` | [`../skills/start/SKILL.md`](../skills/start/SKILL.md) | `Read, Grep, Glob, Write, Edit, Bash, Task, AskUserQuestion` | router de entrada, proveedor y estado de publicación |
| `autopilot` | [`../skills/autopilot/SKILL.md`](../skills/autopilot/SKILL.md) | `Read, Glob, Write, AskUserQuestion` | orquestación autónoma |
| `product-phase` | [`../skills/product-phase/SKILL.md`](../skills/product-phase/SKILL.md) | sin delegación a agentes | fase no interactiva de producto |
| `onboarding` | [`../skills/onboarding/SKILL.md`](../skills/onboarding/SKILL.md) | incluye `Bash` controlado | router de proveedor, credenciales y destino remoto |
| `discovery` | [`../skills/discovery/SKILL.md`](../skills/discovery/SKILL.md) | `Task, AskUserQuestion` | descubrimiento guiado |
| `analyze` | [`../skills/analyze/SKILL.md`](../skills/analyze/SKILL.md) | `Task, AskUserQuestion` | análisis desde documento |
| `generate-stories` | [`../skills/generate-stories/SKILL.md`](../skills/generate-stories/SKILL.md) | `Task, AskUserQuestion` | historias desde contexto |
| `audit` | [`../skills/audit/SKILL.md`](../skills/audit/SKILL.md) | `Task, AskUserQuestion` | auditoría de fondo |
| `validate` | [`../skills/validate/SKILL.md`](../skills/validate/SKILL.md) | `Task, AskUserQuestion` | aprobación de HUs |
| `save-docs` | [`../skills/save-docs/SKILL.md`](../skills/save-docs/SKILL.md) | `Read, Grep, Glob, Write, Edit` | persistencia local |
| `team` | [`../skills/team/SKILL.md`](../skills/team/SKILL.md) | `Task, AskUserQuestion` | equipo y CSV compatible |
| `assign` | [`../skills/assign/SKILL.md`](../skills/assign/SKILL.md) | `Task, AskUserQuestion` | reparto de ownership |
| `dependencies` | [`../skills/dependencies/SKILL.md`](../skills/dependencies/SKILL.md) | `Task, AskUserQuestion` | dependencias y bloqueos |
| `sprint-plan` | [`../skills/sprint-plan/SKILL.md`](../skills/sprint-plan/SKILL.md) | `Task, AskUserQuestion` | DoD, capacidad y sprint |
| `publish` | [`../skills/publish/SKILL.md`](../skills/publish/SKILL.md) | `Bash, Task, AskUserQuestion` | publicación remota y sincronización por proveedor |
| `sprint-review` | [`../skills/sprint-review/SKILL.md`](../skills/sprint-review/SKILL.md) | `Task, AskUserQuestion` | revisión de sprint |
| `export` | [`../skills/export/SKILL.md`](../skills/export/SKILL.md) | `Read, Grep, Glob, Write, AskUserQuestion` | exportación |
| `update` | [`../skills/update/SKILL.md`](../skills/update/SKILL.md) | `Read, Grep, Glob, Bash, AskUserQuestion` | comprobar actualizaciones |

## Agentes

Fuente:

- [`../agents/`](../agents/)

| Agente | Archivo | Color | Función |
|---|---|---|---|
| `product-owner` | [`../agents/product-owner.md`](../agents/product-owner.md) | `blue` | discovery y generación de historias |
| `requirement-analyst` | [`../agents/requirement-analyst.md`](../agents/requirement-analyst.md) | `cyan` | análisis de requisitos |
| `publisher` | [`../agents/publisher.md`](../agents/publisher.md) | `green` | Trello; las rutas Notion y GitHub Projects se ejecutan por fallback oficial desde `publish` |
| `sprint-planner` | [`../agents/sprint-planner.md`](../agents/sprint-planner.md) | `amber` | capacidad y sprint |
| `culture-guardian` | [`../agents/culture-guardian.md`](../agents/culture-guardian.md) | `magenta` | estilo y calidad del texto |
| `senior-auditor` | [`../agents/senior-auditor.md`](../agents/senior-auditor.md) | ver archivo | auditoría de backlog/HUs |

## Relaciones importantes

### Skills que delegan

- `analyze` -> `requirement-analyst`
- `discovery` -> `product-owner`
- `generate-stories` -> `product-owner`
- `audit` -> `senior-auditor`
- `team` -> `sprint-planner`
- `sprint-plan` -> `sprint-planner`
- `publish` -> `publisher` o fallback oficial

### Skills que no deben delegar

- `autopilot`
- `product-phase`
- `save-docs`

## Reglas de negocio destacadas

- el CSV de equipo no depende de llamarse `team.csv`
- `publish` exige resumen + `.md` + asignación real
- `HU-00` o visión es un artefacto de primer nivel
- `Sprint actual` es legacy; el estado correcto es `Sprint activo`
- la selección del proveedor remoto se persiste en `.pspo-agent/runtime/publish-provider.json`
