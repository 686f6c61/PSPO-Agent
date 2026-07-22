#!/usr/bin/env bash
# Hook PreToolUse (matcher: mcp__trello-client__.*): evita que autopilot
# toque Trello antes de terminar la fase de producto.

set -euo pipefail

emit_block() {
    local message="$1"
    echo "BLOCKED" >&2
    echo "$message" >&2
    echo "$message"
}

# Resolver interprete de Python sin depender de 'python3' (en Windows suele ser
# 'python'). Sin interprete no se puede computar el estado: fail-open avisado.
PY="$(command -v python3 || command -v python || true)"
if [ -z "${PY}" ]; then
    echo "[pspo-agent] Aviso: no se encontro python3 ni python; se omite el guardarrail de Trello (fail-open)." >&2
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
print(f'CWD={shlex.quote(cwd)}')
print(f'TOOL_NAME={shlex.quote(tool_name)}')
")"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
phase="$("$PY" "${SCRIPT_DIR}/autopilot-guard.py" --ensure-scaffold --field phase "${CWD}")"

case "${phase}" in
    inactive|product-ready)
        exit 0
        ;;
esac

emit_block "En /pspo-agent:autopilot Trello va despues de la fase de producto. Termina primero con Skill(\"pspo-agent:product-phase\") y deja backlog + HU individuales antes de onboarding o publish."
echo "Tool bloqueada: ${TOOL_NAME}" >&2
exit 2
