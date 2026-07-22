#!/usr/bin/env bash
# Hook PreToolUse (matcher: Agent, Task): bloquea delegaciones ad hoc
# lanzadas desde /pspo-agent:autopilot. product-phase ya no delega:
# redacta y persiste todo localmente. Solo onboarding/publisher puede
# seguir usando Agent/Task en la rama plan-publish.

set -euo pipefail

emit_block() {
    local message="$1"
    echo "BLOCKED" >&2
    echo "$message" >&2
    echo "$message"
}

# Resolver interprete de Python sin depender de 'python3' (en Windows suele ser
# 'python'). Sin interprete no se puede computar el estado: fail-open avisado,
# porque bloquear Agent/Task de forma global romperia la sesion.
PY="$(command -v python3 || command -v python || true)"
if [ -z "${PY}" ]; then
    echo "[pspo-agent] Aviso: no se encontro python3 ni python; se omite el guardarrail de delegaciones (fail-open)." >&2
    exit 0
fi

INPUT=$(cat)

eval "$(printf '%s' "$INPUT" | "$PY" -c "
import json, os, shlex, sys
try:
    data = json.load(sys.stdin)
except Exception:
    data = {}
cwd = data.get('cwd') or os.getcwd()
tool_name = data.get('tool_name', '')
tool_input = data.get('tool_input', {}) or {}
print(f'CWD={shlex.quote(cwd)}')
print(f'TOOL_NAME={shlex.quote(tool_name)}')
print(f'PAYLOAD={shlex.quote(json.dumps(tool_input, ensure_ascii=False))}')
")"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Un unico volcado del estado del guard en vez de reinvocarlo campo a campo.
eval "$("$PY" "${SCRIPT_DIR}/autopilot-guard.py" --ensure-scaffold --dump-shell "${CWD}")"
provider_needs_choice="${publish_provider_needs_choice}"
payload_lower="$(printf '%s' "${PAYLOAD}" | tr '[:upper:]' '[:lower:]')"

case "${phase}" in
    inactive)
        if [[ "${active_skill}" == "pspo-agent:onboarding" ]]; then
            if [[ "${provider_needs_choice}" == "1" || -z "${publish_provider}" ]]; then
                emit_block "En /pspo-agent:onboarding no uses ${TOOL_NAME} para descubrir estado. La ruta valida empieza por trello-fallback/notion-fallback/github-fallback env-status y .pspo-agent/runtime/publish-provider.py."
                exit 2
            fi
            if [[ "${publish_provider}" == "notion" || "${publish_provider}" == "github" || "${publish_provider}" == "local" ]]; then
                emit_block "En /pspo-agent:onboarding con proveedor ${publish_provider} no uses ${TOOL_NAME}. La ruta valida es Bash con notion-fallback.sh o github-fallback.sh o .pspo-agent/runtime/publish-provider.py; no delegues a agentes genericos."
                exit 2
            fi
            if [[ "${payload_lower}" == *"publisher"* ]]; then
                exit 0
            fi
            emit_block "En /pspo-agent:onboarding con proveedor Trello no uses ${TOOL_NAME} genericos ni exploradores. La unica delegacion valida es `Task` con `publisher` para verify-credentials, create-board y configuracion del tablero."
            exit 2
        fi
        exit 0
        ;;
esac

if [[ "${phase}" == "product-phase-active" ]]; then
    emit_block "Durante product-phase no uses ${TOOL_NAME}. Redacta y persiste analisis, vision, backlog, HUs y auditoria directamente con Write/Edit en esta misma sesion."
    echo "Secuencia valida durante product-phase:" >&2
    echo "  Read/Glob puntuales -> Write/Edit de docs/ y runtime" >&2
    echo "  Sin Agent, sin Task y sin volver a la inbox" >&2
    exit 2
fi

if [[ "${phase}" == "product-ready" ]]; then
    if [[ "${gate_status}" == "plan-publish" && "${branch_skill}" == "pspo-agent:onboarding" ]]; then
        if [[ "${provider_needs_choice}" == "1" || -z "${publish_provider}" ]]; then
            emit_block "Durante onboarding desde autopilot primero resuelve el proveedor remoto. No uses ${TOOL_NAME} todavia: la ruta valida es trello-fallback/notion-fallback/github-fallback env-status y .pspo-agent/runtime/publish-provider.py."
            exit 2
        fi
        if [[ "${publish_provider}" == "notion" ]]; then
            emit_block "Durante onboarding Notion desde autopilot no uses ${TOOL_NAME}. La ruta valida es notion-fallback.sh verify-credentials -> retrieve-page -> create-project -> save-project-targets."
            exit 2
        fi
        if [[ "${publish_provider}" == "github" ]]; then
            emit_block "Durante onboarding GitHub Projects desde autopilot no uses ${TOOL_NAME}. La ruta valida es github-fallback.sh verify-credentials -> create-project -> save-project-targets."
            exit 2
        fi
        if [[ "${publish_provider}" == "local" ]]; then
            emit_block "Con proveedor local no uses ${TOOL_NAME} durante onboarding. No hay onboarding remoto: continua con team/assign/dependencies/sprint-plan/publish local."
            exit 2
        fi
        if [[ "${payload_lower}" == *"publisher"* && "${payload_lower}" == *"list-boards"* ]]; then
            emit_block "En onboarding desde autopilot no listes tableros ni pidas eleccion al usuario. Usa el agente publisher para create-board con '{nombre_proyecto} - Backlog', luego manage-lists, manage-labels y guardado de TRELLO_BOARD_ID."
            exit 2
        fi
        if [[ "${payload_lower}" == *"publisher"* ]]; then
            exit 0
        fi
        emit_block "Durante onboarding Trello desde autopilot no uses ${TOOL_NAME} genericos ni exploradores. La unica delegacion valida es el agente publisher para verify-credentials, create-board y configuracion del tablero."
        exit 2
    fi
    exit 0
fi

emit_block "En /pspo-agent:autopilot no se permite lanzar ${TOOL_NAME} directamente. Encadena primero Skill(\"pspo-agent:product-phase\"); esa skill es la unica que puede delegar la fase de producto."
echo "Secuencia valida:" >&2
echo "  pspo-agent:product-phase" >&2
echo "  -> gate final -> validate o assign/dependencies/sprint-plan/publish" >&2
exit 2

exit 0
