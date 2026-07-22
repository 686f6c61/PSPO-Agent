#!/usr/bin/env bash
# Hook PreToolUse: Verifica que .env existe y tiene las credenciales de Trello
# antes de permitir cualquier llamada al servidor MCP trello-client.
#
# Si falta .env o las credenciales, bloquea la operacion con un mensaje claro.
# Codigos de salida:
#   0 = credenciales presentes, continuar
#   2 = credenciales ausentes, bloquear la operacion

set -euo pipefail

# Resolver interprete de Python sin depender de que 'python3' exista en PATH
# (en Windows suele ser 'python'). Este hook es el gate de credenciales del MCP
# de Trello y solo afecta a llamadas MCP de Trello: fail-closed si no hay
# interprete, para no permitir operaciones sin validar credenciales.
PY="$(command -v python3 || command -v python || true)"
if [ -z "${PY}" ]; then
    echo "BLOCKED" >&2
    echo "No se encontro python3 ni python para validar las credenciales de Trello." >&2
    echo "Instala Python 3 (o asegurate de que 'python' esta en el PATH) y reintenta." >&2
    exit 2
fi

# Intentar resolver la raiz real del proyecto para no depender del cwd.
INPUT=$(cat)
PROJECT_DIR=$(echo "$INPUT" | "$PY" -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(
        data.get('cwd')
        or data.get('tool_input', {}).get('cwd')
        or ''
    )
except Exception:
    print('')
" 2>/dev/null || true)

if [ -n "${PROJECT_DIR}" ] && [ -d "${PROJECT_DIR}" ]; then
    ROOT_DIR="${PROJECT_DIR}"
else
    ROOT_DIR=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
fi

ENV_FILE="${ROOT_DIR}/.env"

# Verificar que el fichero .env existe
if [ ! -f "$ENV_FILE" ]; then
    echo "BLOCKED"
    echo "No se encuentra el fichero .env con las credenciales de Trello."
    echo "Ejecuta /pspo-agent:onboarding para configurar las credenciales."
    exit 2
fi

# Verificar que TRELLO_API_KEY tiene valor
TRELLO_API_KEY=$(grep -E "^TRELLO_API_KEY=" "$ENV_FILE" 2>/dev/null | cut -d'=' -f2- | tr -d '[:space:]' || true)
if [ -z "$TRELLO_API_KEY" ]; then
    echo "BLOCKED"
    echo "Falta TRELLO_API_KEY en el fichero .env."
    echo "Ejecuta /pspo-agent:onboarding para configurar las credenciales."
    exit 2
fi

# Verificar que TRELLO_TOKEN tiene valor
TRELLO_TOKEN=$(grep -E "^TRELLO_TOKEN=" "$ENV_FILE" 2>/dev/null | cut -d'=' -f2- | tr -d '[:space:]' || true)
if [ -z "$TRELLO_TOKEN" ]; then
    echo "BLOCKED"
    echo "Falta TRELLO_TOKEN en el fichero .env."
    echo "Ejecuta /pspo-agent:onboarding para configurar las credenciales."
    exit 2
fi

# Todo correcto, permitir la operacion
exit 0
