# Configuración

## Instalación y distribución

Puntos de entrada de distribución:

- manifest Claude Code: [`../.claude-plugin/plugin.json`](../.claude-plugin/plugin.json)
- marketplace: [`../.claude-plugin/marketplace.json`](../.claude-plugin/marketplace.json)
- instalador Linux/macOS: [`../install.sh`](../install.sh)
- instalador Windows: [`../install.ps1`](../install.ps1)
- desinstalador Linux/macOS: [`../uninstall.sh`](../uninstall.sh)
- desinstalador Windows: [`../uninstall.ps1`](../uninstall.ps1)

El instalador:

1. verifica `python3`
2. verifica `claude`
3. registra el marketplace
4. instala el plugin

El desinstalador:

1. desregistra el plugin y el marketplace
2. limpia caché Python
3. opcionalmente borra `.env`
4. opcionalmente borra `docs/` y CSVs de equipo compatibles

## Configuración del plugin

Archivo principal:

- [`../settings.json`](../settings.json)

Secciones activas:

### `defaults.providers`

- `supported`: `trello`, `notion`, `github`, `local`
- `selection_file`: `.pspo-agent/runtime/publish-provider.json`
- `default`: `local`

### `defaults.trello`

- `token_expiration`: `30days`
- `app_name`: `PSPO Agent`
- `scopes`: `read,write`
- `default_lists`:
  - `Backlog`
  - `Sprint activo`
  - `Bloqueada`
  - `En progreso`
  - `En revision`
  - `Hecho`
- `default_labels`:
  - `Critica`
  - `Alta`
  - `Media`
  - `Baja`
- `publish_target_list`: `Backlog`
- `card_position`: `bottom`

### `defaults.notion`

- `api_version`: `2026-03-11`
- `project_title_prefix`: `PSPO`
- `project_page_title`: `{nombre_proyecto}`
- `vision_page_title`: `HU-00 · Vision`
- `database_title`: `Backlog`
- `required_env`:
  - `NOTION_TOKEN`
  - `NOTION_PARENT_PAGE_ID`
- `optional_env`:
  - `NOTION_DATABASE_ID`
  - `NOTION_PROJECT_PAGE_ID`
  - `NOTION_VISION_PAGE_ID`
- `status_options`:
  - `Backlog`
  - `Sprint activo`
  - `Bloqueada`
  - `En progreso`
  - `En revision`
  - `Hecho`

### `defaults.github`

- `project_title_prefix`: `PSPO`
- `project_visibility`: `private`
- `status_field_name`: `Status` (campo nativo del Project v2)
- `status_options`:
  - `Backlog`
  - `Sprint activo`
  - `Bloqueada`
  - `En progreso`
  - `En revision`
  - `Hecho`
- `required_env`:
  - `GITHUB_TOKEN` (o `gh` autenticado con scope `project`)
- `optional_env`:
  - `GH_TOKEN`
  - `GITHUB_PROJECT_NUMBER`
  - `GITHUB_PROJECT_ID`
  - `GITHUB_PROJECT_OWNER`
  - `GITHUB_PROJECT_URL`

### `defaults.discovery`

- `min_questions`: `3`
- `max_questions`: `8`
- `require_confirmation_before_generation`: `true`

### `defaults.stories`

- formato base: `Como [rol], quiero [accion], para [beneficio]`
- `require_given_when_then`: `true`
- `estimation_unit`: `horas_efectivas_con_agentes`
- `hours_per_day`: `8`
- `max_story_size_hours`: `16`
- `estimation_sizes`:
  - `XS = 1`
  - `S = 2`
  - `M = 4`
  - `L = 8`
  - `XL = 16`

### `defaults.validation`

- `require_explicit_approval`: `true`
- `allow_partial_approval`: `true`

### `defaults.docs`

- `output_dir`: `docs`
- `vision_file`: `vision.md`
- `stories_dir`: `historias`
- `backlog_file`: `backlog.md`
- `story_prefix`: `HU`
- `date_format`: `DD/MM/AAAA`

### `defaults.publish`

- `save_local_before_trello`: `true`
- `check_duplicates_by_title`: `true`
- `require_confirmation`: `true`
- `require_member_assignment_for_assigned_stories`: `true`

