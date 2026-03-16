# Seguridad

## Principios

1. No leer `.env` en crudo desde el flujo normal.
2. No copiar secretos en prompts de `Agent` o `Task`.
3. No llamar a `api.trello.com` con `curl`, `wget`, `Fetch` ni scripts ad hoc.
4. Pasar por MCP o por fallback oficial controlado.
5. Guardar trabajo en local antes de publicar.

## Archivos clave

- hooks: [`../hooks/hooks.json`](../hooks/hooks.json)
- ejemplo de credenciales: [`../.env.example`](../.env.example)
- launcher MCP: [`../servers/trello-mcp-launcher.py`](../servers/trello-mcp-launcher.py)
- fallback oficial: [`../servers/trello-fallback.py`](../servers/trello-fallback.py)

## Controles activos

| Riesgo | Control |
|---|---|
| lectura directa de `.env` | [`../hooks/scripts/warn-sensitive-read.sh`](../hooks/scripts/warn-sensitive-read.sh) |
| uso directo de Trello por Bash/Fetch | [`../hooks/scripts/block-trello-bash.sh`](../hooks/scripts/block-trello-bash.sh) |
| uso de MCP sin `.env` válido | [`../hooks/scripts/check-env.sh`](../hooks/scripts/check-env.sh) |
| fuga de API key/token en prompts | [`../hooks/scripts/block-secret-prompt-leak.py`](../hooks/scripts/block-secret-prompt-leak.py) |
| re-preguntar credenciales válidas | [`../hooks/scripts/block-onboarding-credential-reask.py`](../hooks/scripts/block-onboarding-credential-reask.py) |
| `.env` fuera de `.gitignore` | [`../hooks/scripts/check-gitignore.sh`](../hooks/scripts/check-gitignore.sh) |

## Manejo de secretos

### Lo permitido

- usar `.pspo-agent/runtime/trello-fallback.sh env-status --pretty`
- dejar que `trello-mcp-launcher.py` cargue `.env`
- persistir `TRELLO_BOARD_ID` con el helper `save-board-id`

### Lo prohibido

- `Read(".env")`
- pegar `TRELLO_API_KEY=` o `TRELLO_TOKEN=` en prompts
- construir URLs con `?key=...&token=...`
- usar scripts Python improvisados para Trello

## Seguridad en publicación

La publicación solo cuenta como correcta si:

- existe tarjeta
- existe adjunto `.md`
- existe asignación real cuando la HU tiene owner

Eso evita el falso positivo de “éxito” cuando solo se escribió el nombre de la persona en la descripción.

## Seguridad para extensiones futuras

Si añades nuevas skills o hooks:

1. no reabras `.env` sin necesidad
2. no permitas nuevos atajos HTTP a Trello
3. mantén el carril oficial: MCP o fallback
4. añade tests de contenido y runtime si cambias guardrails

