#!/usr/bin/env bash
# Hook PreToolUse (matcher: Bash): Bloquea comandos bash que intenten
# acceder a la API de Trello directamente (curl, wget, python requests).
# Las operaciones con Trello DEBEN ir por el servidor MCP trello-client.
#
# Codigos de salida:
#   0 = comando permitido
#   2 = comando bloqueado (intenta acceder a Trello directamente)

set -euo pipefail

# Leer el input del hook (JSON con tool_input)
INPUT=$(cat)

# Extraer el comando del JSON
COMMAND=$(echo "$INPUT" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    cmd = data.get('tool_input', {}).get('command', '')
    print(cmd)
except Exception:
    print('')
" 2>/dev/null || true)

# Patrones prohibidos: cualquier acceso directo a Trello
BLOCKED_PATTERNS=(
    "api.trello.com"
    "trello.com/1/"
    "TRELLO_API_KEY"
    "TRELLO_TOKEN"
    "curl.*trello"
    "wget.*trello"
    "urllib.*trello"
    "requests.*trello"
)

COMMAND_LOWER=$(echo "$COMMAND" | tr '[:upper:]' '[:lower:]')

for pattern in "${BLOCKED_PATTERNS[@]}"; do
    pattern_lower=$(echo "$pattern" | tr '[:upper:]' '[:lower:]')
    if echo "$COMMAND_LOWER" | grep -qiE "$pattern_lower"; then
        echo "BLOCKED"
        echo "Acceso directo a la API de Trello bloqueado."
        echo "Usa las herramientas MCP del servidor trello-client en vez de bash/curl."
        echo "Herramientas disponibles: verify-credentials, list-boards, get-board,"
        echo "create-board, manage-lists, manage-labels, create-cards, search-cards,"
        echo "add-checklist, attach-file, get-board-members, invite-member."
        exit 2
    fi
done

exit 0
