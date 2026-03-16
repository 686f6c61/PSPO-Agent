#!/usr/bin/env bash
# Hook PreToolUse (matcher: Bash, Fetch): Bloquea comandos que intenten
# acceder a la API de Trello directamente y cualquier Bash/Fetch durante las
# fases tempranas de /pspo-agent:autopilot.
# Las operaciones con Trello DEBEN ir por el servidor MCP trello-client y
# la preparacion local del autopilot debe usar Glob/Read/Write/Edit.
#
# Codigos de salida:
#   0 = comando permitido
#   2 = comando bloqueado (intenta acceder a Trello directamente)

set -euo pipefail

emit_block() {
    local message="$1"
    echo "BLOCKED" >&2
    echo "$message" >&2
    echo "$message"
}

# Leer el input del hook (JSON con tool_input)
INPUT=$(cat)
TOOL_NAME=""
CWD="$(pwd)"
PAYLOAD=""

eval "$(printf '%s' "$INPUT" | python3 -c "
import json, os, shlex, sys
try:
    data = json.load(sys.stdin)
except Exception:
    data = {}
tool_input = data.get('tool_input', {}) or {}
tool_name = data.get('tool_name', '')
cwd = data.get('cwd') or os.getcwd()
print(f'TOOL_NAME={shlex.quote(tool_name)}')
print(f'CWD={shlex.quote(cwd)}')
print(f'PAYLOAD={shlex.quote(json.dumps(tool_input, ensure_ascii=False))}')
" 2>/dev/null || true)"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
phase="$(python3 "${SCRIPT_DIR}/autopilot-guard.py" --ensure-scaffold --field phase "${CWD}")"
gate_status="$(python3 "${SCRIPT_DIR}/autopilot-guard.py" --field gate_status "${CWD}")"
branch_skill="$(python3 "${SCRIPT_DIR}/autopilot-guard.py" --field branch_skill "${CWD}")"
active_skill="$(python3 "${SCRIPT_DIR}/autopilot-guard.py" --field active_skill "${CWD}")"
start_bootstrap="$(python3 "${SCRIPT_DIR}/autopilot-guard.py" --field start_bootstrap "${CWD}")"
onboarding_bootstrap="$(python3 "${SCRIPT_DIR}/autopilot-guard.py" --field onboarding_bootstrap "${CWD}")"
start_bootstrap_file="$(python3 "${SCRIPT_DIR}/autopilot-guard.py" --field start_bootstrap_file "${CWD}")"
onboarding_bootstrap_file="$(python3 "${SCRIPT_DIR}/autopilot-guard.py" --field onboarding_bootstrap_file "${CWD}")"
PAYLOAD_LOWER=$(printf '%s' "$PAYLOAD" | tr '[:upper:]' '[:lower:]')
uses_official_fallback="false"
uses_env_status="false"

if [[ "${TOOL_NAME}" == "Bash" ]] && echo "$PAYLOAD_LOWER" | grep -qiE 'trello-fallback(\.py|\.sh)'; then
    uses_official_fallback="true"
fi

if [[ "${uses_official_fallback}" == "true" ]] && echo "$PAYLOAD_LOWER" | grep -qiE 'env-status'; then
    uses_env_status="true"
fi

case "${phase}" in
    prepare-context)
        emit_block "En /pspo-agent:autopilot no uses ${TOOL_NAME} durante el bootstrap ni la fase de producto. El sistema ya prepara el scaffold operativo; usa Glob/Read y encadena Skill(\"pspo-agent:product-phase\")."
        exit 2
        ;;
    delegate-product-phase|product-phase-active)
        if [[ "${active_skill}" == "pspo-agent:product-phase" ]]; then
            emit_block "Durante product-phase no uses ${TOOL_NAME}, tampoco para mkdir o crear carpetas. Materializa docs/ y docs/historias/ escribiendo los ficheros finales con Write/Edit."
            exit 2
        fi
        emit_block "En /pspo-agent:autopilot no uses ${TOOL_NAME} durante el bootstrap ni la fase de producto. El sistema ya prepara el scaffold operativo; usa Glob/Read y encadena Skill(\"pspo-agent:product-phase\")."
        exit 2
        ;;
esac

