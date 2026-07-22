# Hooks y Runtime

## Registro de hooks

Archivo:

- [`../hooks/hooks.json`](../hooks/hooks.json)

Eventos usados:

- `Stop`
- `PreToolUse`
- `PostToolUse`

## Tabla completa de hooks

| Evento | Matcher | Script | Función |
|---|---|---|---|
| `Stop` | n/a | [`../hooks/scripts/autopilot-stop.py`](../hooks/scripts/autopilot-stop.py) | impide cortar `autopilot` antes de tiempo |
| `PreToolUse` | `mcp__(plugin_pspo-agent_)?trello-client__.*` | [`../hooks/scripts/block-autopilot-trello.sh`](../hooks/scripts/block-autopilot-trello.sh) | Trello no entra antes de fase de producto |
| `PreToolUse` | `mcp__(plugin_pspo-agent_)?trello-client__.*` | [`../hooks/scripts/check-env.sh`](../hooks/scripts/check-env.sh) | exige `.env` válido |
| `PreToolUse` | `Bash` | [`../hooks/scripts/block-trello-bash.sh`](../hooks/scripts/block-trello-bash.sh) | bloquea Bash/WebFetch no permitidos |
| `PreToolUse` | `WebFetch` | [`../hooks/scripts/block-trello-bash.sh`](../hooks/scripts/block-trello-bash.sh) | idem para `WebFetch` |
| `PreToolUse` | `Agent` | [`../hooks/scripts/block-secret-prompt-leak.py`](../hooks/scripts/block-secret-prompt-leak.py) | evita fugas de secretos en prompts |
| `PreToolUse` | `Agent` | [`../hooks/scripts/block-autopilot-agent.sh`](../hooks/scripts/block-autopilot-agent.sh) | bloquea delegaciones fuera del carril |
| `PreToolUse` | `Task` | [`../hooks/scripts/block-secret-prompt-leak.py`](../hooks/scripts/block-secret-prompt-leak.py) | idem |
| `PreToolUse` | `Task` | [`../hooks/scripts/block-autopilot-agent.sh`](../hooks/scripts/block-autopilot-agent.sh) | idem |
| `PreToolUse` | `Read` | [`../hooks/scripts/block-autopilot-drift.sh`](../hooks/scripts/block-autopilot-drift.sh) | evita exploración lateral |
| `PreToolUse` | `Read` | [`../hooks/scripts/warn-sensitive-read.sh`](../hooks/scripts/warn-sensitive-read.sh) | bloquea `.env` y avisa de lecturas sensibles |
| `PreToolUse` | `Glob` | [`../hooks/scripts/block-autopilot-drift.sh`](../hooks/scripts/block-autopilot-drift.sh) | evita globs amplios |
| `PreToolUse` | `ToolSearch` | [`../hooks/scripts/block-autopilot-drift.sh`](../hooks/scripts/block-autopilot-drift.sh) | evita deriva |
| `PreToolUse` | `TodoWrite` | [`../hooks/scripts/block-autopilot-drift.sh`](../hooks/scripts/block-autopilot-drift.sh) | evita deriva |
| `PreToolUse` | `Skill` | [`../hooks/scripts/persist-active-skill.py`](../hooks/scripts/persist-active-skill.py) | persiste skill activa y wrapper fallback |
| `PreToolUse` | `Skill` | [`../hooks/scripts/block-autopilot-skill.sh`](../hooks/scripts/block-autopilot-skill.sh) | fuerza el orden de skills |
| `PreToolUse` | `AskUserQuestion` | [`../hooks/scripts/block-onboarding-credential-reask.py`](../hooks/scripts/block-onboarding-credential-reask.py) | evita volver a pedir credenciales |
| `PostToolUse` | `AskUserQuestion` | [`../hooks/scripts/persist-autopilot-gate.py`](../hooks/scripts/persist-autopilot-gate.py) | guarda la rama elegida en la gate |
| `PostToolUse` | `Write` | [`../hooks/scripts/check-gitignore.sh`](../hooks/scripts/check-gitignore.sh) | avisa si `.env` no está en `.gitignore` |

## Scripts de runtime

### `autopilot-bootstrap.py`

Archivo:

- [`../hooks/scripts/autopilot-bootstrap.py`](../hooks/scripts/autopilot-bootstrap.py)

Hace:

- localiza el documento principal en `.pspo-agent/inbox`
- localiza `vision.md` si existe
- detecta cualquier CSV de equipo compatible
- decide `modo_producto` (`analyze` o `discovery`)
- genera `.pspo-agent/runtime/autopilot-context.md`
- importa el CSV compatible a raíz si hace falta

### `autopilot-guard.py`

Archivo:

- [`../hooks/scripts/autopilot-guard.py`](../hooks/scripts/autopilot-guard.py)

Es la máquina de estado del modo autónomo.

Estados principales:

- `inactive`
- `prepare-context`
- `delegate-product-phase`
- `product-phase-active`
- `product-ready`

También resuelve:

- si Trello está listo
- si Notion ya tiene token y destino base
- si hace falta preguntar por el proveedor de publicación
- si existe CSV compatible
- si hay asignaciones, dependencias y sprint
- cuál es la siguiente skill válida

### `publish-provider.py`

Archivo:

- [`../hooks/scripts/publish-provider.py`](../hooks/scripts/publish-provider.py)

Responsabilidades:

- detectar proveedores configurados en `.env`
- distinguir entre proveedor "con credenciales" y proveedor "listo para publicar"
- persistir `.pspo-agent/runtime/publish-provider.json`
- exponer al runtime si la elección puede ser automática o necesita una sola pregunta

### `persist-active-skill.py`

- guarda `active-skill.status`
- crea `.pspo-agent/runtime/trello-fallback.sh`
- crea `.pspo-agent/runtime/notion-fallback.sh`
- limpia marcas de bootstrap cuando cambia la skill

### `persist-autopilot-gate.py`

- detecta la pregunta final de autopilot
- persiste `review` o `plan-publish`

### `autopilot-stop.py`

- bloquea `Stop` hasta que el flujo esté en un punto válido de salida

## Ficheros runtime que miran los hooks

| Fichero | Leído por |
|---|---|
| `autopilot-context.md` | `autopilot-guard.py`, `block-autopilot-drift.sh`, `autopilot-stop.py` |
| `product-phase.status` | `autopilot-guard.py`, `block-autopilot-agent.sh`, `autopilot-stop.py` |
| `final-gate.status` | `autopilot-guard.py`, `persist-autopilot-gate.py`, `block-autopilot-skill.sh` |
| `autopilot-branch-skill.status` | `autopilot-guard.py`, `block-autopilot-skill.sh` |
| `active-skill.status` | `autopilot-guard.py`, `block-trello-bash.sh` |
| `publish-provider.json` | `publish-provider.py`, `autopilot-guard.py` |

## Qué protege el sistema

- que `autopilot` no vuelva a abrir la inbox cuando ya hay runtime
- que `product-phase` no derive a `Agent/Task`
- que Trello no se toque fuera del momento correcto
- que `.env` no se lea en crudo
- que no se peguen claves en prompts
- que onboarding no vuelva a pedir API key/token si ya son válidos
