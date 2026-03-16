#!/usr/bin/env bash
# Hook PreToolUse (matcher: Skill): fuerza el carril de orquestacion de
# /pspo-agent:autopilot despues de la gate final y evita reentradas a
# product-phase una vez que la fase de producto ya termino.

set -euo pipefail

emit_block() {
    local message="$1"
    echo "BLOCKED" >&2
    echo "$message" >&2
    echo "$message"
}

INPUT=$(cat)

eval "$(printf '%s' "$INPUT" | python3 -c "
import json, os, shlex, sys
try:
    data = json.load(sys.stdin)
except Exception:
    data = {}
cwd = data.get('cwd') or os.getcwd()
tool_input = data.get('tool_input', {}) or {}
skill = tool_input.get('skill') or tool_input.get('name') or ''
print(f'CWD={shlex.quote(cwd)}')
print(f'SKILL_NAME={shlex.quote(skill)}')
")"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
phase="$(python3 "${SCRIPT_DIR}/autopilot-guard.py" --ensure-scaffold --field phase "${CWD}")"
gate_status="$(python3 "${SCRIPT_DIR}/autopilot-guard.py" --field gate_status "${CWD}")"
branch_skill_file="$(python3 "${SCRIPT_DIR}/autopilot-guard.py" --field branch_skill_file "${CWD}")"

set_branch_skill() {
    mkdir -p "$(dirname "${branch_skill_file}")"
    printf '%s\n' "$1" > "${branch_skill_file}"
}

clear_branch_skill() {
    rm -f "${branch_skill_file}"
}

if [[ "${phase}" == "product-ready" ]] && [[ "${SKILL_NAME}" == "pspo-agent:autopilot" ]]; then
    clear_branch_skill
    exit 0
fi

case "${phase}" in
    inactive)
        exit 0
        ;;
    prepare-context)
        emit_block "En /pspo-agent:autopilot no lances skills todavia. Primero usa Glob(\".pspo-agent/inbox/*\") para preparar el contexto runtime."
        exit 2
        ;;
    delegate-product-phase)
        if [[ "${SKILL_NAME}" == "pspo-agent:product-phase" ]]; then
            exit 0
        fi
        emit_block "Ya existe .pspo-agent/runtime/autopilot-context.md. La siguiente skill valida es Skill(\"pspo-agent:product-phase\")."
        exit 2
        ;;
    product-phase-active)
        emit_block "La fase de producto sigue activa. No abras otra skill hasta que product-phase deje los artefactos de docs/ y marque su estado en runtime."
        exit 2
        ;;
    product-ready)
        ;;
esac

case "${gate_status}" in
    ""|pending)
        emit_block "Autopilot ya termino la fase de producto. Antes de abrir otra skill debes resolver la gate final con AskUserQuestion y elegir 'Revisar historias' o 'Planificar y publicar'."
        exit 2
        ;;
    review)
        case "${SKILL_NAME}" in
            pspo-agent:validate|pspo-agent:team|pspo-agent:onboarding|pspo-agent:assign|pspo-agent:dependencies|pspo-agent:sprint-plan|pspo-agent:publish)
                set_branch_skill "${SKILL_NAME}"
                exit 0
                ;;
        esac
        emit_block "La rama elegida es 'Revisar historias'. No vuelvas a product-phase ni abras skills laterales. La continuacion valida empieza en Skill(\"pspo-agent:validate\")."
        exit 2
        ;;
    plan-publish)
        case "${SKILL_NAME}" in
            pspo-agent:onboarding|pspo-agent:team|pspo-agent:assign|pspo-agent:dependencies|pspo-agent:sprint-plan|pspo-agent:publish)
                set_branch_skill "${SKILL_NAME}"
                exit 0
                ;;
        esac
        emit_block "La rama elegida es 'Planificar y publicar'. No vuelvas a product-phase ni abras validate. La continuacion valida es onboarding/team si faltan prerequisitos y luego assign -> dependencies -> sprint-plan -> publish."
        exit 2
        ;;
    done)
        clear_branch_skill
        exit 0
        ;;
esac

exit 0