if [[ "${active_skill}" == "pspo-agent:start" ]] && [[ "${start_bootstrap}" != "done" ]] && [[ "${uses_official_fallback}" != "true" ]]; then
    emit_block "En /pspo-agent:start no uses Bash ni Fetch todavia. La primera accion valida es .pspo-agent/runtime/trello-fallback.sh env-status --pretty."
    exit 2
fi

if [[ "${active_skill}" == "pspo-agent:onboarding" ]] && [[ "${onboarding_bootstrap}" != "done" ]] && [[ "${uses_official_fallback}" != "true" ]]; then
    emit_block "En /pspo-agent:onboarding no uses Bash ni Fetch todavia. La primera accion valida es .pspo-agent/runtime/trello-fallback.sh env-status --pretty."
    exit 2
fi

if [[ "${uses_official_fallback}" == "true" ]] && echo "$PAYLOAD_LOWER" | grep -qiE '(\|\||&&|curl|wget|grep .*trello_|grep .*token|\.claude/|cat .*\.env|sed )'; then
    emit_block "Usa el wrapper oficial en un comando limpio y aislado. No mezcles .pspo-agent/runtime/trello-fallback.sh con curl, grep, .claude ni lecturas manuales de .env."
    exit 2
fi

if [[ "${uses_official_fallback}" == "true" ]]; then
    if [[ "${phase}" == "product-ready" && "${gate_status}" == "plan-publish" && "${branch_skill}" == "pspo-agent:onboarding" ]] \
        && echo "$PAYLOAD_LOWER" | grep -qiE 'list-boards'; then
        emit_block "En onboarding desde autopilot no ejecutes list-boards. Usa directamente .pspo-agent/runtime/trello-fallback.sh create-board y continua con manage-lists, manage-labels y guardado de TRELLO_BOARD_ID."
        exit 2
    fi
    if [[ "${uses_env_status}" == "true" ]]; then
        case "${active_skill}" in
            pspo-agent:start)
                mkdir -p "$(dirname "${start_bootstrap_file}")"
                printf 'done\n' > "${start_bootstrap_file}"
                ;;
            pspo-agent:onboarding)
                mkdir -p "$(dirname "${onboarding_bootstrap_file}")"
                printf 'done\n' > "${onboarding_bootstrap_file}"
                ;;
        esac
    fi
    exit 0
fi

if [[ "${phase}" == "product-ready" && "${gate_status}" == "plan-publish" && "${branch_skill}" == "pspo-agent:onboarding" ]]; then
    emit_block "Durante onboarding desde autopilot no uses ${TOOL_NAME}. Usa Read/Glob para .env, .gitignore, .env.example, runtime/inbox y delega en el agente publisher para verify-credentials, list-boards o create-board."
    exit 2
fi

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

# Patrones prohibidos en autopilot local: la inbox y sus copias se manejan
# con herramientas de fichero, no con Bash.
AUTOPILOT_LOCAL_PATTERNS=(
    "\\.pspo-agent/inbox"
    "cp .*\\.pspo-agent/inbox/.*\\.csv"
    "cp .*\\.pspo-agent/inbox/.*\\.md"
)

for pattern in "${BLOCKED_PATTERNS[@]}"; do
    pattern_lower=$(echo "$pattern" | tr '[:upper:]' '[:lower:]')
    if echo "$PAYLOAD_LOWER" | grep -qiE "$pattern_lower"; then
        emit_block "Acceso directo a la API de Trello bloqueado. Usa las herramientas MCP del servidor trello-client o el wrapper oficial .pspo-agent/runtime/trello-fallback.sh; nunca Bash, Fetch o curl manual."
        echo "Herramientas disponibles: verify-credentials, list-boards, get-board, get-card," >&2
        echo "create-board, manage-lists, manage-labels, create-cards, search-cards," >&2
        echo "update-card, add-checklist, attach-file, get-board-members, invite-member." >&2
        exit 2
    fi
done

for pattern in "${AUTOPILOT_LOCAL_PATTERNS[@]}"; do
    if echo "$PAYLOAD" | grep -qiE "$pattern"; then
        emit_block "En /pspo-agent:autopilot no uses Bash para inspeccionar o copiar la inbox. Usa Glob para listar '.pspo-agent/inbox/*' y deja que el bootstrap importe el CSV compatible por codigo."
        exit 2
    fi
done

exit 0
