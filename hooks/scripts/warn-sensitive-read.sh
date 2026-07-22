#!/usr/bin/env bash
# Hook PreToolUse (matcher: Read): bloquea lecturas crudas de `.env` y avisa
# sobre otros ficheros sensibles.

set -euo pipefail

# Resolver interprete de Python sin depender de 'python3' (en Windows suele ser
# 'python'). Sin interprete no se puede extraer la ruta objetivo: fail-open
# avisado, porque bloquear Read de forma global romperia la sesion.
PY="$(command -v python3 || command -v python || true)"
if [ -z "${PY}" ]; then
    echo "[pspo-agent] Aviso: no se encontro python3 ni python; se omite el aviso de lecturas sensibles (fail-open)." >&2
    exit 0
fi

INPUT=$(cat)

TARGETS=$(echo "$INPUT" | "$PY" -c "
import json, sys
try:
    data = json.load(sys.stdin)
    tool_input = data.get('tool_input', {})
    values = []
    for key in ('file_path', 'path', 'notebook_path'):
        value = tool_input.get(key)
        if isinstance(value, str):
            values.append(value)
    for key in ('paths',):
        value = tool_input.get(key)
        if isinstance(value, list):
            values.extend(str(v) for v in value)
    print('\n'.join(values))
except Exception:
    pass
" 2>/dev/null || true)

if echo "$TARGETS" | grep -Eqi '(^|/)\.env($|[.])|credentials|secret|token'; then
    if echo "$TARGETS" | grep -Eqi '(^|/)\.env($|[.])'; then
        echo "BLOCKED" >&2
        echo "No leas .env en crudo: expone secretos en el historial. Usa Bash con los helpers oficiales: .pspo-agent/runtime/trello-fallback.sh env-status --pretty, .pspo-agent/runtime/notion-fallback.sh env-status --pretty, .pspo-agent/runtime/github-fallback.sh env-status --pretty o .pspo-agent/runtime/publish-provider.py ." >&2
        echo "No leas .env en crudo: expone secretos en el historial. Usa Bash con los helpers oficiales: .pspo-agent/runtime/trello-fallback.sh env-status --pretty, .pspo-agent/runtime/notion-fallback.sh env-status --pretty, .pspo-agent/runtime/github-fallback.sh env-status --pretty o .pspo-agent/runtime/publish-provider.py ."
        exit 2
    fi
    echo "[pspo-agent] Aviso: lectura de fichero sensible detectada." >&2
    echo "[pspo-agent] No muestres ni copies valores de API keys, tokens o credenciales en la conversacion." >&2
fi

exit 0