### `defaults.sprint`

- `duration_days`: `5`
- `max_duration_days`: `5`
- `focus_hours_per_day`: `6`
- `ai_agent_factor`: `0.65`
- `ai_agent_factor_recommended`: `0.70`
- `ai_agent_factor_range`: `0.30 - 0.80`

### `defaults.autopilot`

- `default_input_dir`: `.pspo-agent/inbox`
- ficheros de entrada aceptados:
  - `instrucciones.md`
  - `brief.md`
  - `prd.md`
  - `requirements.md`
  - `brief.txt`
- `require_final_gate`: `true`
- `stop_after_audit_if_trello_missing`: `true`
- `stop_after_audit_if_publish_provider_missing`: `true`

### `defaults.dod`

- `file`: `docs/dod.md`
- `add_checklist_to_trello`: `true`

## Variables de entorno

Referencia:

- [`../.env.example`](../.env.example)

Variables activas:

| Variable | Uso |
|---|---|
| `TRELLO_API_KEY` | API key del Power-Up de Trello |
| `TRELLO_TOKEN` | token de acceso del usuario |
| `TRELLO_TOKEN_CREATED` | fecha de creación del token |
| `TRELLO_BOARD_ID` | tablero de trabajo actual |
| `NOTION_TOKEN` | token de integración interna de Notion |
| `NOTION_PARENT_PAGE_ID` | página padre donde PSPO crea el proyecto desde cero |
| `NOTION_DATABASE_ID` | backlog de Notion ya existente, opcional |
| `NOTION_PROJECT_PAGE_ID` | página raíz del proyecto ya creada, opcional |
| `NOTION_VISION_PAGE_ID` | página HU-00 ya creada, opcional |
| `GITHUB_TOKEN` / `GH_TOKEN` | token con scope `project` como fallback sin `gh` |
| `GITHUB_PROJECT_NUMBER` | número del Project v2 del usuario |
| `GITHUB_PROJECT_ID` | node id del Project v2 |
| `GITHUB_PROJECT_OWNER` | login del propietario del Project v2 |
| `GITHUB_PROJECT_URL` | URL del Project v2 |

Notas:

- el onboarding debe poblar estas variables
- el launcher MCP carga `.env` automáticamente
- el hook de seguridad bloquea lectura cruda de `.env`
- la selección del proveedor no se guarda en `.env`; vive en `.pspo-agent/runtime/publish-provider.json`

## MCP

Archivo de registro MCP:

- [`../.mcp.json`](../.mcp.json)

Contrato actual:

```json
{
  "mcpServers": {
    "trello-client": {
      "command": "python3",
      "args": ["${CLAUDE_PLUGIN_ROOT}/servers/trello-mcp-launcher.py"]
    }
  }
}
```

## Qué vive en `docs/` y qué vive en `Documents/`

Toda la documentación del plugin (incluido el PRD) vive en `Documents/`, en una
sola carpeta.

`docs/` no contiene documentación: es la salida operativa que el plugin genera
en el proyecto del usuario (vision, backlog, historias, etc.) y está en
`.gitignore`, por lo que no se versiona ni se distribuye.

## Selección de proveedor de publicación

Helper runtime:

- [`../hooks/scripts/publish-provider.py`](../hooks/scripts/publish-provider.py)

Responsabilidades:

- detectar `trello`, `notion`, `github` o `local` según señales de proyecto (`.env` o targets persistidos)
- persistir una selección explícita en `.pspo-agent/runtime/publish-provider.json`
- exponer al runtime si hace falta preguntar una sola vez al usuario
- mantener una selección estable del proveedor activo para runtime y autopilot

## Equipo

Un CSV de equipo compatible es cualquier `.csv` con esta cabecera exacta:

```csv
nombre,email,rol,categoria,dedicacion,usa_agente_ia
```

La selección del CSV la implementan:

- [`../skills/team/SKILL.md`](../skills/team/SKILL.md)
- [`../hooks/scripts/autopilot-bootstrap.py`](../hooks/scripts/autopilot-bootstrap.py)
- [`../hooks/scripts/autopilot-guard.py`](../hooks/scripts/autopilot-guard.py)
